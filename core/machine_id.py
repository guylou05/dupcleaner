import hashlib


def get_machine_id() -> str:
    """Return a stable per-machine fingerprint (SHA-256 of Windows MachineGuid)."""
    raw = _read_machine_guid() or _mac_fallback()
    return hashlib.sha256(raw.encode()).hexdigest()


def _read_machine_guid() -> str | None:
    try:
        import winreg
        key = winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE,
            r"SOFTWARE\Microsoft\Cryptography",
        )
        guid, _ = winreg.QueryValueEx(key, "MachineGuid")
        winreg.CloseKey(key)
        return guid
    except Exception:
        return None


def _mac_fallback() -> str:
    import uuid
    return str(uuid.getnode())
