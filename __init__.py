from clipboard import (init_osx_clipboard, init_windows_clipboard)
from platform import system

def determine_clipboard():
    # Determine the OS/platform and set
    # the copy() and paste() functions accordingly.
    if system() == 'Windows':
        return init_windows_clipboard()
    elif system() == 'Darwin':
        return init_osx_clipboard()

copy, paste = determine_clipboard()