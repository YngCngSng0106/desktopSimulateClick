import time
import ctypes
import ctypes.wintypes as wt
import pyautogui
import pygetwindow as gw
from pywinauto import Application
from winfocus import force_foreground

user32 = ctypes.windll.user32
TVM_GETNEXTITEM = 0x110A
TVM_GETITEMW = 0x113E
TVM_GETITEMA = 0x110D
TVM_EXPAND = 0x1102
TVGN_ROOT = 0
TVGN_NEXT = 1
TVGN_CHILD = 4
TVGN_CARET = 9
TVIF_TEXT = 1
TVM_SELECTITEM = 0x110B
TVE_EXPAND = 2


class TVITEM(ctypes.Structure):
    _fields_ = [
        ("mask", wt.UINT),
        ("hItem", wt.LPVOID),
        ("state", wt.UINT),
        ("stateMask", wt.UINT),
        ("pszText", ctypes.c_void_p),
        ("cchTextMax", ctypes.c_int),
        ("iImage", ctypes.c_int),
        ("iSelectedImage", ctypes.c_int),
        ("cChildren", ctypes.c_int),
        ("lParam", wt.LPARAM),
    ]


def get_item_text(hwnd, hitem):
    # 先试 Unicode，再试 ANSI
    for msg, dtype in ((TVM_GETITEMW, ctypes.c_wchar), (TVM_GETITEMA, ctypes.c_char)):
        buf = ctypes.create_string_buffer(1024)
        item = TVITEM(TVIF_TEXT, hitem, 0, 0, ctypes.cast(buf, ctypes.c_void_p), 1024, 0, 0, 0, 0)
        if user32.SendMessageW(hwnd, msg, 0, ctypes.byref(item)):
            try:
                return buf.value.decode("gbk", "replace") if dtype is ctypes.c_char else buf.value
            except Exception:
                return repr(buf.value)
    return ""


def enum_tree(hwnd):
    def walk(hitem, depth):
        items = []
        h = user32.SendMessageW(hwnd, TVM_GETNEXTITEM, TVGN_CHILD, hitem)
        while h:
            text = get_item_text(hwnd, h)
            items.append((depth, text))
            items.extend(walk(h, depth + 1))
            h = user32.SendMessageW(hwnd, TVM_GETNEXTITEM, TVGN_NEXT, h)
        return items
    root = user32.SendMessageW(hwnd, TVM_GETNEXTITEM, TVGN_ROOT, 0)
    if not root:
        return []
    return walk(root, 0)


def select_item(hwnd, target_text):
    def find(hitem, depth):
        h = user32.SendMessageW(hwnd, TVM_GETNEXTITEM, TVGN_CHILD, hitem)
        while h:
            text = get_item_text(hwnd, h)
            if target_text in text:
                user32.SendMessageW(hwnd, TVM_EXPAND, TVE_EXPAND, h)
                user32.SendMessageW(hwnd, TVM_SELECTITEM, TVGN_CARET, h)
                return True
            if find(h, depth + 1):
                return True
            h = user32.SendMessageW(hwnd, TVM_GETNEXTITEM, TVGN_NEXT, h)
        return False
    root = user32.SendMessageW(hwnd, TVM_GETNEXTITEM, TVGN_ROOT, 0)
    return find(root, 0)


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


def main():
    win = find_xshell()
    force_foreground(win._hWnd)
    time.sleep(0.5)
    pyautogui.click(26, 35)
    time.sleep(0.8)
    pyautogui.press("n")
    time.sleep(1.5)
    dlg = find_dlg()
    if not dlg:
        print("!! 对话框未打开")
        return

    app = Application(backend="win32").connect(handle=dlg._hWnd)
    d = app.top_window()
    tree_ctrl = d.child_window(class_name="SysTreeView32")
    hwnd = tree_ctrl.handle
    print(">> 左侧类别树：")
    for depth, text in enum_tree(hwnd):
        print(f"   {'  ' * depth}- {text!r}")

    ok = select_item(hwnd, "用户身份验证")
    print(f">> 选中'用户身份验证' => {ok}")
    time.sleep(1.5)
    print(">> 切换后的页面控件：")
    def safe_children(ctrl):
        try:
            return list(ctrl.children())
        except Exception:
            return []
    def walk(elem, depth):
        if depth > 5:
            return
        try:
            cls = elem.class_name()
        except Exception:
            return
        if cls in ("Edit", "ComboBox", "Button", "CheckBox", "Static", "RadioButton"):
            try:
                nm = elem.window_text()
            except Exception:
                nm = ""
            r = elem.rectangle()
            print(f"   {'  '*depth}{cls} | {nm!r} | rect=({r.left},{r.top},{r.right},{r.bottom})")
        for ch in safe_children(elem):
            walk(ch, depth + 1)
    walk(d, 0)

    d.close()
    time.sleep(0.8)
    if find_dlg():
        pyautogui.press("esc")


if __name__ == "__main__":
    main()