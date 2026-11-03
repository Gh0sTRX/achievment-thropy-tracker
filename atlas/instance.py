"""Keep the per-user Windows install closed while Inno Setup replaces binaries."""
import sys


def acquire():
    if sys.platform!='win32':return None
    import ctypes
    from ctypes import wintypes
    kernel=ctypes.WinDLL('kernel32',use_last_error=True)
    kernel.CreateMutexW.argtypes=[ctypes.c_void_p,wintypes.BOOL,wintypes.LPCWSTR]
    kernel.CreateMutexW.restype=wintypes.HANDLE
    handle=kernel.CreateMutexW(None,False,'Local\\AchievementAtlas.Running')
    if not handle:raise OSError('Uygulama kilidi oluşturulamadı.')
    if ctypes.get_last_error()==183:
        kernel.CloseHandle.argtypes=[wintypes.HANDLE];kernel.CloseHandle(handle)
        ctypes.windll.user32.MessageBoxW(None,'Achievement Atlas zaten açık. Önce mevcut pencereyi kullan veya kapat.','Achievement Atlas',64)
        return False
    return handle


def release(handle):
    if handle is None or handle is False:return
    import ctypes
    from ctypes import wintypes
    kernel=ctypes.WinDLL('kernel32',use_last_error=True)
    kernel.CloseHandle.argtypes=[wintypes.HANDLE]
    kernel.CloseHandle(handle)
