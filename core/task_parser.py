import json

VALID_ACTIONS = {"switch_tab", "send_command", "wait"}


class TaskError(Exception):
    pass


def normalize_step(step, index):
    if isinstance(step, str):
        return {"action": "send_command", "command": step, "wait": None}
    if not isinstance(step, dict):
        raise TaskError(f"第 {index} 步必须是字符串或对象")
    if "action" in step:
        action = step["action"]
        if action not in VALID_ACTIONS:
            raise TaskError(f"第 {index} 步的 action '{action}' 不支持，可用: {sorted(VALID_ACTIONS)}")
        if action == "switch_tab" and "tab" not in step:
            raise TaskError(f"第 {index} 步 switch_tab 缺少 tab 字段")
        if action == "send_command" and "command" not in step:
            raise TaskError(f"第 {index} 步 send_command 缺少 command 字段")
        return dict(step)
    if "tab" in step and "command" in step:
        return {"action": "send_command", "command": step["command"],
                "tab": step["tab"], "wait": step.get("wait")}
    if "command" in step:
        return {"action": "send_command", "command": step["command"],
                "tab": step.get("tab"), "wait": step.get("wait")}
    raise TaskError(f"第 {index} 步无法识别，请使用 action/command 字段")


def load_task(path):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise TaskError("任务详情必须是 JSON 对象")
    if "steps" not in data or not isinstance(data["steps"], list) or not data["steps"]:
        raise TaskError("任务详情缺少 steps 列表（至少一步）")
    steps = [normalize_step(s, i + 1) for i, s in enumerate(data["steps"])]
    return {"name": data.get("name", path), "steps": steps}