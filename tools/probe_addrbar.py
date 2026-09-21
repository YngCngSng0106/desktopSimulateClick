import time
import pyautogui
import pygetwindow as gw
from pywinauto import Application
from winfocus import force_foreground


def find_xshell():
    for w in gw.getAllWindows():
        if "Xshell" in (w.title or ""):
            return w
    return None


def main():
    win = find_xshell()
    if not win:
        print("!! 未找到 Xshell")
        return
    force_foreground(win._hWnd)
    time.sleep(0.6)

    app = Application(backend="win32").connect(handle=win._hWnd)
    w = app.window(handle=win._hWnd)

    # 定位地址栏输入框（NsComboBox）
    addr = None
    for ctrl in w.children():
        if ctrl.class_name() == "NsComboBox":
            addr = ctrl
            break
    if not addr:
        print("!! 未找到地址栏")
        return
    r = addr.rectangle()
    x, y = (r.left + r.right) // 2, (r.top + r.bottom) // 2
    print(f">> 地址栏 rect={r} 点击 ({x},{y})")
    pyautogui.click(x, y)
    time.sleep(0.8)

    # 清空后输入 URL
    pyautogui.hotkey("ctrl", "a")
    pyautogui.typewrite("ssh://test@127.0.0.1:1", interval=0.03)
    time.sleep(0.5)
    print(">> 已输入 URL，按 Enter 连接（目标为 127.0.0.1:1，会连接失败，用于验证流程）")
    pyautogui.press("enter")
    time.sleep(3)

    titles = [t.title for t in gw.getAllWindows() if t.title.strip()]
    print(">> 连接后窗口标题：")
    for t in titles:
        if "Xshell" in t or "127.0.0.1" in t or "test@" in t:
            print(f"   {t!r}")
    print(">> 主窗口标题（应包含新标签）:", find_xshell().title)

    # 关闭测试标签
    print(">> 关闭新标签 (Ctrl+F4)")
    pyautogui.hotkey("ctrl", "f4")
    time.sleep(1)


if __name__ == "__main__":
    main()