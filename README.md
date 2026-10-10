# AI桌面宠物 — 团子

一个可爱的AI桌面宠物，住在你的桌面上，能聊天、能互动。

## 快速开始

```bash
pip install PyQt5 requests
python main.py
```

**首次运行会弹出设置页面**，选择AI聊天模式：
- **不使用AI**：宠物用预设回复，无需任何配置，直接能玩
- **Ollama本地AI**：需要安装Ollama，完全离线
- **在线API**：需要注册获取API Key

## 操作

| 操作 | 效果 |
|------|------|
| 左键点击 | 摸头（增加快乐度） |
| 左键拖动 | 移动宠物位置 |
| 右键 | 打开菜单 |

## 右键菜单

| 功能 | 效果 |
|------|------|
| 🍖 喂食 | 增加饱食度 |
| 🤚 摸头 | 增加快乐度 |
| 🎮 玩耍 | 增加快乐度，消耗精力 |
| 💤 睡觉 | 恢复精力 |
| 💬 聊天 | 打开AI聊天窗口 |
| ⚙️ 设置 | 修改AI模式 |
| ❌ 退出 | 保存并退出 |

## AI聊天配置

### 方式1：不使用AI（推荐入门）
无需配置，宠物会用可爱的预设回复。

### 方式2：Ollama本地AI（推荐进阶）
1. 下载安装 Ollama: https://ollama.com
2. 运行: `ollama pull qwen2.5:0.5b`
3. 右键 → 设置 → 选择"Ollama本地AI"

### 方式3：在线API
1. 注册硅基流动: https://siliconflow.cn （免费）
2. 获取API Key
3. 右键 → 设置 → 选择"在线API" → 粘贴Key

## 文件结构

```
AI桌面宠物/
├── README.md          # 说明文档
├── requirements.txt   # Python依赖
├── main.py            # 入口
├── pet.py             # 宠物状态 + AI聊天
├── ui.py              # 界面（桌面宠物 + 聊天窗口）
├── config.py          # 配置管理
├── settings.py        # 设置页面
├── pet_config.json    # 用户配置（运行后生成）
└── pet_save.json      # 宠物存档（运行后生成）
```

## 打包分享给别人

把整个文件夹打包发给别人，对方只需要：
```bash
pip install PyQt5 requests
python main.py
```
首次运行会弹出设置页面，选择"不使用AI"就能直接玩。
