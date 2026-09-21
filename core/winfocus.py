import ctypes
import time

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32


def force_foreground(hwnd):
    fg = user32.GetForegroundWindow()
    cur_thread = user32.GetWindowThreadProcessId(fg, None)
    my_thread = kernel32.GetCurrentThreadId()
    tgt_thread = user32.GetWindowThreadProcessId(hwnd, None)
    if cur_thread != my_thread:
        user32.AttachThreadInput(cur_thread, my_thread, True)
    if tgt_thread != my_thread:
        user32.AttachThreadInput(tgt_thread, my_thread, True)
    user32.BringWindowToTop(hwnd)
    user32.SetForegroundWindow(hwnd)
    if cur_thread != my_thread:
        user32.AttachThreadInput(cur_thread, my_thread, False)
    if tgt_thread != my_thread:
        user32.AttachThreadInput(tgt_thread, my_thread, False)
    time.sleep(0.2)


def is_visible(hwnd):
    return bool(user32.IsWindowVisible(hwnd))