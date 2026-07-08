import shutil
import os
from pathlib import Path
from db.database import add_trash_item, get_trash_items, delete_trash_item

TRASH_DIR = Path(os.getenv("APPDATA", Path.home())) / "DupeClearPro" / "RecoveryBin"


def _trash_dest(src: Path) -> Path:
    anchor_clean = src.anchor.replace(":\\", "").replace(":", "").replace("\\", "")
    relative = src.relative_to(src.anchor)
    return TRASH_DIR / anchor_clean / relative


def get_bin_size() -> int:
    total = 0
    if TRASH_DIR.exists():
        for dirpath, _, filenames in os.walk(TRASH_DIR):
            for f in filenames:
                try:
                    total += os.path.getsize(os.path.join(dirpath, f))
                except OSError:
                    pass
    return total


def safe_delete(file_path: str, scan_history_id: int = None) -> bool:
    TRASH_DIR.mkdir(parents=True, exist_ok=True)
    src = Path(file_path)
    if not src.exists():
        return False
    dest = _trash_dest(src)
    dest.parent.mkdir(parents=True, exist_ok=True)
    try:
        shutil.move(str(src), str(dest))
        add_trash_item(
            original_path=str(src),
            trash_path=str(dest),
            file_name=src.name,
            size_bytes=dest.stat().st_size,
            scan_history_id=scan_history_id,
        )
        return True
    except Exception:
        return False


def restore_file(trash_item_id: int) -> tuple:
    rows = get_trash_items()
    item = next((r for r in rows if r["id"] == trash_item_id), None)
    if not item:
        return False, "Item not found in database."

    src = Path(item["trash_path"])
    dest = Path(item["original_path"])

    if not src.exists():
        return False, "File no longer exists in recovery bin."

    dest.parent.mkdir(parents=True, exist_ok=True)
    try:
        shutil.move(str(src), str(dest))
        delete_trash_item(trash_item_id)
        return True, str(dest)
    except Exception as e:
        return False, str(e)


def permanently_delete(trash_item_id: int) -> bool:
    rows = get_trash_items()
    item = next((r for r in rows if r["id"] == trash_item_id), None)
    if not item:
        return False
    try:
        p = Path(item["trash_path"])
        if p.exists():
            p.unlink()
        delete_trash_item(trash_item_id)
        return True
    except Exception:
        return False


def empty_bin() -> tuple:
    """Delete everything in the bin. Returns (count, bytes_freed)."""
    rows = get_trash_items()
    count = 0
    freed = 0
    for row in rows:
        p = Path(row["trash_path"])
        try:
            size = row["size_bytes"]
            if p.exists():
                p.unlink()
            delete_trash_item(row["id"])
            count += 1
            freed += size
        except Exception:
            pass
    return count, freed
