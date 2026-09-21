import time
import ctypes
import ctypes.wintypes as wt
import pyautogui
import pyperclip
import pygetwindow as gw
from pywinauto import Application
from winfocus import force_foreground

user32 = ctypes.windll.user32

# TabCtrl 消息
TCM_GETITEMCOUNT = 0x1304
TCM_GETITEMRECT = 0x130A
TCM_GETITEMW = 0x130C
TCM_GETITEMTEXTW = 0x132E
TCIF_TEXT = 0x0001


class TCITEM(ctypes.Structure):
    _fields_ = [
        ("mask", wt.UINT),
        ("dwState", wt.UINT),
        ("dwStateMask", wt.UINT),
        ("pszText", ctypes.c_void_p),
        ("cchTextMax", ctypes.c_int),
        ("iImage", ctypes.c_int),
        ("lParam", wt.LPARAM),
    ]


class RECT(ctypes.Structure):
    _fields_ = [("left", ctypes.c_long), ("top", ctypes.c_long),
                ("right", ctypes.c_long), ("bottom", ctypes.c_long)]


def find_xshell():
    for w in gw.getAllWindows():
        if "Xshell" in (w.title or ""):
            return w
    return None


def get_tabs(tab_hwnd):
    n = user32.SendMessageW(tab_hwnd, TCM_GETITEMCOUNT, 0, 0)
    tabs = []
    for i in range(n):
        buf = ctypes.create_unicode_buffer(256)
        item = TCITEM(TCIF_TEXT, 0, 0, ctypes.cast(buf, ctypes.c_void_p), 256, 0, 0)
        user32.SendMessageW(tab_hwnd, TCM_GETITEMW, i, ctypes.byref(item))
        rc = RECT()
        user32.SendMessageW(tab_hwnd, TCM_GETITEMRECT, i, ctypes.byref(rc))
        tabs.append((i, buf.value, (rc.left, rc.top, rc.right, rc.bottom)))
    return tabs


def main():
    win = find_xshell()
    if not win:
        print("!! 未找到 Xshell")
        return
    force_foreground(win._hWnd)
    time.sleep(0.6)
    app = Application(backend="win32").connect(handle=win._hWnd)
    w = app.window(handle=win._hWnd)

    # 1) 读取标签
    tab = None
    for ctrl in w.children():
        if "TabCtrl" in ctrl.class_name():
            tab = ctrl
            break
    if not tab:
        print("!! 未找到标签控件")
        return
    print(f">> 标签控件: {tab.class_name()}")
    tabs = get_tabs(tab.handle)
    print(">> 当前标签：")
    for i, text, rc in tabs:
        print(f"   [{i}] {text!r} rect={rc}")

    # 2) 测试输出抓取：发一条标记命令，然后尝试 Ctrl+A + Ctrl+C
    marker = f"CAPTURE_PROBE_{int(time.time()*1000)%100000}"
    print(f">> 发送标记命令: echo {marker}")
    pyautogui.typewrite(f"echo {marker}", interval=0.03)
    pyautogui.press("enter")
    time.sleep(1.5)

    print(">> 尝试 Ctrl+A (全选) + Ctrl+C (复制) ...")
    pyperclip.copy("")  # 清空剪贴板
    pyautogui.hotkey("ctrl", "a")
    time.sleep(0.6)
    pyautogui.hotkey("ctrl", "c")
    time.sleep(0.6)
    clip1 = pyperclip.paste()
    print(f">> 剪贴板长度: {len(clip1)}，含标记: {marker in clip1}")

    if marker not in clip1:
        print(">> Ctrl+A 无效，尝试拖拽全选 ...")
        # 拖拽从终端左上到右下（终端区域 T155-B1017，标签条在 T130-155）
        x1, y1 = win.left + 60, win.top + 170
        x2, y2 = win.right - 40, win.bottom - 40
        pyautogui.click(x1, y1)
        time.sleep(0.2)
        pyautogui.moveTo(x1, y1, duration=0.2)
        pyautogui.dragTo(x2, y2, duration=0.8, button="left")
        time.sleep(0.4)
        pyperclip.copy("")
        pyautogui.hotkey("ctrl", "c")
        time.sleep(0.6)
        clip2 = pyperclip.paste()
        print(f">> 拖拽后剪贴板长度: {len(clip2)}，含标记: {marker in clip2}")
        # 取消选区
        pyautogui.press("esc")
        time.sleep(0.3)

    # 抓一段展示
    txt = pyperclip.paste()
    print(">> 抓到的文本前 500 字符：")
    print(txt[:500].replace("\r", ""))


if __name__ == "__main__":
    main()