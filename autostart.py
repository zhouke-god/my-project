"""
autostart.py — 开机自启动管理
"""
import os
import sys
import json


def get_startup_folder():
    """获取Windows启动文件夹路径"""
    # shell:startup 对应的路径
    appdata = os.environ.get("APPDATA", "")
    return os.path.join(appdata, "Microsoft", "Windows", "Start Menu",
                        "Programs", "Startup")


def get_exe_path():
    """获取当前exe路径"""
    if getattr(sys, 'frozen', False):
        return sys.executable
    else:
        return os.path.abspath(sys.argv[0])


def get_shortcut_path():
    """获取快捷方式路径"""
    return os.path.join(get_startup_folder(), "AI_Pet.lnk")


def is_autostart_enabled():
    """检查是否已设置开机自启动"""
    return os.path.exists(get_shortcut_path())


def enable_autostart():
    """设置开机自启动"""
    try:
        import win32com.client

        shell = win32com.client.Dispatch("WScript.Shell")
        shortcut = shell.CreateShortCut(get_shortcut_path())
        shortcut.Targetpath = get_exe_path()
        shortcut.WorkingDirectory = os.path.dirname(get_exe_path())
        shortcut.Description = "AI Pet - Desktop Pet"
        shortcut.save()

        # 保存配置
        _save_config(True)
        return True
    except Exception as e:
        print(f"[AutoStart] 启用失败: {e}")
        # 备用方案：用bat文件
        return _enable_autostart_bat()


def disable_autostart():
    """取消开机自启动"""
    try:
        shortcut_path = get_shortcut_path()
        if os.path.exists(shortcut_path):
            os.remove(shortcut_path)

        bat_path = shortcut_path.replace(".lnk", ".bat")
        if os.path.exists(bat_path):
            os.remove(bat_path)

        _save_config(False)
        return True
    except Exception as e:
        print(f"[AutoStart] 禁用失败: {e}")
        return False


def _enable_autostart_bat():
    """备用方案：用bat文件实现自启动"""
    try:
        exe_path = get_exe_path()
        bat_path = get_shortcut_path().replace(".lnk", ".bat")
        bat_dir = os.path.dirname(exe_path)

        with open(bat_path, "w") as f:
            f.write(f'@echo off\n')
            f.write(f'cd /d "{bat_dir}"\n')
            f.write(f'start "" "{exe_path}"\n')

        _save_config(True)
        return True
    except Exception as e:
        print(f"[AutoStart] bat方案也失败: {e}")
        return False


CONFIG_FILE = "autostart_config.json"


def _save_config(enabled):
    with open(CONFIG_FILE, "w") as f:
        json.dump({"autostart": enabled}, f)


def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                return json.load(f).get("autostart", False)
        except Exception:
            pass
    return False
