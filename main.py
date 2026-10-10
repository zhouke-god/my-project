"""
main.py — AI桌面宠物入口
"""
import sys
import os
import traceback

# 确保当前目录在Python路径中，并把工作目录切到程序所在目录
# （否则从其他目录运行时，存档/精灵图会生成到错误位置）
if getattr(sys, 'frozen', False):
    os.chdir(os.path.dirname(sys.executable))
    sys.path.insert(0, os.path.dirname(sys.executable))
else:
    _script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(_script_dir)
    sys.path.insert(0, _script_dir)

try:
    from PyQt5.QtWidgets import QApplication, QMessageBox
    from pet import PetState, ChatAI
    from ui import PetWidget, ChatWindow
    from config import load_config
    from settings import SettingsDialog
    from pet_selector import PetSelectorDialog, load_selected_pet, save_selected_pet
    from pets import get_pet_data
    from eula import EulaDialog, is_eula_accepted, AboutDialog

    def _acquire_single_instance_lock():
        """Windows命名互斥体防双开。已存在实例时返回None；否则持有锁直到进程结束"""
        import ctypes
        kernel32 = ctypes.windll.kernel32
        mutex = kernel32.CreateMutexW(None, False, "AIDesktopPetSingleInstanceMutex")
        if kernel32.GetLastError() == 183:  # ERROR_ALREADY_EXISTS
            kernel32.CloseHandle(mutex)
            return None
        return mutex

    def main():
        app = QApplication(sys.argv)
        app.setQuitOnLastWindowClosed(False)

        # 单实例检查：避免双开出现两只宠物
        _mutex = _acquire_single_instance_lock()
        if _mutex is None:
            QMessageBox.information(None, "AI桌面宠物", "宠物已经在桌面上啦，去找找看吧~")
            sys.exit(0)

        # 首次运行显示EULA
        if not is_eula_accepted():
            eula = EulaDialog()
            if not eula.exec_():
                sys.exit(0)

        # 加载配置
        cfg = load_config()

        # 首次运行弹出设置
        if cfg.get("first_run", True):
            # 先选宠物
            selector = PetSelectorDialog()
            if selector.exec_():
                pet_name = selector.current_pet
                save_selected_pet(pet_name)
            else:
                pet_name = "团子"

            # 再设置AI
            dialog = SettingsDialog(is_first_run=True)
            dialog.exec_()
            cfg = dialog.get_config()
        else:
            pet_name = load_selected_pet()

        # 获取宠物数据
        pet_data = get_pet_data(pet_name)

        # 初始化宠物状态
        pet = PetState()
        pet.name = pet_name

        # 初始化AI
        chat_ai = ChatAI(pet)
        import pet as pet_module
        pet_module.PET_PERSONALITY = pet_data["personality"]

        # 创建桌面宠物窗口
        try:
            pet_widget = PetWidget(pet)
            print(f"[DEBUG] PetWidget创建成功")
        except Exception as e:
            print(f"[DEBUG] PetWidget创建失败: {e}")
            raise

        # 创建聊天窗口
        chat_window = ChatWindow(pet, chat_ai)

        # 连接信号
        def open_chat():
            # 聊天框从宠物上方弹出；上方放不下则放到下面，并保持在屏幕内
            pw = pet_widget
            x = pw.x() + pw.width() // 2 - chat_window.width() // 2
            y = pw.y() - chat_window.height() - 12
            screen = QApplication.primaryScreen().availableGeometry()
            x = max(screen.left(), min(x, screen.right() - chat_window.width()))
            if y < screen.top():
                y = pw.y() + pw.height() + 12
            chat_window.move(x, y)
            chat_window.show()
            chat_window.raise_()
            chat_window.activateWindow()

        def open_settings():
            dialog = SettingsDialog()
            if dialog.exec_():
                chat_ai.reload_config()

        def change_pet():
            selector = PetSelectorDialog(current_pet=pet.name)
            if selector.exec_():
                new_name = selector.current_pet
                save_selected_pet(new_name)
                pet.name = new_name
                new_data = get_pet_data(new_name)
                pet_module.PET_PERSONALITY = new_data["personality"]
                # 重置皮肤为新宠物的默认颜色
                pet_widget.skin_name = "默认蓝"
                from features import SKINS
                pet_widget.skin_colors = SKINS["默认蓝"]
                # 强制重绘
                pet_widget.update()
                # 显示问候语
                pet_widget.show_bubble(new_data["greeting"], duration=4)
                print(f"[DEBUG] 切换到宠物: {new_name}")

        def open_about():
            from eula import AboutDialog
            dialog = AboutDialog()
            dialog.exec_()

        pet_widget.chat_requested.connect(open_chat)
        pet_widget.settings_requested.connect(open_settings)
        pet_widget.change_pet_requested.connect(change_pet)
        pet_widget.about_requested.connect(open_about)

        # 显示宠物
        print(f"[DEBUG] 显示宠物: {pet.name}")
        pet_widget.show()
        print(f"[DEBUG] 宠物窗口已显示，位置: {pet_widget.x()}, {pet_widget.y()}")
        pet_widget.show_bubble(pet_data["greeting"], duration=4)
        print(f"[DEBUG] 启动完成")

        sys.exit(app.exec_())

    if __name__ == "__main__":
        main()

except Exception as e:
    # 显示错误信息
    error_msg = traceback.format_exc()
    print(error_msg)
    try:
        from PyQt5.QtWidgets import QApplication, QMessageBox
        app = QApplication(sys.argv)
        QMessageBox.critical(None, "启动错误", f"程序启动失败：\n\n{error_msg}")
    except:
        input(f"程序启动失败，按回车退出...\n{error_msg}")
