import hashlib
from db.database import get_setting, set_setting

SALT = "DupeClearPro2024XK9"
PRO_PREFIX = "DCP-"
VALID_PREFIXES = {"a9", "f3", "7b", "2c", "e5"}


def validate_license(key: str) -> bool:
    if not key or not key.upper().startswith(PRO_PREFIX):
        return False
    digest = hashlib.sha256((SALT + key.upper()).encode()).hexdigest()
    return digest[:2] in VALID_PREFIXES


def is_pro() -> bool:
    key = get_setting("license_key", "")
    return validate_license(key)


def activate_license(key: str) -> bool:
    if validate_license(key):
        set_setting("license_key", key.upper())
        set_setting("license_status", "pro")
        return True
    return False


def deactivate_license():
    set_setting("license_key", "")
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
