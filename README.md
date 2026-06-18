🧠 AstrBot 用户画像插件
https://img.shields.io/badge/AstrBot-Plugin-blue
https://img.shields.io/badge/Python-3.10+-green
https://img.shields.io/badge/License-MIT-yellow

为 AstrBot 提供长期记忆的用户画像系统。支持群聊/私聊隔离、自动学习、AI 优化、LLM 上下文注入等功能，让您的 AI 助手更懂用户。

✨ 特性
📌 多维度画像 – 支持自定义分类（职业、爱好、性格等），每个分类包含主值、备选（带频率）和历史值。

🧠 自动学习 – 通过正则规则从对话中自动提取标签值，并动态升级主值。

💉 LLM 上下文注入 – 在每次 AI 对话前自动注入精简画像（受冷却控制），提升回答准确性。

🤖 AI 画像优化 – 可调用 LLM 分析画像并提出优化建议（支持通知/半自动/全自动模式）。

👥 群聊/私聊隔离 – 同一用户在不同群组或私聊中的画像相互独立。

🔐 管理员权限 – 管理全局维度、自动学习规则、他人标签、导入导出等。

⚙️ 可视化配置 – 所有参数均可在 AstrBot WebUI 设置面板中调整，无需修改代码。

💾 数据持久化 – JSON 文件存储，支持自定义数据目录。

📦 安装
方法一：通过 AstrBot 插件市场（推荐）
在 AstrBot WebUI 中打开「插件管理」。

在插件市场搜索 user_profile，点击安装。

重启 AstrBot 或重载插件。

方法二：手动克隆
bash
cd /path/to/AstrBot/data/plugins
git clone https://github.com/你的用户名/astrbot_plugin_user_profile.git
# 重启 AstrBot 或重载插件
方法三：下载 ZIP 包
从 GitHub Releases 下载最新版 ZIP，解压到 data/plugins 目录，重命名为 astrbot_plugin_user_profile。

⚙️ 配置（设置面板）
在 AstrBot WebUI 的「插件设置」中找到 用户画像，所有配置项均可实时调整：

配置项	类型	默认值	说明
prefix	string	""	指令前缀（避免冲突，例如 up_）
max_tags	int	8	每人每场景最大分类数
value_max_len	int	10	标签值最大字符长度
inject_cooldown	int	600	画像注入冷却时间（秒）
freq_upgrade_ratio	float	1.5	备选升级为主值的频率倍数阈值
data_dir	string	data/user_profiles	数据存储目录（可改为绝对路径）
auto_learn_enabled	bool	true	是否启用自动学习
enable_ai_optimize	bool	false	是否启用 AI 优化
ai_optimize_mode	string	notify	优化模式：notify / semi_auto / auto
ai_optimize_prompt	text	(自定义)	AI 优化提示词模板
ai_min_confidence	float	0.7	半自动模式最低置信度
ai_optimize_cooldown	int	3600	AI 优化冷却时间（秒）
ai_optimize_min_changes	int	3	冷却期内触发优化所需的最小变更次数
initial_admins	list	[]	初始管理员 ID 列表
openai_api_key	string	""	（备用）OpenAI API Key
openai_base_url	string	""	（备用）自定义 API 地址
openai_model	string	gpt-3.5-turbo	（备用）使用的模型
重要：修改 data_dir 后必须重启 AstrBot 才能生效（路径在插件加载时确定）。

📟 指令快速参考
所有指令均支持通过设置面板配置 prefix 前缀（例如 /up_profile）。

指令	权限	说明
/profile	所有人	查看自己当前会话画像摘要（含主值与备选数量）
/profile @某人	管理员	查看指定用户的画像详情（支持 @提及）
/profile all	管理员	查看当前群组所有用户的画像摘要
/tag 分类=值 [@某人]	所有人/管理员	设置标签（管理员可代他人设置）
/untag 分类	所有人	删除自己的某个分类及其所有备选项
/addcat 分类名	管理员	添加一个全局画像维度
/delcat 分类名	管理员	删除全局维度（已存用户数据不会自动清除）
/listcat	所有人	列出所有全局维度
/addrules 正则 分类	管理员	添加自动学习规则（正则表达式）
/delrule 分类	管理员	删除该分类下的所有规则
/listrules	所有人	列出所有自动学习规则
/setlimit 参数 值	管理员	动态调整 max_tags、freq_upgrade_ratio 等参数
/injectnow	所有人	重置冷却，强制下次对话注入最新画像
/admin add/remove/list	管理员	管理管理员列表
/export @某人	管理员	导出用户画像 JSON
/import <JSON>	管理员	导入用户画像 JSON（覆盖写入）
/profile_help	所有人	显示本帮助信息
📖 详细指令使用说明
🔹 通用指令（所有用户）
/profile – 查看自己的画像摘要
格式：/profile

输出示例：

text
您的画像摘要：
职业: 后端工程师 (备选2个)
爱好: 篮球 (备选1个)
注意：若画像为空，会提示“您的画像为空”。

