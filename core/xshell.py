import os
import time
import win32gui
import win32con
import pyautogui
import pyperclip
from .winfocus import force_foreground

pyautogui.PAUSE = 0.05


class XshellError(Exception):
    pass


class XshellController:
    def __init__(self, cfg, log):
        self.cfg = cfg
        self.xcfg = cfg["xshell"]
        self.timing = cfg["timing"]
        self.log = log

    def _find_hwnd(self):
        kw = self.xcfg.get("window_title_contains", "Xshell")
        found = None
        import ctypes
        user32 = ctypes.windll.user32
        WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)

        def cb(hwnd, _):
            nonlocal found
            if not user32.IsWindowVisible(hwnd):
                return True
            title = win32gui.GetWindowText(hwnd)
            if title and kw in title:
                found = hwnd
                return False
            return True

        user32.EnumWindows(WNDENUMPROC(cb), None)
        return found

    def _hwnd(self):
        hwnd = self._find_hwnd()
        if not hwnd:
            raise XshellError("未找到 Xshell 窗口，请先打开 Xshell")
        return hwnd

    def window_title(self):
        hwnd = self._hwnd()
        return win32gui.GetWindowText(hwnd)

    def window_rect(self):
        return win32gui.GetWindowRect(self._hwnd())

    def activate(self):
        hwnd = self._hwnd()
        force_foreground(hwnd)
        time.sleep(self.timing["after_activate"])
        if self.xcfg.get("click_title_to_activate", True):
            left, top, right, bottom = self.window_rect()
            pyautogui.click((left + right) // 2, top + 10)
            time.sleep(0.2)

    def _type_text(self, text):
        method = self.xcfg.get("input_method", "paste")
        if method == "paste":
            pyperclip.copy(text)
            time.sleep(0.1)
            pyautogui.hotkey("ctrl", "v")
        else:
            pyautogui.typewrite(text, interval=self.xcfg.get("type_interval", 0.03))
        time.sleep(0.2)

    def send_command(self, command, wait=None):
        self.activate()
        if self.xcfg.get("click_terminal_before_send", True):
            left, top, right, bottom = self.window_rect()
            m = self.xcfg.get("terminal_margin", {"top": 170, "left": 40})
            pyautogui.click(left + m["left"], top + m["top"])
            time.sleep(0.25)
        self._type_text(command)
        pyautogui.press("enter")
        wait = wait if wait is not None else self.timing["after_command"]
        time.sleep(max(wait, 0.1))

    def switch_tab(self, target):
        self.activate()
        start_title = self.window_title()
        if target.lower() in start_title.lower():
            self.log(f"当前标签已匹配: {start_title}")
            return True
        keys = self.xcfg.get("tab_cycle_key", ["ctrl", "tab"])
        wait = self.timing.get("tab_cycle_wait", 0.8)
        for i in range(self.xcfg.get("max_tab_cycle", 30)):
            pyautogui.hotkey(*keys)
            time.sleep(wait)
            title = self.window_title()
            if target.lower() in title.lower():
                self.log(f"已切换到标签: {title}")
                return True
            if title == start_title:
                break
        msg = f"未找到标签 '{target}'（当前标题: {start_title}）"
        if self.xcfg.get("stop_on_tab_not_found", True):
            raise XshellError(msg)
        self.log(f"警告: {msg}")
        return False

    def close_tab(self):
        self.activate()
        pyautogui.hotkey("ctrl", "f4")
        time.sleep(0.5)