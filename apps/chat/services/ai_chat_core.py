import openai
import time
import re
from typing import List, Dict, Optional
from django.conf import settings


# ─── Tier Prompts ────────────────────────────────────────────────────────────────

TIER_CONVERSATION_READY = """You are a Christian articulation assistant for the Preachly app.
Your task is to generate a "Conversation Ready" response to a user-submitted objection or faith-based question.
When responding to objections, explain the Christian perspective rather than correcting the questioner's position.
Frame ideas positively instead of refuting opposing views.
This tier is designed to give believers something they can confidently say in a real conversation.

The response MUST follow this exact structure:

CONVERSATION READY

1. Direct Answer (Clear & Decisive)
Begin with a clear, confident answer in 1–2 sentences.
No hedging language. If relevant, include one short Scripture quote integrated naturally.

2. Clarifying Frame (Balanced Theology)
2–4 short sentences (max 80 words) explaining the theological framing.
Emphasize grace-first Christianity. Keep tight and conversational.

3. Say It Like This (Conversation Sentence)
One short quotation someone could actually say in a live conversation. 1–2 sentences max.
Format as:
You could say:
"…"

4. Short Metaphor (Memorable & Simple)
One brief metaphor or analogy (2–3 sentences max). Vivid but simple.

STYLE: No emojis. No AI disclaimers. No mention of internal structure. Clean formatting.
Tier structure overrides tone if conflicts arise."""

TIER_IN_DEPTH = """You are a Christian articulation assistant for the Preachly app.
Your task is to generate an "In-Depth" response to a user-submitted objection or faith-based question.
When responding to objections, explain the Christian perspective rather than correcting the questioner's position.
Frame ideas positively instead of refuting opposing views.

The response MUST follow this exact structure:

IN-DEPTH RESPONSE

1. Clear Starting Point
2–4 sentences. Clear but warm answer. Establish emotional steadiness.
Include one Scripture quote in full sentence form if appropriate.

2. Expanding the Foundation
Biblical and theological reasoning. Include 1–3 Scripture references (quote at least one in full).
Explain key distinctions clearly. Keep sentences readable. No jargon. No sermon tone.

3. What This Means Personally
Apply theology to real life. Address emotional realities. Emphasize humility.
Feel human and pastoral, not theoretical.

4. How You Could Walk Someone Through It
4–6 sentences. Natural language. No church jargon. Calm and thoughtful.
Format as:
If I were explaining it more fully, I might say:
"…"

5. Reflection Prompt (For Personal Practice)
1–2 reflective questions the user can ask themselves to deepen understanding.

STYLE: No emojis. No AI disclaimers. No mention of internal structure. Clean formatting.
Tier structure overrides tone if conflicts arise."""

TIER_FULL_FRAMEWORK = """You are an advanced Christian worldview articulation assistant for the Preachly app.
Your task is to generate a "Full Framework" response to a user-submitted objection or faith-based question.
When responding to objections, explain the Christian perspective rather than correcting the questioner's position.
Frame ideas positively instead of refuting opposing views.

The response MUST follow this exact structure:

FULL FRAMEWORK

1. Biblical Foundation
Include 1–2 scripture passages directly and explain their meaning in context.
Do not list verses without explanation. Present balanced biblical tension if applicable.

2. Theological Coherence
Explain how this issue fits within Creation, Fall, Redemption, Restoration.
Clarify key theological distinctions. Emphasize grace-first framing. No denominational bias.

3. Philosophical Coherence
Demonstrate internal logical consistency within the Christian worldview.
Connect to real human questions about meaning, dignity, identity, morality.
Do not attack opposing views — highlight worldview consistency.

4. Cultural Engagement Layer
Acknowledge emotional or cultural weight behind the question.
Offer a short conversation-ready framing sentence someone could say.
Keep tone calm, grounded, non-reactive.

5. Strategic Summary
Four concise bullet points:
Biblically —
Theologically —
Philosophically —
Culturally —

STYLE: No emojis. No AI disclaimers. No mention of internal structure. Clean formatting.
Tier structure overrides tone if conflicts arise."""

# ─── Clarification Prompts ───────────────────────────────────────────────────────

