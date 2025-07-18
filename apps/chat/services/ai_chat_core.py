import openai
import time
from typing import List, Dict, Optional
from django.conf import settings
# from apps.aipersona.models import AIPersona


class AIChatCore:
    """Enhanced AI service with persona support"""

    pass

#     def __init__(self, model: str = "gpt-3.5-turbo", temperature: float = 0.7):
#         self.client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
#         self.model = model
#         self.temperature = temperature
#         self.max_tokens = 1000

#     def generate_response(
#         self,
#         conversation_history: List[Dict],
#         user,  # Django User instance
#         # persona: AIPersona = None,
#         session_context: Dict = None,
#     ) -> Dict:
#         """Generate AI response using persona and user context"""

#         start_time = time.time()

#         try:
#             # Build system prompt based on persona
#             system_prompt = self._build_persona_system_prompt(persona, user)

#             # Prepare messages
#             messages = [{"role": "system", "content": system_prompt}]
#             messages.extend(conversation_history)

#             # Adjust temperature based on persona risk aversion
#             temperature = self._get_persona_temperature(persona)

#             response = self.client.chat.completions.create(
#                 model=self.model,
#                 messages=messages,
#                 temperature=temperature,
#                 max_tokens=self.max_tokens,
#             )

#             response_time = time.time() - start_time

#             # Collect user context for future conversations
#             user_context_data = self._collect_user_context(user, persona)

#             return {
#                 "content": response.choices[0].message.content,
#                 "tokens_used": response.usage.total_tokens,
#                 "response_time": response_time,
#                 "model_used": self.model,
#                 "user_context": user_context_data,
#                 "persona_id": persona.id if persona else None,
#                 "success": True,
#             }

#         except Exception as e:
#             return {
#                 "content": "I'm sorry, I'm having trouble responding right now. Please try again.",
#                 "tokens_used": 0,
#                 "response_time": time.time() - start_time,
#                 "model_used": self.model,
#                 "success": False,
#                 "error": str(e),
#             }
#     def _build_persona_system_prompt(self, persona: AIPersona, user) -> str:
#         """Build system prompt based on persona characteristics"""
        
#         if not persona:
#             return "You are a helpful HR assistant. Provide professional and accurate HR guidance."
        
#         # Simple, direct persona prompt
#         prompt = f"""You are {persona.name}, {persona.title}.

#     When someone asks your name, simply say "I'm {persona.name}" or "My name is {persona.name}".

#     Your details:
#     - Name: {persona.name}
#     - Title: {persona.title}
#     - Personality: {persona.personality or 'Professional and helpful'}

#     Your approach: {persona.approach or 'Provide clear, actionable guidance'}

#     Risk level: {persona.risk_aversion or 'medium'}
#     """

#         # Add legal constraints if they exist
#         if persona.legal_constraints.exists():
#             prompt += "\nLegal constraints:\n"
#             for constraint in persona.legal_constraints.filter(is_active=True):
#                 prompt += f"- {constraint.description}\n"

#         # Add custom system prompt if available
#         if persona.system_prompt:
#             prompt += f"\nAdditional instructions:\n{persona.system_prompt}\n"

#         prompt += f"\nAlways respond as {persona.name}. Stay in character."
        
#         return prompt

#     def _get_persona_temperature(self, persona: AIPersona) -> float:
#         """Adjust temperature based on persona risk aversion"""
#         if not persona or not persona.risk_aversion:
#             return self.temperature
        
#         # More conservative (lower temperature) for high risk aversion
#         risk_temp_map = {
#             'low': 0.9,      # More creative/flexible
#             'medium': 0.7,   # Balanced
#             'high': 0.5      # More conservative/consistent
#         }
        
#         return risk_temp_map.get(persona.risk_aversion, self.temperature)

#     def _collect_user_context(self, user, persona: AIPersona) -> Dict:
#         """Collect user context for session management"""
#         context = {
#             'user_id': user.id,
#             'username': user.username,
#             'persona_id': persona.id if persona else None,
#             'timestamp': time.time()
#         }
        
#         # Add user profile info if available
#         if hasattr(user, 'profile'):
#             profile = user.profile
#             context.update({
#                 'organization': getattr(profile, 'organization', None),
#                 'role': getattr(profile, 'role', None),
#                 'industry': getattr(profile, 'industry', None),
#             })
        
#         return context


# class PersonaContextBuilder:
#     """Helper class to build context-aware prompts"""
    
#     def __init__(self, persona: AIPersona, user):
#         self.persona = persona
#         self.user = user
    
#     def build_specialized_prompt(self, task_type: str) -> str:
#         """Build task-specific prompts based on persona expertise"""
        
#         base_prompt = f"As {self.persona.name}, a {self.persona.title}, "
        
#         task_prompts = {
#             'compliance': f"{base_prompt}provide compliance guidance while adhering to all legal constraints.",
#             'strategy': f"{base_prompt}help develop strategic HR initiatives aligned with business goals.",
#             'recruitment': f"{base_prompt}assist with talent acquisition and recruitment strategies.",
#             'compensation': f"{base_prompt}provide compensation and benefits guidance.",
#             'development': f"{base_prompt}help with learning and development initiatives.",
#             'general': f"{base_prompt}provide comprehensive HR support."
#         }
        
#         return task_prompts.get(task_type, task_prompts['general'])
    
#     def get_persona_news_categories(self) -> List[str]:
#         """Get news categories relevant to this persona"""
#         if not self.persona.news_categories.exists():
#             return []
        
#         return [
#             category.category.name 
#             for category in self.persona.news_categories.filter(is_primary=True)
#         ]