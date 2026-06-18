# 🧠 AstrBot 用户画像插件

[![AstrBot](https://img.shields.io/badge/AstrBot-Plugin-blue)](https://docs.astrbot.app)
[![Python](https://img.shields.io/badge/Python-3.10+-green)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

为 [AstrBot](https://github.com/Soulter/AstrBot) 提供长期记忆的用户画像系统。支持群聊/私聊隔离、自动学习、AI 优化、LLM 上下文注入等功能，让您的 AI 助手更懂用户。

---

## ✨ 特性

- 📌 **多维度画像** – 支持自定义分类（职业、爱好、性格等），每个分类包含主值、备选（带频率）和历史值。
- 🧠 **自动学习** – 通过正则规则从对话中自动提取标签值，并动态升级主值。
- 💉 **LLM 上下文注入** – 在每次 AI 对话前自动注入精简画像（受冷却控制），提升回答准确性。
- 🤖 **AI 画像优化** – 可调用 LLM 分析画像并提出优化建议（支持通知/半自动/全自动模式）。
- 👥 **群聊/私聊隔离** – 同一用户在不同群组或私聊中的画像相互独立。
- 🔐 **管理员权限** – 管理全局维度、自动学习规则、他人标签、导入导出等。
- ⚙️ **可视化配置** – 所有参数均可在 AstrBot WebUI 设置面板中调整，无需修改代码。
- 💾 **数据持久化** – JSON 文件存储，支持自定义数据目录。

---

## 📦 安装

### 方法一：通过 AstrBot 插件市场（推荐）
1. 在 AstrBot WebUI 中打开「插件管理」。
2. 在插件市场搜索 `user_profile`，点击安装。
3. 重启 AstrBot 或重载插件。

### 方法二：手动克隆
```bash
cd /path/to/AstrBot/data/plugins
git clone https://github.com/你的用户名/astrbot_plugin_user_profile.git
# 重启 AstrBot 或重载插件
## 📋 指令速查

| 指令 | 说明 | 权限 |
|------|------|------|
| `/profile` | 查看自己的画像摘要 | 所有人 |
| `/profile @某人` | 查看指定用户的画像 | 管理员 |
| `/profile all` | 查看群内所有用户画像 | 管理员 |
| `/tag 分类=值` | 设置自己的标签 | 所有人 |
| `/tag 分类=值 @某人` | 为他人设置标签 | 管理员 |
| `/untag 分类` | 删除自己的某个分类 | 所有人 |
| `/addcat 分类名` | 添加全局维度 | 管理员 |
| `/delcat 分类名` | 删除全局维度 | 管理员 |
| `/listcat` | 列出全局维度 | 所有人 |
| `/addrules 正则 分类` | 添加学习规则 | 管理员 |
| `/delrule 分类` | 删除规则 | 管理员 |
| `/listrules` | 列出学习规则 | 所有人 |
| `/setlimit 参数 值` | 动态调整参数 | 管理员 |
| `/injectnow` | 强制注入画像 | 所有人 |
| `/admin add/remove/list` | 管理管理员 | 管理员 |
| `/export @某人` | 导出画像JSON | 管理员 |
| `/import <JSON>` | 导入画像JSON | 管理员 |
| `/profile_help` | 详细帮助 | 所有人 |
