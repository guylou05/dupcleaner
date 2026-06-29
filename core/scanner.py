import os
import threading
from datetime import datetime
from collections import defaultdict
from dataclasses import dataclass

from core.hasher import partial_hash, full_hash
from core.image_similarity import is_image, group_similar_images
from db.models import FileInfo, DuplicateGroup, ScanOptions
from utils.constants import IMAGE_EXTENSIONS, SCAN_BATCH_SIZE, SCAN_FREE_LIMIT_GB
from utils.file_utils import walk_files

try:
    from PIL import Image
    import io
    _PIL_AVAILABLE = True
except ImportError:
    _PIL_AVAILABLE = False


def _make_thumbnail(path: str, size: int = 72) -> bytes | None:
    if not _PIL_AVAILABLE:
        return None
    ext = os.path.splitext(path)[1].lower()
    if ext not in IMAGE_EXTENSIONS:
        return None
    try:
        img = Image.open(path)
        img.thumbnail((size, size))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()
    except Exception:
        return None


def _auto_select(groups: list, rule: str = "newest") -> list:
    for group in groups:
        files = group.files
        if rule == "newest":
            keep = max(files, key=lambda f: f.modified_at)
        elif rule == "shortest_path":
            keep = min(files, key=lambda f: len(f.path))
        elif rule == "primary_drive":
            c_files = [f for f in files if f.path.lower().startswith("c:\\")]
            keep = c_files[0] if c_files else files[0]
        else:
            keep = max(files, key=lambda f: f.modified_at)

        for f in files:
            f.is_recommended_keep = (f is keep)
            f.marked_for_delete = (f is not keep)
    return groups


