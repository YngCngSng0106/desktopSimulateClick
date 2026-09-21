import sys
import time
import json
import ctypes
import pyautogui
import pywinauto
import pygetwindow as gw
from pywinauto import Application
import win32gui

XSH_EXE = r"C:\Program Files (x86)\NetSarang\Xshell 7\Xshell.exe"


def dump_all_windows():
    out = []

    def cb(hwnd, _):
        if not win32gui.IsWindowVisible(hwnd):
            return True
        t = win32gui.GetWindowText(hwnd) or ""
        if not t.strip():
            return True
        cls = win32gui.GetClassName(hwnd)
        rect = win32gui.GetWindowRect(hwnd)
        out.append(f"[{hwnd}] class={cls} title={t!r} rect={rect}")
        return True

    win32gui.EnumWindows(cb, None)
    return out


def find_xshell():
    wins = gw.getAllWindows()
    for w in wins:
        t = (w.title or "").strip()
        if "Xshell" in t:
            return w
    return None


def main():
    win = find_xshell()
    launched = False
    if not win:
        print(">> 启动 Xshell ...")
        pyautogui.hotkey("win", "r")
        time.sleep(0.8)
        pyautogui.typewrite(XSH_EXE, interval=0.02)
        pyautogui.press("enter")
        launched = True
        time.sleep(5)
        win = find_xshell()
    if not win:
        print("!! 未找到 Xshell")
        sys.exit(1)

    print(f">> Xshell 主窗口: {win.title!r}")
    app = Application(backend="win32").connect(handle=win._hWnd)
    w = app.window(handle=win._hWnd)
    w.set_focus()
    time.sleep(1)

    print(">> 尝试 Ctrl+N ...")
    w.type_keys("^n", pause=0.1)
    time.sleep(2)

    titles = dump_all_windows()
    print(">> 当前可见顶层窗口：")
    for line in titles:
        print("   " + line)

    dlg = None
    for line in titles:
        if any(k in line for k in ["新建会话", "New Session"]):
            dlg = line
            break
    if not dlg:
        print("!! 未发现新建会话对话框，尝试 Alt+F 菜单路径 ...")
        w.type_keys("%f", pause=0.3)
        time.sleep(0.5)
        # 尝试输入菜单项关键字
        pyautogui.press("n")
        time.sleep(2)
        titles2 = dump_all_windows()
        for line in titles2:
            print("   [menu] " + line)
        dlg = None
        for line in titles2:
            if any(k in line for k in ["新建会话", "New Session"]):
                dlg = line
                break

    if not dlg:
        print("!! 仍然未找到对话框")
        sys.exit(2)

    # 探测对话框控件
    hwnd = int(dlg.split("]")[0].strip("["))
    app2 = Application(backend="win32").connect(handle=hwnd)
    top = app2.top_window()
    controls = []

    def walk(elem, depth=0):
        info = elem.element_info
        controls.append({
            "depth": depth,
            "type": info.control_type,
            "name": info.name,
            "class": info.class_name,
            "rect": [info.rectangle.left, info.rectangle.top,
                     info.rectangle.right, info.rectangle.bottom],
            "hwnd": info.handle,
        })
        for ch in elem.children():
            walk(ch, depth + 1)

    try:
        walk(top)
        print(">> 对话框控件树：")
        for c in controls:
            pad = "   " * c["depth"]
            r = c["rect"]
            print(f"{pad}{c['type']} | {c['name']!r} | {c['class']} | rect={r} hwnd={c['hwnd']}")
        with open(r"config\xshell_dialog_probe.json", "w", encoding="utf-8") as f:
            json.dump(controls, f, ensure_ascii=False, indent=2)
        print(">> 已保存 config\\xshell_dialog_probe.json")
    except Exception as ex:
        print(f"!! 探测控件失败: {ex}")

    try:
        top.close()
        print(">> 已关闭对话框")
    except Exception as ex:
        print(f"!! 关闭对话框失败: {ex}")


if __name__ == "__main__":
    main()