"""
Prompt Builder Service.

Responsible for translating visual inputs and metadata into highly structured, provider-agnostic
AI requests. Centralizes all prompt engineering logic and hallucination guards.
"""
from typing import List, Dict, Any

from app.domain.models.video import CaptionTone
from app.domain.models.analysis import VisionInputPackage
from app.domain.models.ai import AIMessage, AIMessageRole, AITextContent, AIContentBlock
from app.domain.models.vision import VisionAnalysisRequest, VisionAnalysisResult
from app.domain.models.caption import CaptionGenerationRequest


class PromptBuilder:
    """
    Constructs provider-agnostic prompts for the Vision Analysis subsystem.
    """

    BASE_SYSTEM_PROMPT = (
        "You are an expert Vision AI tasked with analyzing a sequence of keyframes from a video scene. "
        "Your goal is to extract structured, semantic understanding of the scene.\n\n"
        "STRICT RULES:\n"
        "1. Focus ONLY on visual evidence present in the provided images.\n"
        "2. Do NOT hallucinate names, places, or context that is not visually verifiable.\n"
        "3. If something is ambiguous or cannot be seen, omit it or say 'unknown'.\n"
        "4. Ignore irrelevant background noise; focus on the primary action and subjects.\n"
        "5. Return your analysis strictly as structured JSON matching the requested schema."
    )

    TONE_MODIFIERS = {
        CaptionTone.SARCASTIC: "Pay special attention to absurdities, contradictions, or visually ironic elements in the scene.",
        CaptionTone.HUMOROUS_TECH: "Pay special attention to technology, screens, typing, or anything a developer might find relatable or funny.",
        CaptionTone.HUMOROUS_NON_TECH: "Pay special attention to everyday awkwardness, funny expressions, or visually comedic timing.",
        CaptionTone.FORMAL: "Maintain a strict, objective, and highly professional observation of events.",
        CaptionTone.AUDIO: "Focus on visual cues that indicate sound (e.g. speaking, playing instruments, explosions, shouting).",
        CaptionTone.NONE: "Extract a neutral and balanced summary."
    }

    def build_system_prompt(self, target_tone: CaptionTone) -> str:
        """Constructs the system instructions including tone-specific modifiers."""
        modifier = self.TONE_MODIFIERS.get(target_tone, self.TONE_MODIFIERS[CaptionTone.NONE])
        return f"{self.BASE_SYSTEM_PROMPT}\n\nTONE MODIFIER: {modifier}"

    def build_user_prompt(self) -> str:
        """Constructs the exact text instructions for the user message."""
        return (
            "Analyze the following sequence of images (ordered chronologically) and extract:\n"
            "- A brief scene summary\n"
            "- Visible objects and people\n"
            "- Human activities and facial expressions (if visible)\n"
            "- Environment, lighting, and camera angle\n"
            "- Dominant colors and mood\n"
            "- Any important visible text (OCR)\n"
            "- Any safety flags (e.g. violence, NSFW)\n"
            "Extract anything useful for generating a caption later."
        )

    def _build_response_format(self) -> Dict[str, Any]:
        """
        Builds a generic JSON schema representation matching VisionAnalysisResult.
        Note: Providers like Fireworks and OpenAI natively support this format for structured output.
        """
        return {
            "type": "json_schema",
            "json_schema": {
                "name": "vision_analysis_result",
                "strict": True,
                "schema": {
                    "type": "object",
                    "properties": {
                        "scene_summary": {"type": "string"},
                        "objects": {"type": "array", "items": {"type": "string"}},
                        "people": {"type": "array", "items": {"type": "string"}},
                        "activities": {"type": "array", "items": {"type": "string"}},
                        "environment": {"type": "string"},
                        "mood": {"type": "string"},
                        "dominant_colors": {"type": "array", "items": {"type": "string"}},
                        "ocr_placeholder": {"type": "string"},
                        "safety_flags": {"type": "array", "items": {"type": "string"}}
                    },
                    "required": [
                        "scene_summary", "objects", "people", "activities", 
                        "environment", "mood", "dominant_colors", 
                        "ocr_placeholder", "safety_flags"
                    ],
                    "additionalProperties": False
                }
            }
        }

    def build_messages(self, package: VisionInputPackage) -> List[AIMessage]:
        """Builds the multi-turn conversation array."""
        target_tone = package.target_tone or CaptionTone.NONE
        
        system_msg = AIMessage(
            role=AIMessageRole.SYSTEM,
            content=[AITextContent(text=self.build_system_prompt(target_tone))]
        )

        user_content: List[AIContentBlock] = [AITextContent(text=self.build_user_prompt())]
        # Append all keyframes chronologically
        for kf in package.key_frames:
            user_content.append(kf)

        user_msg = AIMessage(
            role=AIMessageRole.USER,
            content=user_content
        )

        return [system_msg, user_msg]

    def build_scene_analysis_prompt(self, package: VisionInputPackage) -> VisionAnalysisRequest:
        """
        Master method to convert a VisionInputPackage into a ready-to-send VisionAnalysisRequest.
        """
        messages = self.build_messages(package)
        response_format = self._build_response_format()
        
        return VisionAnalysisRequest(
            messages=messages,
            response_format=response_format,
            max_tokens=1500,
            temperature=0.2
        )

    # Caption-writing style instructions per tone. Unlike TONE_MODIFIERS
    # (which steer vision analysis), these describe the voice of the final
    # ready-to-post social media caption.
    CAPTION_TONE_STYLES = {
        CaptionTone.FORMAL: (
            "Write a polished, professional caption suitable for LinkedIn or a brand page. "
            "Clear, confident, no slang, at most one tasteful emoji."
        ),
        CaptionTone.SARCASTIC: (
            "Write a dry, witty, sarcastic caption. Deadpan humor, playful mockery of the "
            "situation in the video, internet-native voice."
        ),
        CaptionTone.HUMOROUS_TECH: (
            "Write a funny caption aimed at developers/tech people. Programming jokes, "
            "tech culture references, relatable engineering humor."
        ),
        CaptionTone.HUMOROUS_NON_TECH: (
            "Write a funny, widely relatable caption for a general audience. Everyday humor, "
            "meme-adjacent energy, no technical references."
        ),
        CaptionTone.AUDIO: (
            "Write a caption that plays on the sounds implied by the video (music, speech, "
            "noise), inviting viewers to turn the sound on."
        ),
        CaptionTone.NONE: (
            "Write a clean, engaging, neutral caption that describes the moment compellingly."
        ),
    }

    def build_caption_generation_prompt(
        self,
        analysis_result: VisionAnalysisResult,
        target_tone: CaptionTone
    ) -> CaptionGenerationRequest:
        """
        Constructs a prompt for generating a caption based on a VisionAnalysisResult.
        """
        style = self.CAPTION_TONE_STYLES.get(target_tone, self.CAPTION_TONE_STYLES[CaptionTone.NONE])
        system_msg = AIMessage(
            role=AIMessageRole.SYSTEM,
            content=[AITextContent(
                text="You are an expert social media caption writer. Given a scene analysis "
                     "from a video, write ONE ready-to-post caption for social media "
                     "(Instagram/TikTok/X style).\n"
                     f"STYLE: {style}\n"
                     "RULES:\n"
                     "1. Output ONLY the caption text — no quotes, no preamble, no explanations.\n"
                     "2. Keep it short and punchy: 1-2 sentences, under 200 characters preferred.\n"
                     "3. Add 2-4 relevant hashtags at the end.\n"
                     "4. Do NOT describe the video mechanically — capture its vibe and hook the viewer.\n"
                     "5. Base it only on what is actually in the scene analysis."
            )]
        )
        
        user_content = (
            f"Scene Summary: {analysis_result.scene_summary}\n"
            f"Objects: {', '.join(analysis_result.objects)}\n"
            f"People: {', '.join(analysis_result.people)}\n"
            f"Activities: {', '.join(analysis_result.activities)}\n"
            f"Environment: {analysis_result.environment}\n"
            f"Mood: {analysis_result.mood}\n"
            f"OCR text: {analysis_result.ocr_placeholder}\n\n"
            "Write the caption now:"
        )
        
        user_msg = AIMessage(
            role=AIMessageRole.USER,
            content=[AITextContent(text=user_content)]
        )
        
        return CaptionGenerationRequest(
            messages=[system_msg, user_msg],
            target_tone=target_tone,
            temperature=0.7,
            max_tokens=500
        )
