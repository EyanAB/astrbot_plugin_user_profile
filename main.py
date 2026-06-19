import asyncio
import json
from pathlib import Path

from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star
from astrbot.api import logger, AstrBotConfig
from astrbot.api.provider import ProviderRequest
from astrbot.core.agent.message import TextPart
from astrbot.core.utils.astrbot_path import get_astrbot_data_path

from .storage import Storage
from .profile_manager import ProfileManager
from .rule_engine import RuleEngine
from .admin_manager import AdminManager
from .ai_optimizer import AIOptimizer
from .utils import extract_mention


class UserProfilePlugin(Star):
    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        self.config = config

        data_dir = self.config.get('data_dir', 'data/user_profiles')
        if not Path(data_dir).is_absolute():
            data_dir = str(Path(get_astrbot_data_path()) / data_dir)

        self.storage = Storage(data_dir)
        self.profile_manager = ProfileManager(self.storage, self.config)
        self.rule_engine = RuleEngine(self.storage)
        self.admin_manager = AdminManager(self.storage, self.config.get('initial_admins', []))
        self.ai_optimizer = AIOptimizer(self.profile_manager, self.admin_manager, self.config, context)

        # 初始化预设分类
        existing_cats = self.storage.read_global_categories()
        if not existing_cats:
            preset = self.config.get('preset_categories', [])
            if preset:
                self.storage.write_global_categories(preset)
                logger.info(f"已写入预设画像分类：{preset}")

        # 初始化预设规则（大幅扩展）
        if self.config.get('preset_rules_enabled', True):
            rules = self.storage.read_rules()
            if not rules:
                default_rules = [
                    # ---- 家乡 ----
                    {"pattern": r"老家(?:是|在|位于)?\s*(.+)", "category": "家乡"},
                    {"pattern": r"家(?:乡|是|在)?\s*(.+)", "category": "家乡"},
                    {"pattern": r"出生(?:在|于)?\s*(.+)", "category": "家乡"},
                    {"pattern": r"来自\s*(.+)", "category": "家乡"},
                    {"pattern": r"我(?:是|来自|老家在)\s*(.+)", "category": "家乡"},
                    # ---- 职业/身份 ----
                    {"pattern": r"我是(.+)工程师", "category": "职业"},
                    {"pattern": r"我是(.+)设计师", "category": "职业"},
                    {"pattern": r"我是(.+)老师", "category": "职业"},
                    {"pattern": r"我是(.+)医生", "category": "职业"},
                    {"pattern": r"我是(.+)律师", "category": "职业"},
                    {"pattern": r"我是(.+)经理", "category": "职业"},
                    {"pattern": r"我是(.+)总监", "category": "职业"},
                    {"pattern": r"我是(.+)开发", "category": "职业"},
                    {"pattern": r"我是(.+)运营", "category": "职业"},
                    {"pattern": r"我是(.+)产品", "category": "职业"},
                    {"pattern": r"我(?:是|做|干|从事)\s*(.+?)(?:的)?$", "category": "职业"},
                    {"pattern": r"职业(?:是|为)\s*(.+)", "category": "职业"},
                    {"pattern": r"岗位(?:是|为)\s*(.+)", "category": "职业"},
                    # ---- 爱好 ----
                    {"pattern": r"我(?:喜欢|爱|爱好|热衷|沉迷|痴迷)\s*(.+)", "category": "爱好"},
                    {"pattern": r"喜欢\s*(.+)", "category": "爱好"},
                    {"pattern": r"爱好(?:是|为)\s*(.+)", "category": "爱好"},
                    # ---- 年龄 ----
                    {"pattern": r"我(?:今年|现在|已经)\s*(\d+)\s*岁", "category": "年龄"},
                    {"pattern": r"年龄(?:是|为)\s*(\d+)\s*岁", "category": "年龄"},
                    {"pattern": r"(\d+)\s*岁", "category": "年龄"},
                    # ---- 专业 ----
                    {"pattern": r"专业(?:是|为|学)\s*(.+)", "category": "专业"},
                    {"pattern": r"我学(?:的是|习)\s*(.+)", "category": "专业"},
                    {"pattern": r"主修\s*(.+)", "category": "专业"},
                    # ---- 技能 ----
                    {"pattern": r"我(?:会|擅长|精通|掌握)\s*(.+)", "category": "技能"},
                    {"pattern": r"(?:会|擅长|精通)\s*(.+)", "category": "技能"},
                    # ---- 学校 ----
                    {"pattern": r"(?:毕业|就读|来自|在)\s*(.+?(?:大学|学院|中学|小学))", "category": "学校"},
                    # ---- 公司 ----
                    {"pattern": r"(?:工作|任职|在)\s*(.+?(?:公司|集团|科技|有限))", "category": "公司"},
                    # ---- 性格 ----
                    {"pattern": r"我(?:比较|性格|挺|很)\s*(.+?)(?:的)?$", "category": "性格"},
                    {"pattern": r"性格(?:是|为)\s*(.+)", "category": "性格"},
                ]
                for rule in default_rules:
                    self.rule_engine.add_rule(rule["pattern"], rule["category"])
                logger.info(f"已添加 {len(default_rules)} 条默认自动学习规则")

    # ========== 辅助方法 ==========
    def _get_user_id(self, event: AstrMessageEvent) -> str:
        return event.message_obj.sender.user_id

    def _get_group_id(self, event: AstrMessageEvent) -> str:
        return event.message_obj.group_id

    # ========== 自动学习 ==========
    @filter.regex(r'.*')
    async def auto_learn(self, event: AstrMessageEvent):
        if event.message_str.startswith('/'):
            return
        if not self.config.get('auto_learn_enabled', True):
            return

        user_id = self._get_user_id(event)
        group_id = self._get_group_id(event)
        text = event.message_str

        # 规则匹配（始终执行）
        matches = self.rule_engine.match(text)
        if matches:
            for category, value in matches:
                self.profile_manager.add_secondary(user_id, group_id, category, value)
                self.ai_optimizer.on_change(user_id, group_id)
            self.ai_optimizer.on_change(user_id, group_id)

        # AI 主动分析（可选）
        if self.config.get('enable_ai_optimize', False):
            asyncio.create_task(
                self.ai_optimizer.check_and_optimize(
                    user_id, group_id, text, event.unified_msg_origin
                )
            )

    # ========== 画像注入 ==========
    @filter.on_llm_request()
    async def inject_profile_before_llm(self, event: AstrMessageEvent, req: ProviderRequest):
        user_id = self._get_user_id(event)
        group_id = self._get_group_id(event)

        if not self.profile_manager.should_inject(user_id, group_id):
            return

        profile = self.profile_manager.get_compact_profile(user_id, group_id)
        if not profile:
            return

        req.extra_user_content_parts.append(
            TextPart(text=f"\n[用户画像] {profile}")
        )

        self.profile_manager.mark_injected(user_id, group_id)
        logger.info(f"已为用户 {user_id} 注入画像：{profile}")

    # ========== 指令处理 ==========
    @filter.command("profile")
    async def profile(self, event: AstrMessageEvent, args: str = ""):
        user_id = self._get_user_id(event)
        group_id = self._get_group_id(event)

        target_id = None
        if args:
            target_id = extract_mention(args)
            if target_id and not self.admin_manager.is_admin(user_id):
                yield event.plain_result("权限不足，仅管理员可查看他人画像")
                return
            if target_id:
                user_id = target_id

        profile = self.profile_manager.get_profile(user_id, group_id)
        categories = profile.get('categories', {})
        if not categories:
            yield event.plain_result("该用户画像为空。")
        else:
            lines = []
            for cat, data in categories.items():
                lines.append(f"【{cat}】主值: {data.get('primary', '无')}")
                sec = data.get('secondary', {})
                if sec:
                    sec_str = ", ".join([f"{v}({cnt})" for v, cnt in sec.items()])
                    lines.append(f"  备选: {sec_str}")
                backup = data.get('backup', [])
                if backup:
                    lines.append(f"  历史: {', '.join(backup)}")
            yield event.plain_result(f"用户画像详情：\n" + "\n".join(lines))

    @filter.command("profile all")
    async def profile_all(self, event: AstrMessageEvent):
        user_id = self._get_user_id(event)
        if not self.admin_manager.is_admin(user_id):
            yield event.plain_result("权限不足")
            return

        group_id = self._get_group_id(event)
        if not group_id:
            yield event.plain_result("私聊中无法查看群所有用户")
            return

        profile_dir = self.storage.data_dir / "profiles"
        if not profile_dir.exists():
            yield event.plain_result("暂无画像数据")
            return

        lines = []
        for file in profile_dir.glob(f"*_{group_id}.json"):
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                uid = data.get('user_id')
                compact = self.profile_manager.get_compact_profile(uid, group_id)
                if compact:
                    lines.append(f"{uid}: {compact}")
            except Exception:
                continue

        if lines:
            yield event.plain_result("群用户画像摘要：\n" + "\n".join(lines))
        else:
            yield event.plain_result("暂无画像")

    @filter.command("tag")
    async def tag(self, event: AstrMessageEvent, args: str):
        parts = args.split()
        if not parts:
            yield event.plain_result("格式：/tag 分类=值 [@某人]")
            return

        kv = parts[0]
        if '=' not in kv:
            yield event.plain_result("格式错误，请使用 分类=值")
            return

        category, value = kv.split('=', 1)
        category = category.strip()
        value = value.strip()

        if not category or not value:
            yield event.plain_result("分类和值不能为空")
            return

        if len(value) > self.config.get('value_max_len', 10):
            yield event.plain_result(f"值长度超过限制 {self.config.get('value_max_len')}")
            return

        user_id = self._get_user_id(event)
        group_id = self._get_group_id(event)
        target_user = user_id

        if len(parts) > 1:
            mention = extract_mention(' '.join(parts[1:]))
            if mention:
                if not self.admin_manager.is_admin(user_id):
                    yield event.plain_result("权限不足，只有管理员可设置他人标签")
                    return
                target_user = mention

        success = self.profile_manager.set_tag(target_user, group_id, category, value)
        if success:
            yield event.plain_result(f"已设置 {category} = {value}")
            if self.config.get('enable_ai_optimize', False):
                await self.ai_optimizer.check_and_optimize(
                    target_user, group_id, event.message_str, event.unified_msg_origin
                )
        else:
            yield event.plain_result("设置失败，请检查值长度或分类名称")

    @filter.command("untag")
    async def untag(self, event: AstrMessageEvent, category: str):
        if not category:
            yield event.plain_result("请指定分类名称")
            return
        user_id = self._get_user_id(event)
        group_id = self._get_group_id(event)
        self.profile_manager.delete_category(user_id, group_id, category)
        yield event.plain_result(f"已删除分类 {category}")

    @filter.command("addcat")
    async def addcat(self, event: AstrMessageEvent, category: str):
        user_id = self._get_user_id(event)
        if not self.admin_manager.is_admin(user_id):
            yield event.plain_result("权限不足")
            return
        if not category:
            yield event.plain_result("请指定分类名称")
            return

        cats = self.storage.read_global_categories()
        if category in cats:
            yield event.plain_result(f"分类 {category} 已存在")
            return

        cats.append(category)
        self.storage.write_global_categories(cats)
        yield event.plain_result(f"已添加全局维度 {category}")

    @filter.command("delcat")
    async def delcat(self, event: AstrMessageEvent, category: str):
        user_id = self._get_user_id(event)
        if not self.admin_manager.is_admin(user_id):
            yield event.plain_result("权限不足")
            return
        if not category:
            yield event.plain_result("请指定分类名称")
            return

        cats = self.storage.read_global_categories()
        if category not in cats:
            yield event.plain_result(f"分类 {category} 不存在")
            return

        cats.remove(category)
        self.storage.write_global_categories(cats)
        yield event.plain_result(f"已删除全局维度 {category}（已有用户数据不会自动清除）")

    @filter.command("listcat")
    async def listcat(self, event: AstrMessageEvent):
        cats = self.storage.read_global_categories()
        if cats:
            yield event.plain_result("全局维度：\n" + "\n".join(cats))
        else:
            yield event.plain_result("暂无全局维度")

    @filter.command("addrules")
    async def addrules(self, event: AstrMessageEvent, pattern: str, category: str):
        user_id = self._get_user_id(event)
        if not self.admin_manager.is_admin(user_id):
            yield event.plain_result("权限不足")
            return
        if not pattern or not category:
            yield event.plain_result("格式：/addrules 正则 分类")
            return

        self.rule_engine.add_rule(pattern, category)
        yield event.plain_result(f"已添加规则：{pattern} -> {category}")

    @filter.command("delrule")
    async def delrule(self, event: AstrMessageEvent, category: str):
        user_id = self._get_user_id(event)
        if not self.admin_manager.is_admin(user_id):
            yield event.plain_result("权限不足")
            return
        if not category:
            yield event.plain_result("请指定分类")
            return

        self.rule_engine.delete_rules_by_category(category)
        yield event.plain_result(f"已删除分类 {category} 的所有规则")

    @filter.command("listrules")
    async def listrules(self, event: AstrMessageEvent):
        rules = self.storage.read_rules()
        if rules:
            lines = [f"{r['category']}: {r['pattern']}" for r in rules]
            yield event.plain_result("自动学习规则：\n" + "\n".join(lines))
        else:
            yield event.plain_result("暂无规则")

    @filter.command("setlimit")
    async def setlimit(self, event: AstrMessageEvent, param: str, value: str):
        user_id = self._get_user_id(event)
        if not self.admin_manager.is_admin(user_id):
            yield event.plain_result("权限不足")
            return

        allowed = ['max_tags', 'freq_upgrade_ratio', 'inject_cooldown', 'ai_optimize_cooldown']
        if param not in allowed:
            yield event.plain_result(f"参数 {param} 不可动态调整")
            return

        try:
            if param in ['max_tags', 'inject_cooldown', 'ai_optimize_cooldown']:
                val = int(value)
            else:
                val = float(value)
        except ValueError:
            yield event.plain_result("值类型错误")
            return

        self.config[param] = val
        self.profile_manager.config[param] = val
        yield event.plain_result(f"已设置 {param} = {val}")

    @filter.command("injectnow")
    async def injectnow(self, event: AstrMessageEvent):
        user_id = self._get_user_id(event)
        group_id = self._get_group_id(event)
        self.profile_manager._last_inject[(user_id, group_id)] = 0
        yield event.plain_result("已强制刷新，下次对话将注入最新画像")

    @filter.command("admin")
    async def admin_cmd(self, event: AstrMessageEvent, op: str, target: str = ""):
        user_id = self._get_user_id(event)
        if not self.admin_manager.is_admin(user_id):
            yield event.plain_result("权限不足")
            return

        if op == "list":
            admins = self.admin_manager.get_admins()
            yield event.plain_result(f"管理员列表：{', '.join(admins) if admins else '无'}")
        elif op == "add":
            if not target:
                yield event.plain_result("请指定用户ID")
                return
            if self.admin_manager.add_admin(target):
                yield event.plain_result(f"已添加 {target} 为管理员")
            else:
                yield event.plain_result(f"{target} 已经是管理员")
        elif op == "remove":
            if not target:
                yield event.plain_result("请指定用户ID")
                return
            if self.admin_manager.remove_admin(target):
                yield event.plain_result(f"已移除 {target} 的管理员权限")
            else:
                yield event.plain_result(f"{target} 不是管理员")
        else:
            yield event.plain_result("未知操作，可用: add, remove, list")

    @filter.command("export")
    async def export_cmd(self, event: AstrMessageEvent, target: str):
        user_id = self._get_user_id(event)
        if not self.admin_manager.is_admin(user_id):
            yield event.plain_result("权限不足")
            return

        target_id = extract_mention(target)
        if not target_id:
            yield event.plain_result("请 @ 一个用户")
            return

        group_id = self._get_group_id(event)
        profile = self.profile_manager.get_profile(target_id, group_id)
        yield event.plain_result(f"画像数据：\n```json\n{json.dumps(profile, ensure_ascii=False, indent=2)}\n```")

    @filter.command("import")
    async def import_cmd(self, event: AstrMessageEvent, json_data: str):
        user_id = self._get_user_id(event)
        if not self.admin_manager.is_admin(user_id):
            yield event.plain_result("权限不足")
            return

        try:
            data = json.loads(json_data)
            uid = data.get('user_id')
            gid = data.get('group_id')
            if not uid:
                yield event.plain_result("无效JSON，缺少 user_id")
                return
            self.storage.write_profile(uid, gid, data)
            yield event.plain_result(f"已导入用户 {uid} 的画像")
        except Exception as e:
            yield event.plain_result(f"导入失败：{str(e)}")

    @filter.command("profile_help")
    async def profile_help(self, event: AstrMessageEvent):
        help_text = """
用户画像插件帮助：
/profile             查看自己当前会话画像摘要（/profile @某人 可查看他人）
/profile all         查看当前群所有用户画像摘要（管理员）
/tag 分类=值 [@某人] 设置标签（管理员可设他人）
/untag 分类          删除自己的某个分类
/addcat 分类名       添加全局画像维度（管理员）
/delcat 分类名       删除全局维度（管理员）
/listcat             列出所有画像维度
/addrules 正则 分类  添加自动学习规则（管理员）
/delrule 分类        删除该标签的所有规则（管理员）
/listrules           列出所有自动学习规则
/setlimit 参数 值    动态调整参数（管理员）
/injectnow           强制下次对话更新画像注入
/admin add/remove/list  管理员管理
/export @某人        导出画像JSON（管理员）
/import <JSON>       导入画像JSON（管理员）
/profile_help        查看本帮助
        """
        yield event.plain_result(help_text)

    # ========== 对外接口 ==========
    def should_inject(self, user_id: str, group_id: str) -> bool:
        return self.profile_manager.should_inject(user_id, group_id)

    def get_profile_compact(self, user_id: str, group_id: str) -> str:
        return self.profile_manager.get_compact_profile(user_id, group_id)

    def mark_injected(self, user_id: str, group_id: str) -> None:
        self.profile_manager.mark_injected(user_id, group_id)

    async def terminate(self):
        logger.info("用户画像插件已卸载")