class DuplicateScanner:
    def __init__(self, options: ScanOptions):
        self.options = options
        self._cancel_event = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self, progress_callback, complete_callback, error_callback=None):
        self._cancel_event.clear()
        self._thread = threading.Thread(
            target=self._run,
            args=(progress_callback, complete_callback, error_callback),
            daemon=True
        )
        self._thread.start()

    def cancel(self):
        self._cancel_event.set()

    def _run(self, progress_cb, complete_cb, error_cb):
        try:
            opts = self.options
            extensions = None
            if opts.file_type_filter:
                extensions = set(opts.file_type_filter)

            exclude = list(opts.exclude_folders or [])

            # Step 1 — collect all files
            all_files = walk_files(
                opts.folders,
                include_hidden=opts.include_hidden,
                min_size_bytes=opts.min_file_size_kb * 1024,
                max_size_bytes=opts.max_file_size_mb * 1024 * 1024 if opts.max_file_size_mb else 0,
                extensions=extensions,
                exclude_folders=exclude,
            )

            # Free tier: cap total data scanned at SCAN_FREE_LIMIT_GB.
            # Skip (don't stop on) oversized files so one large file early in
            # the walk order can't knock out every file that follows it.
            cap_hit = False
            from core.license import is_pro as _is_pro
            if not _is_pro():
                limit = SCAN_FREE_LIMIT_GB * 1024 ** 3
                cumulative, capped = 0, []
                for _path, _size in all_files:
                    if cumulative + _size > limit:
                        cap_hit = True
                        continue
                    cumulative += _size
                    capped.append((_path, _size))
                all_files = capped

            total = len(all_files)
            errors = []
            groups = []
            scanned = 0

            # Step 2 — group by size
            by_size = defaultdict(list)
            for path, size in all_files:
                by_size[size].append(path)

            # Step 3 — partial hash for size groups > 1
            candidates = [paths for paths in by_size.values() if len(paths) > 1]
            flat_candidates = [p for paths in candidates for p in paths]

            by_partial = defaultdict(list)
            for path in flat_candidates:
                if self._cancel_event.is_set():
                    complete_cb([], scanned, errors, cancelled=True, cap_hit=False)
                    return
                ph = partial_hash(path)
                if ph is None:
                    errors.append(path)
                else:
                    by_partial[(os.path.getsize(path), ph)].append(path)
                scanned += 1
                if scanned % SCAN_BATCH_SIZE == 0:
                    progress_cb(scanned, total, len(groups), path)

            # Step 4 — full hash for partial-hash groups > 1
            by_full = defaultdict(list)
            for (size, _), paths in by_partial.items():
                if len(paths) < 2:
                    continue
                for path in paths:
                    if self._cancel_event.is_set():
                        complete_cb([], scanned, errors, cancelled=True, cap_hit=False)
                        return
                    fh = full_hash(path)
                    if fh is None:
                        errors.append(path)
                    else:
                        by_full[(size, fh)].append(path)
                    scanned += 1
                    if scanned % SCAN_BATCH_SIZE == 0:
                        progress_cb(scanned, total, len(groups), path)

            # Step 5 — build DuplicateGroup objects
            for (size, fh), paths in by_full.items():
                if len(paths) < 2:
                    continue
                file_infos = []
                for p in paths:
                    try:
                        stat = os.stat(p)
                        fi = FileInfo(
                            path=p,
                            name=os.path.basename(p),
                            size_bytes=stat.st_size,
                            modified_at=datetime.fromtimestamp(stat.st_mtime),
                            extension=os.path.splitext(p)[1].lower(),
                            thumbnail=_make_thumbnail(p),
                        )
                        file_infos.append(fi)
                    except OSError:
                        errors.append(p)

                if len(file_infos) >= 2:
                    grp = DuplicateGroup(
                        hash_value=fh,
                        files=file_infos,
                        total_size_bytes=size * len(file_infos),
                        wasted_bytes=size * (len(file_infos) - 1),
                        group_type="exact",
                        similarity_score=1.0,
                    )
                    groups.append(grp)

            # Step 6 — near-duplicate images (Pro)
            if opts.enable_image_similarity and not self._cancel_event.is_set():
                all_image_paths = [
                    p for p, _ in all_files
                    if os.path.splitext(p)[1].lower() in IMAGE_EXTENSIONS
                ]
                pairs = group_similar_images(all_image_paths, opts.similarity_threshold)
                for path_a, path_b, sim in pairs:
                    if self._cancel_event.is_set():
                        break
                    try:
                        sa, sb = os.path.getsize(path_a), os.path.getsize(path_b)
                        fi_a = FileInfo(
                            path=path_a, name=os.path.basename(path_a),
                            size_bytes=sa,
                            modified_at=datetime.fromtimestamp(os.stat(path_a).st_mtime),
                            extension=os.path.splitext(path_a)[1].lower(),
                            thumbnail=_make_thumbnail(path_a),
                        )
                        fi_b = FileInfo(
                            path=path_b, name=os.path.basename(path_b),
                            size_bytes=sb,
                            modified_at=datetime.fromtimestamp(os.stat(path_b).st_mtime),
                            extension=os.path.splitext(path_b)[1].lower(),
                            thumbnail=_make_thumbnail(path_b),
                        )
                        grp = DuplicateGroup(
                            hash_value=f"sim_{path_a}_{path_b}",
                            files=[fi_a, fi_b],
                            total_size_bytes=sa + sb,
                            wasted_bytes=min(sa, sb),
                            group_type="similar_image",
                            similarity_score=sim,
                        )
                        groups.append(grp)
                    except OSError:
                        pass

            # Sort: largest wasted bytes first
            groups.sort(key=lambda g: g.wasted_bytes, reverse=True)

            from db.database import get_setting
            rule = get_setting("auto_select_rule", "newest")
            groups = _auto_select(groups, rule)

            complete_cb(groups, scanned, errors, cancelled=False, cap_hit=cap_hit)

        except Exception as exc:
            if error_cb:
                error_cb(exc)
            else:
                complete_cb([], 0, [], cancelled=False, cap_hit=False)
