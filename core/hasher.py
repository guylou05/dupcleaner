import hashlib
import os
from utils.constants import PARTIAL_HASH_BYTES

try:
    import xxhash
    _USE_XXHASH = True
except ImportError:
    _USE_XXHASH = False


def _hasher():
    return xxhash.xxh64() if _USE_XXHASH else hashlib.md5()


def partial_hash(path: str) -> str | None:
    try:
        h = _hasher()
        with open(path, "rb") as f:
            h.update(f.read(PARTIAL_HASH_BYTES))
        return h.hexdigest()
    except OSError:
        return None


def full_hash(path: str) -> str | None:
    try:
        h = _hasher()
        with open(path, "rb") as f:
            while chunk := f.read(1024 * 1024):
                h.update(chunk)
        return h.hexdigest()
    except OSError:
        return None


def md5_hash(path: str) -> str | None:
    try:
        h = hashlib.md5()
        with open(path, "rb") as f:
            while chunk := f.read(1024 * 1024):
                h.update(chunk)
        return h.hexdigest()
    except OSError:
        return None
