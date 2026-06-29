"""Offline license key generator for DupeClear Pro.
Keep this script and the private secret PRIVATE — never ship either.

Usage:
    python keygen.py          # generate 10 keys
    python keygen.py 50       # generate 50 keys
    python keygen.py --verify DCP-XXXX-XXXX-XXXX-XXXX-XXXX  # verify a key
    python keygen.py --new-secret    # print fresh _SA/_SB arrays to replace
                                     # the ones in core/license.py
"""
import os
import sys
import hmac
import hashlib

# -------------------------------------------------------------------------
# These MUST match _SA and _SB in core/license.py exactly.
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
_DOMAIN = b"DupeClearPro-v1-LICENSE"
PRO_PREFIX = "DCP-"


def _secret() -> bytes:
    return bytes(a ^ b for a, b in zip(_SA, _SB))


def _compute_mac(serial: bytes) -> bytes:
    return hmac.new(_secret(), _DOMAIN + serial, hashlib.sha256).digest()


def generate_key() -> str:
    serial = os.urandom(8)
    mac    = _compute_mac(serial)[:8]
    data   = (serial + mac).hex().upper()
    groups = [data[i:i+8] for i in range(0, 32, 8)]
    return PRO_PREFIX + "-".join(groups)


def verify_key(key: str) -> bool:
    k = key.upper().strip()
    if not k.startswith(PRO_PREFIX):
        return False
    raw = k[len(PRO_PREFIX):].replace("-", "")
    if len(raw) != 32:
        return False
    try:
        data = bytes.fromhex(raw)
    except ValueError:
        return False
    serial, claimed_mac = data[:8], data[8:]
    expected_mac = _compute_mac(serial)[:8]
    return hmac.compare_digest(claimed_mac, expected_mac)


def print_new_secret():
    """Generate a fresh secret pair to replace _SA/_SB."""
    import secrets as _s
    real = _s.token_bytes(32)
    mask = _s.token_bytes(32)
    sa   = bytes(r ^ m for r, m in zip(real, mask))
    print("Replace _SA and _SB in BOTH core/license.py and keygen.py:\n")
    print("_SA = bytes([")
    print("    " + ", ".join(f"0x{b:02X}" for b in sa[:16]) + ",")
    print("    " + ", ".join(f"0x{b:02X}" for b in sa[16:]) + ",")
    print("])")
    print("_SB = bytes([")
    print("    " + ", ".join(f"0x{b:02X}" for b in mask[:16]) + ",")
    print("    " + ", ".join(f"0x{b:02X}" for b in mask[16:]) + ",")
    print("])")


if __name__ == "__main__":
    args = sys.argv[1:]

    if args and args[0] == "--new-secret":
        print_new_secret()
        sys.exit(0)

    if args and args[0] == "--verify":
        key = args[1] if len(args) > 1 else input("Key: ").strip()
        ok  = verify_key(key)
        print(f"  {key}  =>  {'VALID ✅' if ok else 'INVALID ❌'}")
        sys.exit(0 if ok else 1)

    count = int(args[0]) if args else 10
    print(f"Generating {count} DupeClear Pro license keys...\n")
    for i in range(count):
        print(f"  {i+1:3d}.  {generate_key()}")
    print("\nFormat: DCP-SSSSSSSS-SSSSSSSS-MMMMMMMM-MMMMMMMM")
    print("        S = 8-byte random serial   M = 8-byte HMAC-SHA256 tag")
    print(f"        Brute-force probability: 1 / 2^64  (~1 in 18 quintillion)")
