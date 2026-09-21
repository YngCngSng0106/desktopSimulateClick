import os
import queue
import threading
import time
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from core.task_parser import load_task, TaskError
from core.xshell import XshellController, XshellError
from core.executor import Executor

LOG_TAGS = {
    "info": ("#333333", None),
    "step": ("#005f9e", None),
    "success": ("#1a7f37", None),
    "error": ("#d1242f", None),
    "warn": ("#9a6700", None),
    "done": ("#8250df", None),
}


class SimulatorApp(tk.Tk):
    def __init__(self, cfg):
        super().__init__()
        self.cfg = cfg
        self.title("桌面模拟点击器 - Xshell 命令执行")
        self.geometry("900x620")

        self.task = None
        self.task_path = None
        self.queue = queue.Queue()
        self.executor = None
        self.worker = None
        self.running = False

        self._build_ui()
        self._poll_queue()

    def _build_ui(self):
        top = ttk.Frame(self, padding=(8, 6))
        top.pack(fill="x")
        ttk.Button(top, text="载入任务", command=self._load_task).pack(side="left")
        ttk.Button(top, text="重新加载", command=self._reload_task).pack(side="left", padx=(6, 0))
        self.btn_start = ttk.Button(top, text="▶ 开始执行", command=self._start, state="disabled")
        self.btn_start.pack(side="left", padx=(6, 0))
        self.btn_stop = ttk.Button(top, text="■ 停止", command=self._stop, state="disabled")
        self.btn_stop.pack(side="left", padx=(6, 0))
        ttk.Button(top, text="检测 Xshell", command=self._check_xshell).pack(side="left", padx=(6, 0))
        self.lbl_task = ttk.Label(top, text="未载入任务", foreground="#666")
        self.lbl_task.pack(side="right")

        paned = ttk.PanedWindow(self, orient="horizontal")
        paned.pack(fill="both", expand=True, padx=8, pady=6)

        left = ttk.Frame(paned)
        ttk.Label(left, text="任务步骤", font=("Microsoft YaHei UI", 10, "bold")).pack(anchor="w")
        self.tree = ttk.Treeview(left, columns=("no", "action", "content"), show="headings", height=12)
        self.tree.heading("no", text="序号")
        self.tree.heading("action", text="动作")
        self.tree.heading("content", text="内容")
        self.tree.column("no", width=46, anchor="center", stretch=False)
        self.tree.column("action", width=110, anchor="center", stretch=False)
        self.tree.column("content", width=300)
        vsb = ttk.Scrollbar(left, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(fill="both", expand=True, side="left")
        vsb.pack(fill="y", side="right")
        paned.add(left, weight=1)

        right = ttk.Frame(paned)
        ttk.Label(right, text="执行日志", font=("Microsoft YaHei UI", 10, "bold")).pack(anchor="w")
        self.txt = tk.Text(right, wrap="word", state="disabled", font=("Consolas", 10),
                           bg="#fafafa", fg="#111")
        for tag, (fg, bg) in LOG_TAGS.items():
            self.txt.tag_configure(tag, foreground=fg, background=bg)
        tvsb = ttk.Scrollbar(right, orient="vertical", command=self.txt.yview)
        self.txt.configure(yscrollcommand=tvsb.set)
        self.txt.pack(fill="both", expand=True, side="left")
        tvsb.pack(fill="y", side="right")
        paned.add(right, weight=1)

        self.status = tk.StringVar(value="就绪")
        ttk.Label(self, textvariable=self.status, relief="sunken", anchor="w",
                  padding=(6, 2)).pack(fill="x", side="bottom")

    def _log(self, msg, tag="info"):
        self.queue.put(("log", msg, tag))

    def _poll_queue(self):
        try:
            while True:
                item = self.queue.get_nowait()
                if item[0] == "log":
                    _, msg, tag = item
                    self._append_log(msg, tag)
                elif item[0] == "step":
                    _, i, total, step = item
                    self._mark_step(i, total, step)
                elif item[0] == "done":
                    _, ok = item
                    self._on_done(ok)
        except queue.Empty:
            pass
        self.after(100, self._poll_queue)

    def _append_log(self, msg, tag="info"):
        ts = time.strftime("%H:%M:%S")
        self.txt.configure(state="normal")
        self.txt.insert("end", f"[{ts}] {msg}\n", tag)
        self.txt.see("end")
        self.txt.configure(state="disabled")

    def _mark_step(self, i, total, step):
        if self.tree.get_children():
            item = self.tree.get_children()[i - 1] if i - 1 < len(self.tree.get_children()) else None
            if item:
                self.tree.item(item, tags=("current",))
        self.tree.selection_set(self.tree.get_children()[i - 1]) if self.tree.get_children() else None
        self.tree.see(self.tree.get_children()[i - 1]) if self.tree.get_children() else None
        self.status.set(f"执行中… 第 {i}/{total} 步")

    def _on_done(self, ok):
        self.running = False
        self.btn_start.configure(state="normal")
        self.btn_stop.configure(state="disabled")
        self.status.set("执行完成 ✓" if ok else "执行结束（存在失败）")

    def _load_task(self):
        path = filedialog.askopenfilename(
            title="选择任务详情文件", filetypes=[("JSON 任务", "*.json"), ("所有文件", "*.*")])
        if not path:
            return
        self._set_task(path)

    def _set_task(self, path):
        try:
            self.task = load_task(path)
            self.task_path = path
            self.lbl_task.configure(text=os.path.basename(path))
            self._populate_tree()
            self.btn_start.configure(state="normal")
            self._log(f"任务已载入：{self.task['name']}（{len(self.task['steps'])} 步）", "success")
        except (TaskError, OSError, ValueError) as e:
            messagebox.showerror("任务加载失败", str(e))
            self._log(f"任务加载失败：{e}", "error")

    def _reload_task(self):
        if self.task_path:
            self._set_task(self.task_path)

    def _populate_tree(self):
        self.tree.delete(*self.tree.get_children())
        for i, step in enumerate(self.task["steps"], 1):
            action = {
                "switch_tab": "切换标签",
                "send_command": "发送命令",
                "wait": "等待",
            }.get(step["action"], step["action"])
            content = ""
            if step["action"] == "switch_tab":
                content = step["tab"]
            elif step["action"] == "send_command":
                content = step["command"]
                if step.get("tab"):
                    content = f"[切到 {step['tab']}] {content}"
            elif step["action"] == "wait":
                content = f"{step.get('seconds', 0)} 秒"
            self.tree.insert("", "end", values=(i, action, content))

    def _check_xshell(self):
        try:
            ctl = XshellController(self.cfg, self._log)
            hwnd = ctl._find_hwnd()
            if hwnd:
                title = ctl.window_title()
                self._log(f"检测到 Xshell 窗口：{title}", "success")
                messagebox.showinfo("检测结果", f"已找到 Xshell 窗口\n{title}")
            else:
                self._log("未找到 Xshell 窗口", "error")
                messagebox.showwarning("检测结果", "未找到 Xshell 窗口，请先打开 Xshell")
        except Exception as e:
            self._log(f"检测失败：{e}", "error")

    def _start(self):
        if not self.task or self.running:
            return
        self.running = True
        self.btn_start.configure(state="disabled")
        self.btn_stop.configure(state="normal")
        self.status.set("执行中…")
        ctl = XshellController(self.cfg, self._log)
        self.executor = Executor(ctl, self._log, self.cfg,
                                 on_step=lambda i, t, s: self.queue.put(("step", i, t, s)))
        self.worker = threading.Thread(target=self._run_worker, daemon=True)
        self.worker.start()

    def _run_worker(self):
        try:
            ok = self.executor.run(self.task)
        except XshellError as e:
            self._log(f"执行异常：{e}", "error")
            ok = False
        except Exception as e:
            self._log(f"执行异常：{e}", "error")
            ok = False
        self.queue.put(("done", ok))

    def _stop(self):
        if self.executor:
            self.executor.stop()
            self.status.set("正在停止…")

    def on_close(self):
        if self.executor:
            self.executor.stop()
        self.destroy()


def main(cfg):
    app = SimulatorApp(cfg)
    app.protocol("WM_DELETE_WINDOW", app.on_close)
    app.mainloop()