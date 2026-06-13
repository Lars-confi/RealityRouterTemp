"""
Keyword manager for dynamic cross-lingual feature translation
"""

import json
import os
from typing import Dict, List, Set

from pydantic import BaseModel

from src.config.settings import get_settings
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class SemanticIntents(BaseModel):
    """Data model representing the semantic intent keywords"""

    gen: List[str]
    fix: List[str]
    refactor: List[str]
    docs: List[str]
    math: List[str]
    summarize: List[str]
    roleplay: List[str]
    format_table: List[str]
    analytical: List[str]
    meta_pos_con: List[str]
    meta_neg_con: List[str]


# Base English keywords (Hardcoded defaults)
BASE_KEYWORDS = {
    "gen": ["create", "write", "generate", "implement"],
    "fix": ["fix", "bug", "debug", "error"],
    "refactor": ["refactor", "optimize", "clean"],
    "docs": ["document", "comment", "readme"],
    "math": ["calculate", "solve", "math", "equation"],
    "summarize": ["summarize", "tl;dr", "summary", "briefly"],
    "roleplay": ["act as", "you are a", "persona", "imagine"],
    "format_table": ["table", "csv", "excel", "columns"],
    "analytical": ["why", "how"],
    "meta_pos_con": ["must", "use", "always"],
    "meta_neg_con": ["don't", "never", "avoid"],
}


class KeywordManager:
    """Manages language-agnostic intent translation"""

    def __init__(self):
        self.settings = get_settings()
        self.app_home = os.getenv(
            "REALITY_ROUTER_HOME", os.path.expanduser("~/.reality_router")
        )
        self.keywords_file = os.path.join(self.app_home, "multilingual_keywords.json")
        self.intents = SemanticIntents(**BASE_KEYWORDS)
        self._load_keywords()

    def _load_keywords(self) -> None:
        """Load translated keywords from disk if they exist, combining with base english"""
        if os.path.exists(self.keywords_file):
            try:
                with open(self.keywords_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                # Merge base english with loaded translations
                merged_data = {}
                for key, base_list in BASE_KEYWORDS.items():
                    loaded_list = data.get(key, [])
                    # Use a set to deduplicate
                    merged_set = set(base_list)
                    merged_set.update([str(item).lower() for item in loaded_list])
                    merged_data[key] = list(merged_set)

                self.intents = SemanticIntents(**merged_data)
                logger.info(f"Loaded multilingual keywords from {self.keywords_file}")
            except Exception as e:
                logger.error(f"Failed to load multilingual keywords: {e}")

    def save_keywords(self) -> None:
        """Save current intents back to disk"""
        try:
            with open(self.keywords_file, "w", encoding="utf-8") as f:
                json.dump(self.intents.model_dump(), f, indent=4, ensure_ascii=False)
            logger.debug(f"Saved multilingual keywords to {self.keywords_file}")
        except Exception as e:
            logger.error(f"Failed to save multilingual keywords: {e}")

    async def translate_and_add_keywords(self, adapter, target_language: str) -> bool:
        """
        Use an LLM adapter to translate the base keywords to a new language and add them to the pool.
        This allows Snap to work correctly across any language.
        """
        logger.info(f"Translating semantic keywords to {target_language}...")

        prompt = (
            f"I need to detect semantic intents in user prompts for a language model router. "
            f"Translate the following sets of English keywords into highly common, natural equivalents in {target_language}. "
            f"For each category, provide 3 to 6 common single words or very short phrases (lowercase) that a user would typically type. "
            f"Respond ONLY with a valid JSON object matching this exact structure, containing arrays of strings:\n\n"
            f"{json.dumps(BASE_KEYWORDS, indent=2)}"
        )

        from src.models.routing import RoutingRequest

        req = RoutingRequest(
            query=prompt,
            parameters={
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.1,
                "response_format": {"type": "json_object"},
            },
        )

        try:
            response = await adapter.forward_request(req)
            content = response.get("text", "")
            if not content:
                content = response.get("reasoning_content", "")

            # Clean potential markdown wrapping
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()

            translated_data = json.loads(content)

            # Validate and merge
            updated = False
            current_dict = self.intents.model_dump()

            for key in BASE_KEYWORDS.keys():
                if key in translated_data and isinstance(translated_data[key], list):
                    current_set = set(current_dict[key])
                    original_len = len(current_set)

                    # Add new words
                    current_set.update(
                        [
                            str(w).lower()
                            for w in translated_data[key]
                            if isinstance(w, str)
                        ]
                    )

                    if len(current_set) > original_len:
                        current_dict[key] = list(current_set)
                        updated = True

            if updated:
                self.intents = SemanticIntents(**current_dict)
                self.save_keywords()
                logger.info(
                    f"Successfully added {target_language} keywords to the routing pool."
                )
                return True
            else:
                logger.debug(f"No new keywords generated for {target_language}.")
                return False

        except Exception as e:
            logger.error(f"Failed to translate keywords for {target_language}: {e}")
            return False

    def get_regex(self, intent_name: str) -> str:
        """Get a regex pattern matching any of the keywords for a specific intent"""
        words = getattr(self.intents, intent_name, [])
        if not words:
            return r"(?!x)x"  # Unmatchable regex

        # Escape special characters and join with OR
        import re

        escaped_words = [re.escape(w) for w in words]
        return r"\b(" + "|".join(escaped_words) + r")\b"


# Global singleton instance
keyword_manager = KeywordManager()
