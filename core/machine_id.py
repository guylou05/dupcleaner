import hashlib
import uuid


def get_machine_id() -> str:
    """Return a stable per-machine fingerprint (SHA-256 of Windows MachineGuid)."""
    raw = _read_machine_guid() or _persisted_fallback()
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


def _persisted_fallback() -> str:
    """
    Fallback for machines where the Windows MachineGuid isn't readable
    (non-Windows, sandboxed, or permission-denied). uuid.getnode() isn't
    safe to use directly here: when no real hardware MAC is available it
    returns a random value on every process start, which would silently
    un-bind a previously activated license on next launch. Persist a
    random UUID in the DB on first use so it stays stable across runs.
    """
    from db.database import get_setting, set_setting
    existing = get_setting("machine_id_fallback", "")
    if existing:
        return existing
    new_id = str(uuid.uuid4())
    set_setting("machine_id_fallback", new_id)
    return new_id
