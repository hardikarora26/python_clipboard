"""
This module implements clipboard handling on Windows using ctypes.
"""
import time
import contextlib
import ctypes
from ctypes import c_size_t, sizeof, c_wchar_p, get_errno, c_wchar, c_char_p, c_char

def init_osx_clipboard():
    import richxerox

    def copy_osx(text=None, clear_first=True, **kwargs):
        richxerox.copy(text, clear_first, **kwargs)

    def paste_osx(format='text'):       
        return richxerox.paste(format)

    return copy_osx, paste_osx
    
class CheckedCall(object):
    def __init__(self, f):
        super(CheckedCall, self).__setattr__("f", f)

    def __call__(self, *args):
        ret = self.f(*args)
        if not ret and get_errno():
            raise Exception("Error calling " + self.f.__name__)
        return ret

    def __setattr__(self, key, value):
        setattr(self.f, key, value)


def init_windows_clipboard():
    from ctypes.wintypes import (HGLOBAL, LPVOID, DWORD, LPCSTR, INT, HWND,
                                 HINSTANCE, HMENU, BOOL, UINT, HANDLE)

    windll = ctypes.windll

    safeCreateWindowExA = CheckedCall(windll.user32.CreateWindowExA)
    safeCreateWindowExA.argtypes = [DWORD, LPCSTR, LPCSTR, DWORD, INT, INT,
                                    INT, INT, HWND, HMENU, HINSTANCE, LPVOID]
    safeCreateWindowExA.restype = HWND

    safeDestroyWindow = CheckedCall(windll.user32.DestroyWindow)
    safeDestroyWindow.argtypes = [HWND]
    safeDestroyWindow.restype = BOOL

    OpenClipboard = windll.user32.OpenClipboard
    OpenClipboard.argtypes = [HWND]
    OpenClipboard.restype = BOOL
    
    RegisterClipboardFormat = CheckedCall(windll.user32.RegisterClipboardFormatA)
    RegisterClipboardFormat.restype = UINT

    safeCloseClipboard = CheckedCall(windll.user32.CloseClipboard)
    safeCloseClipboard.argtypes = []
    safeCloseClipboard.restype = BOOL

    safeEmptyClipboard = CheckedCall(windll.user32.EmptyClipboard)
    safeEmptyClipboard.argtypes = []
    safeEmptyClipboard.restype = BOOL

    safeGetClipboardData = CheckedCall(windll.user32.GetClipboardData)
    safeGetClipboardData.argtypes = [UINT]
    safeGetClipboardData.restype = HANDLE

    safeSetClipboardData = CheckedCall(windll.user32.SetClipboardData)
    safeSetClipboardData.argtypes = [UINT, HANDLE]
    safeSetClipboardData.restype = HANDLE

    safeGlobalAlloc = CheckedCall(windll.kernel32.GlobalAlloc)
    safeGlobalAlloc.argtypes = [UINT, c_size_t]
    safeGlobalAlloc.restype = HGLOBAL

    safeGlobalLock = CheckedCall(windll.kernel32.GlobalLock)
    safeGlobalLock.argtypes = [HGLOBAL]
    safeGlobalLock.restype = LPVOID

    safeGlobalUnlock = CheckedCall(windll.kernel32.GlobalUnlock)
    safeGlobalUnlock.argtypes = [HGLOBAL]
    safeGlobalUnlock.restype = BOOL

    GMEM_MOVEABLE = 0x0002
    CF_TEXT = 1
    CF_UNICODETEXT = 13
    toWinFormatName = {
    'html': 'HTML Format',
    'rtf' : 'Rich Text Format'
    }

    @contextlib.contextmanager
    def window():
        """
        Context that provides a valid Windows hwnd.
        """
        # we really just need the hwnd, so setting "STATIC"
        # as predefined lpClass is just fine.
        hwnd = safeCreateWindowExA(0, b"STATIC", None, 0, 0, 0, 0, 0,
                                   None, None, None, None)
        try:
            yield hwnd
        finally:
            try: 
                safeDestroyWindow(hwnd)
            except OSError as e:
                print(e)
                

    @contextlib.contextmanager
    def clipboard(hwnd):
        """
        Context manager that opens the clipboard and prevents
        other applications from modifying the clipboard content.
        """
        # We may not get the clipboard handle immediately because
        # some other application is accessing it (?)
        # We try for at least 500ms to get the clipboard.
        t = time.time() + 0.5
        success = False
        while time.time() < t:
            success = OpenClipboard(hwnd)
            if success:
                break
            time.sleep(0.01)
        if not success:
            raise Exception("Error calling OpenClipboard")

        try:
            yield
        finally:
            safeCloseClipboard()
            
    def get_format(formatName):
        if formatName == 'text':
            return CF_UNICODETEXT

        formatName = toWinFormatName.get(formatName, formatName)
        return RegisterClipboardFormat(formatName)
        
    def set_clipboard_data(format, data):
        count = len(data) + 1
        handle = safeGlobalAlloc(GMEM_MOVEABLE,
                                  count * sizeof(c_char))
        locked_handle = safeGlobalLock(handle)

        ctypes.memmove(c_char_p(locked_handle), c_char_p(data), count * sizeof(c_char))

        safeGlobalUnlock(handle)
        safeSetClipboardData(format, handle)

    def copy_windows(text = None, **kwargs ):
        # This function is heavily based on
        # http://msdn.com/ms649016#_win32_Copying_Information_to_the_Clipboard
        with window() as hwnd:
            # http://msdn.com/ms649048
            # If an application calls OpenClipboard with hwnd set to NULL,
            # EmptyClipboard sets the clipboard owner to NULL;
            # this causes SetClipboardData to fail.
            # => We need a valid hwnd to copy something.
            with clipboard(hwnd):
                safeEmptyClipboard()
                if text is not None:
                    set_clipboard_data(CF_TEXT, text) 
                for fmt, value in kwargs.items():
                    set_clipboard_data(get_format(fmt), value)                  

    def paste_windows(formatName = 'text'):
        with clipboard(None):
            fmt = get_format(formatName)
            handle = safeGetClipboardData(fmt)
            if not handle:
            # GetClipboardData may return NULL with errno == NO_ERROR
            # if the clipboard is empty.
            # (Also, it may return a handle to an empty buffer,
            # but technically that's not empty)
                return ''
            if fmt == CF_UNICODETEXT:
                return c_wchar_p(handle).value
            return c_char_p(handle).value
 
    return copy_windows, paste_windows
