"""
settings.py — 设置页面
"""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QRadioButton, QButtonGroup, QPushButton, QGroupBox,
    QComboBox, QMessageBox
)
from PyQt5.QtCore import Qt
from config import load_config, save_config


class SettingsDialog(QDialog):
    """设置对话框"""

    def __init__(self, parent=None, is_first_run=False):
        super().__init__(parent)
        self.cfg = load_config()
        self.is_first_run = is_first_run
        self.result_cfg = dict(self.cfg)

        self.setWindowTitle("AI桌面宠物 - 设置")
        self.setFixedSize(420, 500)
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.Tool)

        self.setStyleSheet("""
            QDialog { background: #f8f9fa; font-family: "Microsoft YaHei"; }
            QGroupBox { font-weight: bold; font-size: 13px; border: 1px solid #ddd;
                        border-radius: 8px; margin-top: 10px; padding-top: 15px; }
            QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; }
            QRadioButton { font-size: 12px; padding: 4px; }
            QLabel { font-size: 12px; }
            QLineEdit { border: 1px solid #ddd; border-radius: 6px; padding: 6px; font-size: 12px; }
            QLineEdit:focus { border-color: #78dcff; }
            QPushButton { border-radius: 6px; padding: 8px 16px; font-size: 12px; }
            #saveBtn { background: #78dcff; color: white; font-weight: bold; }
            #saveBtn:hover { background: #5bc0f0; }
            #cancelBtn { background: #eee; color: #666; }
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # 标题
        if is_first_run:
            title = QLabel("👋 欢迎使用AI桌面宠物！")
            title.setStyleSheet("font-size: 16px; font-weight: bold; color: #333;")
            layout.addWidget(title)

            desc = QLabel("选择AI聊天模式（可以跳过，之后随时修改）：")
            desc.setStyleSheet("color: #666; margin-bottom: 5px;")
            layout.addWidget(desc)

        # ─── AI模式选择 ───
        ai_group = QGroupBox("AI聊天模式")
        ai_layout = QVBoxLayout()

        self.ai_group = QButtonGroup()

        self.rb_none = QRadioButton("不使用AI（预设回复，无需配置）")
        self.rb_none.setToolTip("宠物会用固定的可爱回复，不需要任何网络")
        self.ai_group.addButton(self.rb_none, 0)
        ai_layout.addWidget(self.rb_none)

        self.rb_ollama = QRadioButton("Ollama本地AI（需要安装Ollama）")
        self.rb_ollama.setToolTip("完全本地运行，不需要联网，需要下载约1.5GB")
        self.ai_group.addButton(self.rb_ollama, 1)
        ai_layout.addWidget(self.rb_ollama)

        self.rb_api = QRadioButton("在线API（需要API Key）")
        self.rb_api.setToolTip("使用在线AI服务，需要注册并获取API Key")
        self.ai_group.addButton(self.rb_api, 2)
        ai_layout.addWidget(self.rb_api)

        ai_group.setLayout(ai_layout)
        layout.addWidget(ai_group)

        # ─── Ollama设置 ───
        self.ollama_group = QGroupBox("Ollama设置")
        ollama_layout = QVBoxLayout()

        row1 = QHBoxLayout()
        row1.addWidget(QLabel("地址:"))
        self.ollama_url = QLineEdit(self.cfg.get("ollama_url", "http://localhost:11434"))
        row1.addWidget(self.ollama_url)
        ollama_layout.addLayout(row1)

        row2 = QHBoxLayout()
        row2.addWidget(QLabel("模型:"))
        self.ollama_model = QComboBox()
        self.ollama_model.setEditable(True)
        self.ollama_model.addItems(self._detect_ollama_models())
        self.ollama_model.setCurrentText(self.cfg.get("ollama_model", "qwen2.5:1.5b"))
        row2.addWidget(self.ollama_model)
        ollama_layout.addLayout(row2)

        ollama_hint = QLabel("需要先安装Ollama: https://ollama.com")
        ollama_hint.setStyleSheet("color: #999; font-size: 11px;")
        ollama_layout.addWidget(ollama_hint)

        self.ollama_group.setLayout(ollama_layout)
        layout.addWidget(self.ollama_group)

        # ─── API设置 ───
        self.api_group = QGroupBox("在线API设置")
        api_layout = QVBoxLayout()

        row3 = QHBoxLayout()
        row3.addWidget(QLabel("服务商:"))
        self.api_provider = QComboBox()
        self.api_provider.addItems(["硅基流动 (SiliconFlow)", "DeepSeek", "自定义"])
        self.api_provider.currentIndexChanged.connect(self._on_provider_changed)
        row3.addWidget(self.api_provider)
        api_layout.addLayout(row3)

        row4 = QHBoxLayout()
        row4.addWidget(QLabel("API Key:"))
        self.api_key = QLineEdit(self.cfg.get("api_key", ""))
        self.api_key.setPlaceholderText("粘贴你的API Key")
        self.api_key.setEchoMode(QLineEdit.Password)
        row4.addWidget(self.api_key)
        api_layout.addLayout(row4)

        row5 = QHBoxLayout()
        row5.addWidget(QLabel("地址:"))
        self.api_url = QLineEdit(self.cfg.get("api_base_url", ""))
        row5.addWidget(self.api_url)
        api_layout.addLayout(row5)

        row6 = QHBoxLayout()
        row6.addWidget(QLabel("模型:"))
        self.api_model = QComboBox()
        self.api_model.setEditable(True)
        self.api_model.addItems([
            "Qwen/Qwen2.5-1.5B-Instruct",
            "Qwen/Qwen2.5-7B-Instruct",
            "deepseek-chat",
        ])
        self.api_model.setCurrentText(self.cfg.get("api_model", "Qwen/Qwen2.5-1.5B-Instruct"))
        row6.addWidget(self.api_model)
        api_layout.addLayout(row6)

        api_hint = QLabel("免费注册: siliconflow.cn 或 platform.deepseek.com")
        api_hint.setStyleSheet("color: #999; font-size: 11px;")
        api_layout.addWidget(api_hint)

        self.api_group.setLayout(api_layout)
        layout.addWidget(self.api_group)

        # ─── 按钮 ───
        btn_layout = QHBoxLayout()

        if not is_first_run:
            cancel_btn = QPushButton("取消")
            cancel_btn.setObjectName("cancelBtn")
            cancel_btn.clicked.connect(self.reject)
            btn_layout.addWidget(cancel_btn)

        save_btn = QPushButton("开始使用" if is_first_run else "保存")
        save_btn.setObjectName("saveBtn")
        save_btn.clicked.connect(self._save)
        btn_layout.addWidget(save_btn)

        layout.addLayout(btn_layout)

        # 初始化状态
        self._load_current()
        self._update_visibility()
        self.ai_group.buttonClicked.connect(self._update_visibility)

    def _detect_ollama_models(self):
        """自动检测本机已安装的Ollama模型，失败则返回常用推荐列表"""
        try:
            import requests
            url = self.cfg.get("ollama_url", "http://localhost:11434")
            resp = requests.get(f"{url}/api/tags", timeout=3)
            if resp.status_code == 200:
                models = [m["name"] for m in resp.json().get("models", [])
                          if m.get("name") and "embed" not in m["name"]]
                if models:
                    return models
        except Exception:
            pass
        return ["qwen2.5:1.5b", "qwen2.5:0.5b", "phi3:mini", "llama3.2:1b"]

    def _load_current(self):
        """加载当前配置到UI"""
        mode = self.cfg.get("ai_mode", "none")
        if mode == "none":
            self.rb_none.setChecked(True)
        elif mode == "ollama":
            self.rb_ollama.setChecked(True)
        elif mode == "api":
            self.rb_api.setChecked(True)

        # API服务商
        provider = self.cfg.get("api_provider", "siliconflow")
        provider_map = {"siliconflow": 0, "deepseek": 1, "custom": 2}
        self.api_provider.setCurrentIndex(provider_map.get(provider, 0))
        self._on_provider_changed()

    def _update_visibility(self):
        """根据选择显示/隐藏设置区域"""
        is_none = self.rb_none.isChecked()
        is_ollama = self.rb_ollama.isChecked()
        is_api = self.rb_api.isChecked()

        self.ollama_group.setVisible(is_ollama)
        self.api_group.setVisible(is_api)

    def _on_provider_changed(self):
        """切换服务商时更新默认值"""
        idx = self.api_provider.currentIndex()
        if idx == 0:  # SiliconFlow
            self.api_url.setText("https://api.siliconflow.cn/v1")
            self.api_model.setCurrentText("Qwen/Qwen2.5-1.5B-Instruct")
        elif idx == 1:  # DeepSeek
            self.api_url.setText("https://api.deepseek.com/v1")
            self.api_model.setCurrentText("deepseek-chat")
        # 自定义不改

    def _save(self):
        """保存配置"""
        if self.rb_none.isChecked():
            self.result_cfg["ai_mode"] = "none"
        elif self.rb_ollama.isChecked():
            self.result_cfg["ai_mode"] = "ollama"
            self.result_cfg["ollama_url"] = self.ollama_url.text().strip()
            self.result_cfg["ollama_model"] = self.ollama_model.currentText().strip()
        elif self.rb_api.isChecked():
            self.result_cfg["ai_mode"] = "api"
            key = self.api_key.text().strip()
            if not key:
                QMessageBox.warning(self, "提示", "请输入API Key")
                return
            self.result_cfg["api_key"] = key
            self.result_cfg["api_base_url"] = self.api_url.text().strip()
            self.result_cfg["api_model"] = self.api_model.currentText().strip()

            provider_map = {0: "siliconflow", 1: "deepseek", 2: "custom"}
            self.result_cfg["api_provider"] = provider_map.get(
                self.api_provider.currentIndex(), "custom")

        self.result_cfg["first_run"] = False
        save_config(self.result_cfg)
        self.cfg = self.result_cfg
        self.accept()

    def get_config(self):
        return self.result_cfg
