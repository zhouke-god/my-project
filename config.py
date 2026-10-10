"""
config.py — 配置管理
"""
import json
import os

CONFIG_FILE = "pet_config.json"

# 默认配置
DEFAULT_CONFIG = {
    "ai_mode": "none",           # none / ollama / api
    "api_provider": "siliconflow", # siliconflow / deepseek / custom
    "api_key": "",
    "api_base_url": "https://api.siliconflow.cn/v1",
    "api_model": "Qwen/Qwen2.5-1.5B-Instruct",
    "ollama_url": "http://localhost:11434",
    "ollama_model": "qwen2.5:1.5b",
    "first_run": True,
    "pet_name": "团子",
}


def load_config():
    """加载配置"""
    if not os.path.exists(CONFIG_FILE):
        return dict(DEFAULT_CONFIG)
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        # 合并默认值（防止缺少新字段）
        for k, v in DEFAULT_CONFIG.items():
            if k not in cfg:
                cfg[k] = v
        return cfg
    except Exception:
        return dict(DEFAULT_CONFIG)


def save_config(cfg):
    """保存配置"""
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"保存配置失败: {e}")
