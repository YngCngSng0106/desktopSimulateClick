import ctypes
import time
import win32gui
import win32con
import win32api

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32


def force_foreground(hwnd):
    """强制把窗口置前（绕过 Windows 前台锁定限制）"""
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
    time.sleep(0.3)


def post_key(hwnd, vk, extended=False, keyup=False):
    """直接向窗口投递按键消息（无需窗口前台）"""
    lparam = 1
    if extended:
        lparam |= (1 << 24) | (1 << 29)
    if keyup:
        lparam |= (1 << 30) | (1 << 31)
        msg = win32con.WM_KEYUP
    else:
        msg = win32con.WM_KEYDOWN
    win32api.PostMessage(hwnd, msg, vk, lparam)


def post_syskey(hwnd, vk, keyup=False):
    lparam = 1
    if keyup:
        lparam |= (1 << 30) | (1 << 31)
        msg = win32con.WM_SYSKEYUP
    else:
        msg = win32con.WM_SYSKEYDOWN
    win32api.PostMessage(hwnd, msg, vk, lparam)


def send_alt_menu(hwnd, letters, interval=0.15):
    """发 Alt 打开菜单栏，再依次按助记符，如 send_alt_menu(hwnd, ['F','N'])"""
    post_syskey(hwnd, win32con.VK_MENU)
    time.sleep(interval)
    for ch in letters:
        vk = ord(ch.upper())
        post_key(hwnd, vk)
        time.sleep(interval)
    post_syskey(hwnd, win32con.VK_MENU, keyup=True)


def send_ctrl_chord(hwnd, key_char, interval=0.15):
    """发 Ctrl+字符 组合"""
    vk = ord(key_char.upper())
    win32api.PostMessage(hwnd, win32con.WM_KEYDOWN, win32con.VK_CONTROL, 1)
    time.sleep(0.05)
    win32api.PostMessage(hwnd, win32con.WM_KEYDOWN, vk, 1)
    time.sleep(interval)
    win32api.PostMessage(hwnd, win32con.WM_KEYUP, vk, 0xC0000001)
    win32api.PostMessage(hwnd, win32con.WM_KEYUP, win32con.VK_CONTROL, 0xC0000001)


if __name__ == "__main__":
    print("focus helper loaded")