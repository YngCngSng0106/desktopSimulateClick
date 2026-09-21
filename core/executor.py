import time
import threading


class Executor:
    def __init__(self, controller, log, cfg, on_step=None):
        self.controller = controller
        self.log = log
        self.cfg = cfg
        self.on_step = on_step
        self._stop = threading.Event()

    def stop(self):
        self._stop.set()

    def run(self, task):
        steps = task["steps"]
        total = len(steps)
        self._stop.clear()
        self.log(f"开始执行任务：{task.get('name')}（共 {total} 步）", tag="info")
        ok = True
        for i, step in enumerate(steps, 1):
            if self._stop.is_set():
                self.log(f"已停止（完成 {i - 1}/{total} 步）", tag="warn")
                return False
            desc = self._describe(step)
            self.log(f"[{i}/{total}] {desc}", tag="step")
            if self.on_step:
                self.on_step(i, total, step)
            try:
                self._run_step(step)
            except Exception as e:
                ok = False
                self.log(f"[{i}/{total}] 失败：{e}", tag="error")
                if self.cfg["executor"].get("stop_on_error", True):
                    break
        self.log("任务完成，成功" if ok else "任务结束，存在失败步骤", tag="done")
        return ok

    def _describe(self, step):
        action = step["action"]
        if action == "switch_tab":
            return f"切换到标签：{step['tab']}"
        if action == "send_command":
            return f"发送命令：{step['command']}"
        if action == "wait":
            return f"等待 {step.get('seconds', 0)} 秒"
        return str(action)

    def _run_step(self, step):
        action = step["action"]
        if action == "switch_tab":
            self.controller.switch_tab(step["tab"])
        elif action == "send_command":
            tab = step.get("tab")
            if tab:
                self.controller.switch_tab(tab)
            self.controller.send_command(step["command"], step.get("wait"))
        elif action == "wait":
            seconds = float(step.get("seconds", 0))
            if seconds > 0:
                time.sleep(seconds)