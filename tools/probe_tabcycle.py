import time
import pyautogui
import pygetwindow as gw
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

    start = win.title
    print(f">> 初始标题: {start!r}")

    # 循环 Ctrl+Tab，记录每次标题变化
    seen = [start]
    for i in range(8):
        pyautogui.hotkey("ctrl", "tab")
        time.sleep(0.8)
        t = win.title
        if t != seen[-1]:
            print(f">> [{i+1}] Ctrl+Tab 后标题: {t!r}")
        seen.append(t)
        if i >= 1 and t == start:
            print(">> 已回到初始标签")
            break

    # 回到初始标题
    guard = 0
    while win.title != start and guard < 20:
        pyautogui.hotkey("ctrl", "tab")
        time.sleep(0.8)
        guard += 1
    print(f">> 已恢复初始标签: {win.title == start} (转了 {guard} 次)")


if __name__ == "__main__":
    main()