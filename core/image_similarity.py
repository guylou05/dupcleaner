from utils.constants import IMAGE_EXTENSIONS

try:
    import imagehash
    from PIL import Image
    _AVAILABLE = True
except ImportError:
    _AVAILABLE = False


def is_image(path: str) -> bool:
    import os
    return os.path.splitext(path)[1].lower() in IMAGE_EXTENSIONS


def perceptual_hash(path: str) -> str | None:
    if not _AVAILABLE:
        return None
    try:
        img = Image.open(path)
        return str(imagehash.dhash(img))
    except Exception:
        return None


def hash_distance(h1: str, h2: str) -> int:
    if not _AVAILABLE or h1 is None or h2 is None:
        return 999
    try:
        return imagehash.hex_to_hash(h1) - imagehash.hex_to_hash(h2)
    except Exception:
        return 999


def similarity_pct(h1: str, h2: str, max_distance: int = 64) -> float:
    dist = hash_distance(h1, h2)
    return max(0.0, 1.0 - dist / max_distance)


def group_similar_images(image_paths: list, threshold_pct: int = 90) -> list:
    """Return list of (path_a, path_b, similarity) tuples above threshold."""
    if not _AVAILABLE or not image_paths:
        return []
    threshold = threshold_pct / 100.0
    hashes = {}
    for p in image_paths:
        h = perceptual_hash(p)
        if h is not None:
            hashes[p] = h

    pairs = []
    paths = list(hashes.keys())
    for i in range(len(paths)):
        for j in range(i + 1, len(paths)):
            sim = similarity_pct(hashes[paths[i]], hashes[paths[j]])
            if sim >= threshold:
                pairs.append((paths[i], paths[j], sim))
    return pairs
