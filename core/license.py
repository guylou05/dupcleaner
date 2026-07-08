import hmac
import hashlib
import os
from db.database import get_setting, set_setting

# -------------------------------------------------------------------------
# Secret stored as two separate byte arrays XOR'd together at runtime.
# Neither array alone reveals the secret; a string search won't find it.
# Replace both arrays with freshly generated values before shipping.
# Generate new ones with: python -c "import secrets; a=secrets.token_bytes(32);
#   b=secrets.token_bytes(32); print(list(a)); print(list(b ^ c for b,c in zip(b,a)))"
# -------------------------------------------------------------------------
_SA = bytes([
    0x4A, 0x9C, 0x2F, 0x71, 0xB3, 0x8E, 0x5D, 0x16,
    0xC7, 0x3A, 0x94, 0xE2, 0x58, 0x0B, 0xF4, 0x27,
    0x6E, 0xA1, 0x3C, 0x87, 0xD9, 0x52, 0x1F, 0x6B,
    0xC4, 0x38, 0x7A, 0xE5, 0x2D, 0x90, 0x4F, 0xB8,
])
_SB = bytes([
    0x31, 0xF7, 0xA2, 0x4E, 0x6C, 0x19, 0x8B, 0xD5,
    0x42, 0xBE, 0x17, 0x7C, 0xA3, 0xE6, 0x5F, 0x08,
    0x93, 0x2A, 0xC1, 0x5E, 0xB4, 0x7F, 0x08, 0xD2,
    0x49, 0xAC, 0x63, 0x18, 0xF2, 0x37, 0xE1, 0x5C,
])

# Domain separator — changes the MAC even if the raw secret leaks.
_DOMAIN = b"DupeClearPro-v1-LICENSE"

PRO_PREFIX = "DCP-"
_KEY_DATA_HEX_LEN = 32  # 8 bytes serial + 8 bytes MAC = 16 bytes = 32 hex chars


def _secret() -> bytes:
    """Reconstruct the 256-bit HMAC key at runtime from two disjoint arrays."""
    return bytes(a ^ b for a, b in zip(_SA, _SB))


def _compute_mac(serial: bytes) -> bytes:
    """HMAC-SHA256(secret, DOMAIN || serial) — full 32-byte digest."""
    return hmac.new(_secret(), _DOMAIN + serial, hashlib.sha256).digest()


def _parse_key(key: str):
    """Return (serial: bytes, claimed_mac: bytes) or raise ValueError."""
    k = key.upper().strip()
    if not k.startswith(PRO_PREFIX):
        raise ValueError("bad prefix")
    raw = k[len(PRO_PREFIX):].replace("-", "")
    if len(raw) != _KEY_DATA_HEX_LEN:
        raise ValueError("bad length")
    data = bytes.fromhex(raw)   # raises ValueError on non-hex
    return data[:8], data[8:]   # serial, mac


def validate_license(key: str) -> bool:
    """
    License format: DCP-XXXXXXXX-XXXXXXXX-XXXXXXXX-XXXXXXXX
                       |--serial--|  |----8-byte MAC---------|

    Security properties:
    - 64-bit MAC verification  =>  P(random key valid) = 1/2^64
    - hmac.compare_digest      =>  timing-safe, no oracle
    - secret never in plaintext =>  string search won't find it
    """
    try:
        serial, claimed_mac = _parse_key(key)
    except (ValueError, Exception):
        return False
    expected_mac = _compute_mac(serial)[:8]
    return hmac.compare_digest(claimed_mac, expected_mac)


def is_pro() -> bool:
    from core.machine_id import get_machine_id
    key = get_setting("license_key", "")
    if not validate_license(key):
        return False
    stored_mid = get_setting("license_machine_id", "")
    # If no machine ID was stored yet (pre-binding upgrade), bind now
    if not stored_mid:
        set_setting("license_machine_id", get_machine_id())
        return True
    return hmac.compare_digest(stored_mid, get_machine_id())


def activate_license(key: str) -> bool:
    from core.machine_id import get_machine_id
    if validate_license(key):
        set_setting("license_key", key.upper().strip())
        set_setting("license_machine_id", get_machine_id())
        set_setting("license_status", "pro")
        return True
    return False


def deactivate_license():
    set_setting("license_key", "")
    set_setting("license_machine_id", "")
    set_setting("license_status", "free")


def requires_pro(fallback_message="This feature requires DupeClear Pro"):
    def decorator(func):
        def wrapper(self, *args, **kwargs):
            if not is_pro():
                if hasattr(self, "show_pro_prompt"):
                    self.show_pro_prompt(fallback_message)
                return
            return func(self, *args, **kwargs)
        return wrapper
    return decorator