CLARIFICATION_YES_PROMPT = """If the user selects Need More Clarity (YES), provide a focused expansion that deepens the explanation without repeating the original response.

Rules:
- Do NOT restate the previous answer.
- Do NOT summarize the earlier response.
- Assume the user has already read it.
- Move the explanation one step deeper.

Structure:
1. Clarify the Key Idea — explain core concept more clearly in 2–3 sentences.
2. Add a New Insight — one new perspective or distinction not mentioned before.
3. Scriptural Reinforcement — 1 additional relevant scripture reference.
4. Practical Understanding — why this matters in real life or conversations.

Maximum 120 words. Short clear sentences. No repeating phrases from original.
No sermon tone. No vague language. Return only the clarification response."""

CLARIFICATION_NO_PROMPT = """If the user selects No for "Need More Clarity," generate a thoughtful follow-up question the user could ask in conversation.

The purpose is to keep the conversation relational and curious rather than argumentative.

Format exactly as:
You could ask:
"…"

Guidelines:
- Feel natural in spoken conversation
- Invite the other person to share their perspective
- Avoid sounding like a debate tactic
- Avoid interrogative or confrontational tone
- Calm, curious, thoughtful
- No church jargon
- Under 40 words total

Return only the follow-up question in the format above."""

# ─── Tone Blocks ─────────────────────────────────────────────────────────────────

TONE_BLOCKS = {
    "Clear and Hopeful": {
        "description": "Simple, direct, and steady. Communicates truth clearly while emphasizing God's love and faithfulness.",
        "guardrails": ["Short sentences", "Minimal imagery", "Calm cadence", "No emotional intensity spikes"]
    },
    "Dynamic and Powerful": {
        "description": "Bold, vivid, and image-driven. Uses strong verbs and compelling contrasts. Stirs conviction without aggression.",
        "guardrails": ["Strong verbs (redeems, breaks, restores)", "Controlled vivid imagery", "Rhythmic phrasing", "Avoid softness"]
    },
    "Practical and Everyday": {
        "description": "Down-to-earth and solution-oriented. Focuses on how faith plays out in real decisions and habits.",
        "guardrails": ["Real-life examples", "Action steps implied", "Minimal theological abstraction", "Everyday language"]
    },
    "Encouraging and Purposeful": {
        "description": "Affirming and growth-focused. Emphasizes development, refinement, and becoming. Frames challenges as shaping moments.",
        "guardrails": ["Words like growth, shaping, forming", "Gentle optimism", "Avoid dramatic language", "Avoid hype"]
    },
    "Uplifting and Optimistic": {
        "description": "Light-filled and joy-centered. Emphasizes hope, renewal, and God's goodness prevailing over darkness.",
        "guardrails": ["Hope-forward phrasing", "Emphasis on joy and restoration", "Avoid heavy theological depth", "Avoid emotional intensity"]
    },
    "Scholarly and Rational": {
        "description": "Structured, reasoned, and historically grounded. Appeals to logic, coherence, and theological continuity.",
        "guardrails": ["Structured reasoning", "Use of distinctions", "Historical or doctrinal references", "Minimal emotional language"]
    },
    "Warm and Relatable": {
        "description": "Conversational, compassionate, and emotionally aware. Acknowledge struggle before offering clarity.",
        "guardrails": ["Validate emotion first", "Gentle phrasing", "Natural speech cadence", "Avoid intensity or hype"]
    },
    "Passionate and Empowering": {
        "description": "Confident and action-oriented. Emphasizes spiritual authority, identity in Christ, and bold forward movement.",
        "guardrails": ["Direct calls to courage", "Identity language ('You are...')", "Forward momentum", "Avoid softness"]
    },
}

# ─── Tier Config ─────────────────────────────────────────────────────────────────

TIER_CONFIG = {
    "Conversation Ready": {
        "prompt": TIER_CONVERSATION_READY,
        "max_tokens": 600,
        "temperature": 0.55,
    },
    "In-Depth Explanation": {
        "prompt": TIER_IN_DEPTH,
        "max_tokens": 1000,
        "temperature": 0.6,
    },
    "Full Framework": {
        "prompt": TIER_FULL_FRAMEWORK,
        "max_tokens": 1350,
        "temperature": 0.5,
    },
}