/profile @某人 – 查看他人画像（管理员）
格式：/profile @用户

权限：管理员

输出示例：

text
用户 123456 画像详情：
【职业】主值: 全栈工程师
  备选: 后端工程师(3), 前端(1)
  历史: 运维
/profile all – 查看群内所有用户画像（管理员）
格式：/profile all

权限：管理员

说明：列出当前群组所有有画像的用户及其精简画像。

仅限群聊，私聊不可用。

/tag 分类=值 [@某人] – 设置标签
格式：/tag 分类=值 或 /tag 分类=值 @某人

权限：普通用户设自己；管理员可设他人。

说明：若分类不存在则创建，旧主值自动移至备选并累加频率。

限制：值长度受 value_max_len 限制（默认10字符）。

/untag 分类 – 删除自己的某个分类
格式：/untag 分类

说明：彻底移除该分类及其所有备选/历史值。

/listcat – 列出全局维度
输出示例：职业\n爱好\n技能

/listrules – 列出学习规则
输出示例：职业: 我是(.+)工程师

/injectnow – 强制刷新注入
说明：重置冷却，使下一条对话强制注入画像。

/profile_help – 显示详细帮助
说明：显示完整的指令列表及简要说明。

🔹 管理员专用指令
/admin add/remove/list – 管理管理员列表
示例：/admin add 123456，/admin list

/addcat 分类名 – 添加全局维度
示例：/addcat 技能

/delcat 分类名 – 删除全局维度
注意：已有用户数据不会自动清除。

/addrules 正则 分类 – 添加自动学习规则
示例：/addrules 我是(.+)工程师 职业

说明：正则支持 Python re 语法，建议使用捕获组 (…) 精准提取值。

/delrule 分类 – 删除某分类所有规则
示例：/delrule 职业

/setlimit 参数 值 – 动态调整参数
可调参数：max_tags、freq_upgrade_ratio、inject_cooldown、ai_optimize_cooldown

示例：/setlimit max_tags 12

/export @某人 – 导出用户画像 JSON
输出：格式化 JSON 代码块。

/import <JSON> – 导入用户画像 JSON
警告：覆盖写入，建议先导出备份。

🧩 使用示例
1. 管理员初始化
text
/admin add 12345678
/addcat 职业
/addcat 爱好
/addrules 我是(.+)工程师 职业
/addrules 我喜欢(.+) 爱好
2. 用户自动学习
用户说：“我是后端工程师” → 插件匹配规则，将“后端工程师”加入 职业 备选，频率 +1。

多次提及达到主值频率 1.5 倍 → 自动升级为主值。

3. 手动设置标签
text
/tag 职业=全栈工程师
/tag 爱好=篮球 @张三    # 管理员操作
4. 查看画像
text
/profile
/profile @张三
/profile all
5. AI 对话注入
用户发送非命令消息（如“推荐几本技术书籍”），插件在 LLM 请求前注入画像（如 职业:后端工程师；爱好:篮球），LLM 据此提供个性化推荐。

🔌 与其他插件集成
其他 AI 对话插件可通过以下公开方法获取画像数据，实现按需注入：

python
# 获取插件实例
pp = bot.plugins.get("astrbot_plugin_user_profile")
if pp and pp.should_inject(user_id, group_id):
    compact = pp.get_profile_compact(user_id, group_id)
    if compact:
        # 将画像追加到系统提示词或用户消息中
        system_prompt += f"\n[用户画像] {compact}"
    pp.mark_injected(user_id, group_id)
📁 数据存储结构
所有数据保存在 data_dir（默认 data/user_profiles）：

text
data/user_profiles/
├── profiles/
│   ├── private_{user_id}.json       # 私聊画像
│   └── {user_id}_{group_id}.json    # 群聊画像
├── global_categories.json           # 全局维度列表
├── rules.json                       # 自动学习规则
└── admins.json                      # 管理员 ID 列表
画像 JSON 结构示例：

json
{
  "user_id": "123456",
  "group_id": "789012",
  "last_update": 1700000000,
  "categories": {
    "职业": {
      "primary": "后端工程师",
      "secondary": {
        "全栈工程师": 3,
        "架构师": 1
      },
      "backup": ["前端"]
    }
  }
}
🛠️ 开发与调试
重载插件：在 AstrBot WebUI 的插件管理中点击「重载」即可快速测试代码修改。

日志查看：插件会输出详细的注入、学习、优化日志，便于排查问题。

单元测试：建议针对 ProfileManager 和 RuleEngine 编写测试用例（暂无内置）。

🤝 贡献
欢迎 Issue 和 PR！请确保：

代码符合 PEP8 规范，并使用 ruff 格式化。

新功能包含必要的注释和文档。

尽量保持向后兼容。

📄 许可证
本项目采用 MIT License。

🙏 致谢
AstrBot – 强大的多平台聊天机器人框架。

所有贡献者与用户的支持！

祝您使用愉快！ 🚀