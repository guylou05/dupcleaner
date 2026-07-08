import os
from pathlib import Path


def format_size(size_bytes: int) -> str:
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 ** 2:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 ** 3:
        return f"{size_bytes / 1024**2:.1f} MB"
    else:
        return f"{size_bytes / 1024**3:.2f} GB"


def format_size_mb(size_bytes: int) -> str:
    return f"{size_bytes / 1024**2:.1f} MB"


def get_extension(path: str) -> str:
    return Path(path).suffix.lower()


def open_in_explorer(path: str):
    import subprocess
    try:
        subprocess.Popen(f'explorer /select,"{path}"')
    except Exception:
        try:
            os.startfile(os.path.dirname(path))
        except Exception:
            pass


def safe_path_display(path: str, max_len: int = 60) -> str:
    if len(path) <= max_len:
        return path
    parts = Path(path).parts
    if len(parts) <= 2:
        return path
    return str(Path(parts[0]) / "..." / Path(*parts[-2:]))


def walk_files(folders: list, include_hidden: bool = False,
               min_size_bytes: int = 1024,
               max_size_bytes: int = 0,
               extensions: set = None,
               exclude_folders: list = None) -> list:
    exclude_set = set()
    if exclude_folders:
        exclude_set = {os.path.normcase(os.path.normpath(f)) for f in exclude_folders}

    results = []
    for folder in folders:
        for dirpath, dirnames, filenames in os.walk(folder, topdown=True):
            norm_dir = os.path.normcase(os.path.normpath(dirpath))
            if norm_dir in exclude_set:
                dirnames.clear()
                continue
            # prune excluded sub-dirs in-place so os.walk skips them
            dirnames[:] = [
                d for d in dirnames
                if os.path.normcase(os.path.join(dirpath, d)) not in exclude_set
                and (include_hidden or not d.startswith("."))
            ]
            for fname in filenames:
                if not include_hidden and fname.startswith("."):
                    continue
                fpath = os.path.join(dirpath, fname)
                try:
                    size = os.path.getsize(fpath)
                except OSError:
                    continue
                if size < min_size_bytes:
                    continue
                if max_size_bytes and size > max_size_bytes:
                    continue
                ext = os.path.splitext(fname)[1].lower()
                if extensions and ext not in extensions:
                    continue
                results.append((fpath, size))
    return results
