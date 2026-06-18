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
    
    async def check_and_optimize(self, user_id: str, group_id: Optional[str], message_text: str = ""):
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
        
        profile = self.pm.get_profile(user_id, group_id)
        compact = self.pm.get_compact_profile(user_id, group_id)
        prompt_template = self.config.get('ai_optimize_prompt', 
                                          "请根据用户画像和最近对话，提出优化建议，并以 JSON 格式返回：{\"category\": \"分类\", \"suggest\": \"建议值\", \"confidence\": 0.8}")
        prompt = f"{prompt_template}\n\n当前用户画像：{compact}\n最新消息：{message_text}"
        
        try:
            suggestion = await self._call_ai(prompt)
            if suggestion:
                await self._apply_suggestion(user_id, group_id, suggestion)
        except Exception as e:
            logger.error(f"AI 优化失败: {e}")
    
    async def _call_ai(self, prompt: str) -> Optional[dict]:
        ai = self.context.bot.ai
        if ai:
            try:
                response = await ai.chat_completion([{"role": "user", "content": prompt}])
                content = response['choices'][0]['message']['content']
            except:
                content = None
        else:
            api_key = self.config.get('openai_api_key')
            base_url = self.config.get('openai_base_url', 'https://api.openai.com/v1')
            model = self.config.get('openai_model', 'gpt-3.5-turbo')
            if not api_key:
                return None
            import aiohttp
            async with aiohttp.ClientSession() as session:
                url = f"{base_url}/chat/completions"
                headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
                data = {
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.3,
                }
                async with session.post(url, json=data, headers=headers) as resp:
                    if resp.status != 200:
                        logger.error(f"OpenAI API error: {await resp.text()}")
                        return None
                    result = await resp.json()
                    content = result['choices'][0]['message']['content']
        
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
        notify_admins = True
        
        if mode == 'notify':
            await self._notify_admins(f"AI 建议更新用户 {user_id} 的 {category} 为 '{suggest}' (置信度: {confidence})", admins)
        elif mode == 'semi_auto':
            min_conf = self.config.get('ai_min_confidence', 0.7)
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
