import openai
import time
import re
from typing import List, Dict, Optional
from django.conf import settings


class AIChatCore:
    """Bible-focused AI service with spiritual context awareness"""

    def __init__(self, model: str = "gpt-3.5-turbo", temperature: float = 0.7):
        self.client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = model
        self.temperature = temperature
        self.max_tokens = 1000

    def generate_bible_response(
        self,
        conversation_history: List[Dict],
        user,  # Django User instance
        user_context: Dict = None,
    ) -> Dict:
        """Generate Bible-focused AI response using spiritual context"""

        start_time = time.time()

        try:
            # Build Bible-focused system prompt
            system_prompt = self._build_bible_system_prompt(user_context)

            # Prepare messages for AI
            messages = [{"role": "system", "content": system_prompt}]
            messages.extend(conversation_history)

            # Adjust temperature based on user's tone preference
            temperature = self._get_contextual_temperature(user_context)

            # Generate response
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=self.max_tokens,
            )

            response_time = time.time() - start_time
            content = response.choices[0].message.content

            # Extract Bible references from response
            bible_references = self._extract_bible_references(content)

            # Build conversation context for future reference
            conversation_context = self._build_conversation_context(
                user_context, content, bible_references
            )

            return {
                "content": content,
                "tokens_used": response.usage.total_tokens,
                "response_time": response_time,
                "model_used": self.model,
                "bible_references": bible_references,
                "conversation_context": conversation_context,
                "success": True,
            }

        except Exception as e:
            return {
                "content": "I apologize, but I'm having trouble responding right now. Please try again, and I'll do my best to help you with your Bible study.",
                "tokens_used": 0,
                "response_time": time.time() - start_time,
                "model_used": self.model,
                "bible_references": [],
                "success": False,
                "error": str(e),
            }

    def _build_bible_system_prompt(self, user_context: Dict) -> str:
        """Build Bible-focused system prompt based on user's spiritual context"""
        
        # Base Bible assistant prompt
        base_prompt = """You are a knowledgeable and compassionate Bible study assistant. Your role is to help users understand Scripture, grow in their faith, and apply biblical wisdom to their lives.

Core Guidelines:
- Always be respectful of different Christian denominations and interpretations
- Provide accurate biblical information and context
- Use appropriate biblical references to support your responses
- Be encouraging and supportive in your tone
- When discussing complex theological topics, present multiple perspectives when appropriate
- Always point users toward Scripture and prayer
- Be humble about limitations and encourage users to seek pastoral guidance for deep personal matters"""

        if not user_context:
            return base_prompt

        # Customize based on user's spiritual journey
        journey_reason = user_context.get('journey_reason', '')
        if journey_reason:
            base_prompt += f"\n\nUser's Journey: This person is exploring faith because: {journey_reason}. Be especially sensitive to their spiritual journey and meet them where they are."

        # Denomination awareness
        denomination = user_context.get('denomination', '')
        if denomination:
            base_prompt += f"\n\nDenominational Background: The user identifies with {denomination}. Be respectful of this tradition while providing biblically grounded responses."

        # Faith goals
        faith_goal = user_context.get('faith_goal', '')
        if faith_goal:
            base_prompt += f"\n\nFaith Goal: They want to {faith_goal}. Help them work toward this spiritual goal through Scripture."

        # Tone preference
        tone_preference = user_context.get('tone_preference', {})
        if tone_preference:
            tone_name = tone_preference.get('name', '')
            tone_description = tone_preference.get('description', '')
            if tone_name and tone_description:
                base_prompt += f"\n\nTone Preference: Use a {tone_name} tone - {tone_description}. Adjust your communication style accordingly."

        # Bible familiarity
        bible_familiarity = user_context.get('bible_familiarity', {})
        if bible_familiarity:
            familiarity_level = bible_familiarity.get('label', '')
            if familiarity_level:
                base_prompt += f"\n\nBible Knowledge Level: {familiarity_level}. Adjust your explanations and references to match their current understanding."

        # Bible version preference
        bible_version = user_context.get('bible_version', {})
        if bible_version:
            version_title = bible_version.get('title', '')
            if version_title:
                base_prompt += f"\n\nPreferred Bible Version: When quoting Scripture, use {version_title} when possible."

        # Final instructions
        base_prompt += "\n\nRemember to be authentic, caring, and Christ-centered in all your responses. Your goal is to help this person grow closer to God through understanding His Word."

        return base_prompt

    def _get_contextual_temperature(self, user_context: Dict) -> float:
        """Adjust AI temperature based on user's spiritual context"""
        if not user_context:
            return self.temperature

        # More conservative for serious theological discussions
        tone_preference = user_context.get('tone_preference', {})
        tone_name = tone_preference.get('name', '').lower()
        
        # Adjust based on tone preference
        if 'scholarly' in tone_name or 'formal' in tone_name:
            return 0.5  # More conservative and consistent
        elif 'casual' in tone_name or 'friendly' in tone_name:
            return 0.8  # More creative and conversational
        
        return self.temperature

    def _extract_bible_references(self, content: str) -> List[Dict]:
        """Extract Bible references from AI response"""
        # Common Bible reference patterns
        patterns = [
            r'\b\d*\s*([A-Z][a-z]+\.?)\s+(\d+):(\d+(?:-\d+)?)\b',  # John 3:16 or 1 John 3:16
            r'\b([A-Z][a-z]+\.?)\s+(\d+):(\d+(?:-\d+)?)\b',        # John 3:16
            r'\b\d*\s*([A-Z][a-z]+\.?)\s+(\d+)\b',                 # John 3 (whole chapter)
        ]
        
        references = []
        
        for pattern in patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                if len(match) == 3:  # Book, Chapter, Verse
                    book, chapter, verse = match
                    references.append({
                        "book": book,
                        "chapter": int(chapter),
                        "verse": verse,
                        "reference": f"{book} {chapter}:{verse}"
                    })
                elif len(match) == 2:  # Book, Chapter (whole chapter)
                    book, chapter = match
                    references.append({
                        "book": book,
                        "chapter": int(chapter),
                        "verse": None,
                        "reference": f"{book} {chapter}"
                    })
        
        # Remove duplicates
        unique_references = []
        seen = set()
        for ref in references:
            ref_key = (ref['book'], ref['chapter'], ref['verse'])
            if ref_key not in seen:
                seen.add(ref_key)
                unique_references.append(ref)
        
        return unique_references

    def _build_conversation_context(
        self, user_context: Dict, ai_response: str, bible_references: List[Dict]
    ) -> Dict:
        """Build context for future conversations"""
        
        context = {
            'timestamp': time.time(),
            'response_length': len(ai_response),
            'bible_references_count': len(bible_references),
            'topics_discussed': [],  # Could be enhanced with NLP
        }
        
        # Add Bible books mentioned
        if bible_references:
            context['bible_books_mentioned'] = list(set([ref['book'] for ref in bible_references]))
        
        # Extract potential themes/topics from the response
        context['potential_themes'] = self._extract_themes(ai_response)
        
        # Add user's spiritual state context
        if user_context:
            context['user_spiritual_state'] = {
                'journey_reason': user_context.get('journey_reason', ''),
                'faith_goal': user_context.get('faith_goal', ''),
                'bible_familiarity': user_context.get('bible_familiarity', {}).get('label', ''),
                'denomination': user_context.get('denomination', ''),
            }
        
        # Add response quality metrics
        context['response_metrics'] = {
            'has_bible_references': len(bible_references) > 0,
            'reference_density': len(bible_references) / max(len(ai_response.split()), 1),
            'estimated_reading_time': len(ai_response.split()) / 200,  # words per minute
        }
        
        return context

    def _extract_themes(self, content: str) -> List[str]:
        """Extract potential biblical themes from response content"""
        # Common biblical themes/topics
        themes = [
            'faith', 'love', 'hope', 'forgiveness', 'salvation', 'grace', 'mercy',
            'prayer', 'worship', 'discipleship', 'fellowship', 'ministry', 'service',
            'scripture', 'bible study', 'theology', 'doctrine', 'prophecy', 'mission',
            'evangelism', 'baptism', 'communion', 'church', 'christian living',
            'spiritual growth', 'temptation', 'sin', 'redemption', 'eternal life',
            'heaven', 'hell', 'angels', 'demons', 'spiritual warfare', 'wisdom',
            'guidance', 'healing', 'miracles', 'testimony', 'witness', 'obedience',
            'trust', 'patience', 'humility', 'joy', 'peace', 'thanksgiving',
            'repentance', 'confession', 'holiness', 'righteousness', 'justice'
        ]
        
        content_lower = content.lower()
        found_themes = []
        
        for theme in themes:
            if theme in content_lower:
                found_themes.append(theme)
        
        return found_themes[:10]  # Limit to top 10 themes

    def generate_conversation_summary(self, conversation_history: List[Dict]) -> Dict:
        """Generate a summary of the conversation for context"""
        if not conversation_history:
            return {}
        
        try:
            # Create a summary prompt
            summary_prompt = """Please provide a brief summary of this Bible study conversation, including:
1. Main topics discussed
2. Key Bible passages referenced
3. User's spiritual questions or concerns
4. Suggested next steps for study

Keep the summary concise but informative."""
            
            # Prepare conversation text
            conversation_text = ""
            for msg in conversation_history[-10:]:  # Last 10 messages
                role = "User" if msg.get("role") == "user" else "Assistant"
                conversation_text += f"{role}: {msg.get('content', '')}\n\n"
            
            messages = [
                {"role": "system", "content": summary_prompt},
                {"role": "user", "content": f"Conversation to summarize:\n{conversation_text}"}
            ]
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                temperature=0.3,
                max_tokens=300,
            )
            
            summary = response.choices[0].message.content
            
            return {
                "summary": summary,
                "message_count": len(conversation_history),
                "tokens_used": response.usage.total_tokens,
                "success": True,
            }
            
        except Exception as e:
            return {
                "summary": "Unable to generate conversation summary",
                "error": str(e),
                "success": False,
            }

    def suggest_follow_up_topics(self, conversation_context: Dict, user_context: Dict) -> List[str]:
        """Suggest follow-up topics based on conversation and user context"""
        suggestions = []
        
        # Based on Bible books mentioned
        bible_books = conversation_context.get('bible_books_mentioned', [])
        if bible_books:
            suggestions.append(f"Continue exploring {bible_books[0]} with related passages")
        
        # Based on themes discussed
        themes = conversation_context.get('potential_themes', [])
        if themes:
            primary_theme = themes[0]
            suggestions.append(f"Deepen your understanding of {primary_theme} in Scripture")
        
        # Based on user's faith goal
        if user_context:
            faith_goal = user_context.get('faith_goal', '')
            if faith_goal:
                suggestions.append(f"Continue working toward: {faith_goal}")
        
        # Based on user's journey reason
        journey_reason = user_context.get('journey_reason', '')
        if journey_reason and 'doubt' in journey_reason.lower():
            suggestions.append("Explore passages about faith and overcoming doubt")
        elif journey_reason and 'growth' in journey_reason.lower():
            suggestions.append("Study spiritual disciplines for continued growth")
        
        # Default suggestions
        if not suggestions:
            suggestions = [
                "Begin a daily Bible reading plan",
                "Study the Gospel of John for foundational understanding",
                "Explore the Psalms for prayer and worship",
                "Learn about Christian character in the New Testament"
            ]
        
        return suggestions[:5]  # Limit to 5 suggestions

    def validate_bible_reference(self, reference: str) -> bool:
        """Basic validation of Bible reference format"""
        # Simple validation patterns
        patterns = [
            r'^\d*\s*[A-Z][a-z]+\.?\s+\d+:\d+(-\d+)?$',  # John 3:16 or 1 John 3:16-17
            r'^\d*\s*[A-Z][a-z]+\.?\s+\d+$',             # John 3
        ]
        
        for pattern in patterns:
            if re.match(pattern, reference.strip()):
                return True
        
        return False

    def get_ai_health_status(self) -> Dict:
        """Get AI service health status"""
        try:
            # Simple health check with minimal token usage
            test_response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "Hello"}],
                temperature=0.1,
                max_tokens=10,
            )
            
            return {
                "status": "healthy",
                "model": self.model,
                "response_time": 0.1,  # Approximate
                "tokens_used": test_response.usage.total_tokens,
                "success": True,
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "model": self.model,
                "success": False,
            }