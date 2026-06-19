import time
import json
from typing import Optional
from astrbot.api import logger
from .profile_manager import ProfileManager
from .admin_manager import AdminManager

class AIOptimizer:
    def __init__(self, profile_manager: ProfileManager, admin_manager: AdminManager, config: dict, context):
        self.pm = profile_manager
        self.admin = admin_manager
        self.config = config
        self.context = context
        self._last_optimize = {}
        self._change_count = {}

    def on_change(self, user_id: str, group_id: Optional[str]):
        key = (user_id, group_id)
        self._change_count[key] = self._change_count.get(key, 0) + 1

    async def check_and_optimize(self, user_id: str, group_id: Optional[str], message_text: str = "", umo=None):
        if not self.config.get('enable_ai_optimize', False):
            return
        key = (user_id, group_id)
        now = time.time()
        cooldown = self.config.get('ai_optimize_cooldown', 3600)
        min_changes = self.config.get('ai_optimize_min_changes', 3)

        last = self._last_optimize.get(key, 0)
        if now - last < cooldown:
            if self._change_count.get(key, 0) < min_changes:
                return

        self._last_optimize[key] = now
        self._change_count[key] = 0

        compact = self.pm.get_compact_profile(user_id, group_id)
        prompt_template = self.config.get('ai_optimize_prompt',
                                          "请根据用户画像和最近对话，提取用户的核心属性信息（如家乡、职业、爱好、技能、年龄等），并以 JSON 格式返回。要求：- \"category\" 必须是简洁的分类名（如 \"家乡\"、\"职业\"、\"爱好\"），优先使用已有分类。- \"suggest\" 必须是简短的值（如 \"吉林\"、\"视觉设计师\"、\"篮球\"），不要包含额外解释或建议。- 如果信息不明确或置信度低于0.6，则返回空。输出格式：{\"category\": \"分类\", \"suggest\": \"值\", \"confidence\": 0.9}")
        prompt = f"{prompt_template}\n\n当前用户画像：{compact}\n最新消息：{message_text}"

        try:
            suggestion = await self._call_ai(prompt, umo)
            if suggestion:
                await self._apply_suggestion(user_id, group_id, suggestion)
        except Exception as e:
            logger.error(f"AI 优化失败: {e}")

    async def _call_ai(self, prompt: str, umo=None) -> Optional[dict]:
        try:
            provider_id = await self.context.get_current_chat_provider_id(umo=umo)
            if not provider_id:
                logger.warning("AI优化：没有可用的聊天模型，跳过")
                return None

            llm_resp = await self.context.llm_generate(
                chat_provider_id=provider_id,
                prompt=prompt,
                temperature=0.3
            )
            content = llm_resp.completion_text
        except Exception as e:
            logger.error(f"AI优化调用失败: {e}")
            return None

        if not content:
            return None
        try:
            start = content.find('{')
            end = content.rfind('}') + 1
            if start == -1 or end == -1:
                return None
            json_str = content[start:end]
            return json.loads(json_str)
        except:
            return None

    async def _apply_suggestion(self, user_id: str, group_id: Optional[str], suggestion: dict):
        category = suggestion.get('category')
        suggest = suggestion.get('suggest')
        confidence = suggestion.get('confidence', 0.0)
        mode = self.config.get('ai_optimize_mode', 'notify')

        if not category or not suggest:
            return

        admins = self.admin.get_admins()

        if mode == 'notify':
            await self._notify_admins(f"AI 建议更新用户 {user_id} 的 {category} 为 '{suggest}' (置信度: {confidence})", admins)
        elif mode == 'semi_auto':
            min_conf = self.config.get('ai_min_confidence', 0.6)
            if confidence >= min_conf:
                self.pm.set_tag(user_id, group_id, category, suggest)
                await self._notify_admins(f"AI 优化已自动应用：用户 {user_id} 的 {category} 更新为 '{suggest}'", admins)
            else:
                await self._notify_admins(f"AI 建议更新用户 {user_id} 的 {category} 为 '{suggest}'，但置信度 {confidence} 低于阈值，请手动处理。", admins)
        elif mode == 'auto':
            self.pm.set_tag(user_id, group_id, category, suggest)
            await self._notify_admins(f"AI 优化已自动应用（自动模式）：用户 {user_id} 的 {category} 更新为 '{suggest}'", admins)

    async def _notify_admins(self, msg: str, admins: list):
        logger.info(f"[AI优化通知] {msg}")