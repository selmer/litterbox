import threading

_active_poller = None
_active_lock = threading.Lock()


def set_active_poller(poller) -> None:
    global _active_poller
    with _active_lock:
        _active_poller = poller


def get_active_poller():
    with _active_lock:
        return _active_poller


def reload_active_poller() -> tuple[bool, str | None]:
    poller = get_active_poller()
    if poller is None:
        return False, "No active poller is available to reload."
    try:
        ok = poller.reload_cloud()
    except Exception as exc:
        return False, str(exc)
    if not ok:
        return False, "Tuya Cloud connection could not be initialized."
    return True, None