def build_tone_block(tone_name: str, tier_name: str) -> str:
    """Build the tone injection system message"""
    tone = TONE_BLOCKS.get(tone_name, TONE_BLOCKS["Clear and Hopeful"])
    guardrails = "\n".join([f"- {g}" for g in tone["guardrails"]])

    # Tone intensity based on tier
    intensity_map = {
        "Conversation Ready": "60%",
        "In-Depth Explanation": "80%",
        "Full Framework": "50%",
    }
    intensity = intensity_map.get(tier_name, "70%")

    return f"""USER-SELECTED TONE DIRECTIVE:

Tone Name: {tone_name}

Tone Description:
{tone["description"]}

Tone Behavioral Constraints:
{guardrails}

Tone Application Rules:
- Maintain this tone consistently.
- Do not override structural requirements of the selected tier.
- If tone conflicts with clarity, prioritize clarity.
- Avoid blending with other tones.
- Match tone subtly, not theatrically.
- Tone intensity should be moderated to approximately {intensity} to fit the selected tier depth."""


# ─── Main AI Service ──────────────────────────────────────────────────────────────

class AIChatCore:
    """Preachly AI service — GPT-5 with modular Tier + Tone architecture"""

    MODEL = "gpt-4.1"  

    def __init__(self):
        self.client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)

    def _call_api(self, messages: List[Dict], max_tokens: int, temperature: float = None) -> Dict:
        kwargs = {
            "model": self.MODEL,
            "messages": messages,
            "max_tokens": max_tokens,  # gpt-4.1 uses max_tokens normally
        }
        if temperature is not None:
            kwargs["temperature"] = temperature
        return self.client.chat.completions.create(**kwargs)

    def generate_preachly_response(
        self,
        objection: str,
        tone: str = "Clear and Hopeful",
        depth: str = "In-Depth Explanation",
        user_context: Dict = None,
    ) -> Dict:
        """
        Generate Preachly structured response.
        Uses two separate system messages: Tier + Tone (modular architecture).
        """
        start_time = time.time()

        try:
            tier_config = TIER_CONFIG.get(depth, TIER_CONFIG["In-Depth Explanation"])
            tier_prompt = tier_config["prompt"]
            max_tokens = tier_config["max_tokens"]
            temperature = tier_config["temperature"]
            tone_block = build_tone_block(tone, depth)

            messages = [
                {"role": "system", "content": tier_prompt},
                {"role": "system", "content": tone_block},
                {"role": "user", "content": objection},
            ]

            response = self._call_api(messages, max_tokens, temperature)
            content = response.choices[0].message.content
            print(f"DEBUG content extracted: {content!r}")

            return {
                "content": content,
                "tokens_used": response.usage.total_tokens,
                "response_time": time.time() - start_time,
                "model_used": self.MODEL,
                "tone": tone,
                "depth": depth,
                "success": True,
            }

        except Exception as e:
            return {
                "content": self._get_biblical_error_message(),
                "success": False,
                "error": str(e),
                "tone": tone,
                "depth": depth,
            }

    def generate_clarification_yes(
        self,
        original_response: str,
        tone: str = "Clear and Hopeful",
    ) -> Dict:
        """
        Handle 'Need More Clarity → YES'.
        Deepens explanation without restating.
        Max 120 words.
        """
        start_time = time.time()

        try:
            tone_block = build_tone_block(tone, "Conversation Ready")

            messages = [
                {"role": "system", "content": CLARIFICATION_YES_PROMPT},
                {"role": "system", "content": tone_block},
                {"role": "user", "content": f"Original response:\n{original_response}"},
            ]

            response = self._call_api(messages, max_tokens=3000, temperature=0.5)
            content = response.choices[0].message.content

            return {
                "content": content,
                "tokens_used": response.usage.total_tokens,
                "response_time": time.time() - start_time,
                "success": True,
                "type": "clarification_yes",
            }

        except Exception as e:
            return {
                "content": "Let me try to clarify further. The core idea here is that God's grace doesn't depend on our performance — it's freely given.",
                "success": False,
                "error": str(e),
            }

    def generate_clarification_no(
        self,
        original_response: str,
        tone: str = "Clear and Hopeful",
    ) -> Dict:
        """
        Handle 'Need More Clarity → NO'.
        Generates a follow-up question the user can ask in conversation.
        Always ends with static UI text: '— or —\nStart a new chat'
        """
        start_time = time.time()

        try:
            tone_block = build_tone_block(tone, "Conversation Ready")

            messages = [
                {"role": "system", "content": CLARIFICATION_NO_PROMPT},
                {"role": "system", "content": tone_block},
                {"role": "user", "content": f"Original response topic:\n{original_response[:200]}"},
            ]

            response = self._call_api(messages, max_tokens=100, temperature=0.6)

            # NOTE: '— or —\nStart a new chat' is appended at UI level, not here.

            content = response.choices[0].message.content
    
            # Clean up formatting — remove extra newlines and normalize quotes
            content = content.strip()
            content = content.replace('\n"', ' "')
            content = content.replace('You could ask:  \n', 'You could ask: ')
            content = content.replace('You could ask:\n', 'You could ask: ')

            import re
            content = re.sub(r'You could ask:\s+', 'You could ask: ', content)

            return {
                "content": content,
                "tokens_used": response.usage.total_tokens,
                "response_time": time.time() - start_time,
                "success": True,
                "type": "clarification_no",
                "show_new_chat_option": True,  # Frontend uses this to render the static text
            }

        except Exception as e:
            return {
                "content": 'You could ask:\n"What made you start thinking about this topic?"',
                "success": False,
                "error": str(e),
                "show_new_chat_option": True,
            }

    def generate_bible_response(
        self,
        conversation_history: List[Dict],
        user,
        user_context: Dict = None,
    ) -> Dict:
        """Generate Bible-focused AI response (used by WebSocket consumer)"""
        start_time = time.time()

        try:
            system_prompt = self._build_bible_system_prompt(user_context)
            messages = [{"role": "system", "content": system_prompt}]
            messages.extend(conversation_history)

            response = self._call_api(messages, max_tokens=1000, temperature=0.7)
            content = response.choices[0].message.content
            bible_references = self._extract_bible_references(content)

            return {
                "content": content,
                "tokens_used": response.usage.total_tokens,
                "response_time": time.time() - start_time,
                "model_used": self.MODEL,
                "bible_references": bible_references,
                "success": True,
            }

        except Exception as e:
            return {
                "content": "I'm having trouble responding right now. Please try again.",
                "tokens_used": 0,
                "response_time": time.time() - start_time,
                "model_used": self.MODEL,
                "bible_references": [],
                "success": False,
                "error": str(e),
            }

    def _build_bible_system_prompt(self, user_context: Dict = None) -> str:
        denomination = ""
        tone = "Clear and Hopeful"
        bible_version = "NIV"

        if user_context:
            denomination = user_context.get('denomination', '')
            tone_pref = user_context.get('tone_preference', {})
            if isinstance(tone_pref, dict):
                tone = tone_pref.get('name', tone)
            bv = user_context.get('bible_version', {})
            if isinstance(bv, dict):
                bible_version = bv.get('title', bible_version)

        denomination_line = f"\nUser's denomination: {denomination}" if denomination else ""

        return f"""You are Preachly, a Christian Bible study assistant.
Provide scripture-based, thoughtful answers to faith questions.
Tone: {tone}
Bible version preference: {bible_version}{denomination_line}
Be encouraging, biblically grounded, and conversational.
Do not use emojis. Do not mention being an AI."""

    def _extract_bible_references(self, content: str) -> List[Dict]:
        patterns = [
            r'\b\d*\s*([A-Z][a-z]+\.?)\s+(\d+):(\d+(?:-\d+)?)\b',
            r'\b([A-Z][a-z]+\.?)\s+(\d+):(\d+(?:-\d+)?)\b',
        ]
        references = []
        for pattern in patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                if len(match) == 3:
                    book, chapter, verse = match
                    references.append({
                        "book": book,
                        "chapter": int(chapter),
                        "verse": verse,
                        "reference": f"{book} {chapter}:{verse}"
                    })
        # Deduplicate
        seen = set()
        unique = []
        for ref in references:
            key = (ref['book'], ref['chapter'], ref['verse'])
            if key not in seen:
                seen.add(key)
                unique.append(ref)
        return unique

    def _get_biblical_error_message(self) -> str:
        import random
        errors = [
            "Seems I'm having a 'parting of the Red Sea' moment—stuck in the middle! Give it another go.",
            "Looks like I'm having a Jonah moment—briefly off course! Try again, and we'll get back on mission.",
            "I've hit a Jericho wall, but don't worry—it's coming down! Give it another try.",
            "Even Paul had shipwrecks—this is mine. Let's try again and stay the course.",
            "I've run into a Goliath-sized glitch… but I've got my slingshot ready. Try again!",
        ]
        return random.choice(errors)

    def get_ai_health_status(self) -> Dict:
        try:
            response = self._call_api(
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=10
            )
            return {
                "status": "healthy",
                "model": self.MODEL,
                "tokens_used": response.usage.total_tokens,
                "success": True,
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "model": self.MODEL,
                "success": False,
            }
