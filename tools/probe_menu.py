import time
import pyautogui
import pygetwindow as gw
from pywinauto import Application
from winfocus import force_foreground

MENUBAR = (26, 35)  # 菜单栏第一个项"文件"的预估坐标


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


def dump_popup():
    for w in gw.getAllWindows():
        t = (w.title or "").strip()
        if t and t not in ("", "Program Manager"):
            cls = w._hWnd
    # 打印所有可见窗口标题
    print("  当前窗口:")
    for w in gw.getAllWindows():
        t = (w.title or "").strip()
        if t:
            print(f"    {t!r}")


def main():
    win = find_xshell()
    if not win:
        print("!! 未找到 Xshell")
        return
    force_foreground(win._hWnd)
    time.sleep(0.6)

    print(f">> 点击菜单栏 '文件' @ {MENUBAR}")
    pyautogui.click(*MENUBAR)
    time.sleep(1)
    dump_popup()

    # 菜单打开后，直接按键盘 N（菜单项助记符），或点击
    if not find_dlg():
        print(">> 按 N ...")
        pyautogui.press("n")
        time.sleep(1.5)
    if find_dlg():
        print(">> 对话框已打开:", find_dlg().title)
        return

    # 否则用键盘方向键：在文件菜单里第一个项就是 新建会话
    print(">> 按 Down+Enter ...")
    pyautogui.press("down")
    time.sleep(0.3)
    pyautogui.press("enter")
    time.sleep(1.5)
    if find_dlg():
        print(">> 对话框已打开:", find_dlg().title)
    else:
        print("!! 仍未打开，截图诊断")
        pyautogui.screenshot(r"config\shot_menu.png")


if __name__ == "__main__":
    main()