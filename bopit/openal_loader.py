"""Load the vendored OpenAL Soft before cyal loads its own bundled copy.

cyal links against OpenAL32.dll (libopenal.so.1 on Linux). Once a library with that name
is loaded, the system reuses it, so preloading ours by full path makes cyal use it too.
Must run before the first import of cyal.
"""

import ctypes
import logging
import sys

from bopit.config import VENDOR_DIR

log = logging.getLogger(__name__)

_LIBRARY_NAMES = {"win32": "OpenAL32.dll", "linux": "libopenal.so.1"}
_loaded: ctypes.CDLL | None = None


def preload_openal() -> None:
    global _loaded
    if _loaded is not None:
        return
    if "cyal" in sys.modules:
        log.error("cyal was imported before the vendored OpenAL was loaded; using cyal's copy")
        return
    name = _LIBRARY_NAMES.get(sys.platform)
    if name is None:
        log.warning("No vendored OpenAL for platform %s, using the system one", sys.platform)
        return
    path = VENDOR_DIR / "openal" / name
    try:
        mode = getattr(ctypes, "RTLD_GLOBAL", 0)
        _loaded = ctypes.CDLL(str(path), mode=mode)
    except OSError:
        log.exception("Could not load vendored OpenAL from %s, falling back to cyal's copy", path)
        return
    log.info("Loaded OpenAL from %s", path)


def loaded_openal_path() -> str | None:
    """Full path of the OpenAL library actually in use, on Windows."""
    if sys.platform != "win32":
        return None
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.GetModuleHandleW.restype = ctypes.c_void_p
    kernel32.GetModuleFileNameW.argtypes = [ctypes.c_void_p, ctypes.c_wchar_p, ctypes.c_uint32]
    handle = kernel32.GetModuleHandleW("OpenAL32.dll")
    if not handle:
        return None
    buffer = ctypes.create_unicode_buffer(1024)
    kernel32.GetModuleFileNameW(handle, buffer, len(buffer))
    return buffer.value
