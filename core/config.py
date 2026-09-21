import json
import os
import copy

DEFAULTS = {
    "xshell": {
        "exe": r"C:\Program Files (x86)\NetSarang\Xshell 7\Xshell.exe",
        "window_title_contains": "Xshell",
        "input_method": "paste",
        "type_interval": 0.03,
        "click_title_to_activate": True,
        "click_terminal_before_send": True,
        "terminal_margin": {"top": 170, "left": 40, "bottom": 30, "right": 10},
        "tab_cycle_key": ["ctrl", "tab"],
        "max_tab_cycle": 30,
        "stop_on_tab_not_found": True
    },
    "timing": {
        "after_activate": 0.5,
        "tab_cycle_wait": 0.8,
        "after_command": 1.0
    },
    "executor": {
        "stop_on_error": True
    }
}

CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                           "config", "simulator.json")


def _deep_merge(base, override):
    out = copy.deepcopy(base)
    for k, v in override.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = v
    return out


def load_config(path=None):
    cfg = copy.deepcopy(DEFAULTS)
    path = path or CONFIG_PATH
    if os.path.isfile(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                user_cfg = json.load(f)
            cfg = _deep_merge(cfg, user_cfg)
        except Exception as e:
            raise RuntimeError(f"配置加载失败 {path}: {e}")
    return cfg