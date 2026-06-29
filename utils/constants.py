APP_NAME        = "DupeClear Pro"
APP_VERSION     = "1.0.0"
APP_AUTHOR      = "DupeClear"

WINDOW_WIDTH    = 1200
WINDOW_HEIGHT   = 760
MIN_WIDTH       = 900
MIN_HEIGHT      = 600
SIDEBAR_WIDTH   = 220
TITLEBAR_HEIGHT = 36
CORNER_RADIUS   = 8

THUMB_SIZE      = 72
CARD_ROW_HEIGHT = 120

SCAN_BATCH_SIZE = 100   # files per progress update tick

PARTIAL_HASH_BYTES = 65536  # 64 KB for fast pre-filter

IMAGE_EXTENSIONS = {
    ".jpg", ".jpeg", ".png", ".gif", ".bmp",
    ".tiff", ".tif", ".webp", ".heic", ".raw",
}

DEFAULT_EXCLUDE_FOLDERS = [
    "C:\\Windows",
    "C:\\Program Files",
    "C:\\Program Files (x86)",
]

SCAN_FREE_LIMIT_GB = 10  # free tier scan cap
