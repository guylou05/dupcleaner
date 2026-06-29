"""Offline key generator for DupeClear Pro.
Run this script to generate valid license keys.
Do NOT distribute this script.
"""
import hashlib
import random
import string
import sys

SALT = "DupeClearPro2024XK9"
PRO_PREFIX = "DCP-"
VALID_PREFIXES = {"a9", "f3", "7b", "2c", "e5"}


def _random_segment(length: int = 4) -> str:
    chars = string.ascii_uppercase + string.digits
    return "".join(random.choices(chars, k=length))


def generate_key() -> str:
    while True:
        segments = "-".join(_random_segment() for _ in range(4))
        key = f"{PRO_PREFIX}{segments}"
        digest = hashlib.sha256((SALT + key).encode()).hexdigest()
        if digest[:2] in VALID_PREFIXES:
            return key


def verify_key(key: str) -> bool:
    if not key.upper().startswith(PRO_PREFIX):
        return False
    digest = hashlib.sha256((SALT + key.upper()).encode()).hexdigest()
    return digest[:2] in VALID_PREFIXES


if __name__ == "__main__":
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    print(f"Generating {count} valid DupeClear Pro license keys...\n")
    for i in range(count):
        key = generate_key()
        print(f"  {i+1:2d}.  {key}")
    print("\nVerification check:")
    test = generate_key()
    print(f"  {test}  ->  valid={verify_key(test)}")
