import sys
import time
import pyautogui
import pygetwindow as gw
from pywinauto import Application
import win32gui
from winfocus import force_foreground

XSH_EXE = r"C:\Program Files (x86)\NetSarang\Xshell 7\Xshell.exe"


def find_xshell():
    for w in gw.getAllWindows():
        if "Xshell" in (w.title or ""):
            return w
    return None


def find_dlg():
    for w in gw.getAllWindows():
        if "新建会话" in (w.title or ""):
            return w
    return None


def has_dialog():
    time.sleep(1.5)
    return find_dlg() is not None


def close_if_open():
    d = find_dlg()
    if d:
        try:
            import pywinauto
            a = Application(backend="win32").connect(handle=d._hWnd)
            a.top_window().close()
        except Exception:
            pass
        time.sleep(1)
    # 若仍有，按 Esc
    if find_dlg():
        pyautogui.press("esc")
        time.sleep(0.8)


def main():
    win = find_xshell()
    if not win:
        print("启动 Xshell"); sys.exit(1)
    force_foreground(win._hWnd)
    time.sleep(0.5)
    app = Application(backend="win32").connect(handle=win._hWnd)
    w = app.window(handle=win._hWnd)

    methods = {}

    # 方法1: Alt+F 然后 N
    close_if_open()
    pyautogui.hotkey("alt", "f")
    time.sleep(0.8)
    pyautogui.press("n")
    methods["Alt+F,N (real keys)"] = has_dialog()
    close_if_open()

    # 方法2: Ctrl+N
    pyautogui.hotkey("ctrl", "n")
    methods["Ctrl+N"] = has_dialog()
    close_if_open()

    # 方法3: Ctrl+Alt+N (会话管理器)
    pyautogui.hotkey("ctrl", "alt", "n")
    methods["Ctrl+Alt+N"] = has_dialog()
    close_if_open()

    # 方法4: F10, F, N
    pyautogui.press("f10")
    time.sleep(0.6)
    pyautogui.press("f")
    time.sleep(0.6)
    pyautogui.press("n")
    methods["F10,F,N"] = has_dialog()
    close_if_open()

    # 方法5: pywinauto 菜单
    close_if_open()
    try:
        menu = w.menu()
        items = menu.items()
        print(">> 菜单项: ", [it.text() for it in items])
        menu.get_menu_path("文件(&F)").get_menu_path("新建会话(&N)").click()
        methods["pywinauto menu"] = has_dialog()
    except Exception as ex:
        methods["pywinauto menu"] = f"ERR {ex}"
    close_if_open()

    # 方法6: 直接 SendMessage 主窗口 WM_COMMAND 0x111 找菜单ID
    # 略过，先打印结果

    print("== 结果 ==")
    for k, v in methods.items():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    main()