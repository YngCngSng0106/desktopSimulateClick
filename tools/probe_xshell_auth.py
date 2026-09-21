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


def find_dlg():
    for w in gw.getAllWindows():
        if "新建会话" in (w.title or ""):
            return w
    return None


def open_dialog():
    win = find_xshell()
    force_foreground(win._hWnd)
    time.sleep(0.5)
    pyautogui.click(26, 35)
    time.sleep(0.8)
    pyautogui.press("n")
    time.sleep(1.5)
    return find_dlg()


def dump_tree(dlg):
    try:
        tree = dlg.child_window(class_name="SysTreeView32")
        print(">> 左侧类别树：")
        for item in tree.root().children():
            def walk(node, depth):
                try:
                    name = node.text()
                except Exception:
                    return
                print(f"   {'  ' * depth}- {name!r}")
                try:
                    for ch in node.children():
                        walk(ch, depth + 1)
                except Exception:
                    pass
            walk(item, 1)
    except Exception as ex:
        print(f"!! 读取树失败: {ex}")


def select_tree_by_text(dlg, target):
    """在树中逐层查找包含 target 的项并选中"""
    tree = dlg.child_window(class_name="SysTreeView32")
    root = tree.root()
    found = [None]

    def walk(node, depth):
        for ch in node.children():
            try:
                t = ch.text()
            except Exception:
                continue
            if target in t:
                ch.select()
                found[0] = True
                time.sleep(1.2)
                return True
            walk(ch, depth + 1)

    walk(root, 0)
    return found[0]


def dump_page(dlg, tag):
    print(f">> === {tag} 页面控件 ===")
    try:
        dlg.print_control_identifiers(depth=3)
    except Exception as ex:
        print(f"   print_control_identifiers err: {ex}")
    print("   -- 手工枚举 Edits/Buttons --")
    for ctrl in dlg.children(depth=4):
        cls = ctrl.class_name()
        if cls in ("Edit", "ComboBox", "Button", "CheckBox", "Static"):
            try:
                nm = ctrl.window_text()
            except Exception:
                nm = ""
            r = ctrl.rectangle()
            print(f"   {cls} | {nm!r} | rect=({r.left},{r.top},{r.right},{r.bottom}) hwnd={ctrl.handle}")


def main():
    dlg_win = open_dialog()
    if not dlg_win:
        print("!! 对话框未打开")
        return
    print(f">> 对话框: {dlg_win.title!r} rect=({dlg_win.left},{dlg_win.top},{dlg_win.right},{dlg_win.bottom})")
    app = Application(backend="win32").connect(handle=dlg_win._hWnd)
    dlg = app.top_window()

    dump_tree(dlg)
    dump_page(dlg, "常规")

    sel = select_tree_by_text(dlg, "用户身份验证")
    print(f">> 选择'用户身份验证' => {sel}")
    dump_page(dlg, "用户身份验证")

    dlg.close()
    time.sleep(0.8)
    if find_dlg():
        pyautogui.press("esc")


if __name__ == "__main__":
    main()