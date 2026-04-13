"""
AmbiguityHandler — bridges the compiler's AmbiguityDetector with the LLM
to generate natural French clarification questions.
"""

from __future__ import annotations

from ai.client import LLMClient, get_llm_client
from ai.prompts.ambiguity_templates import AMBIGUITY_CLARIFICATION


class AmbiguityHandler:

    def __init__(self, client: LLMClient | None = None):
        self._client = client or get_llm_client()

    def generate_clarification(
        self,
        original_query: str,
        candidate_sqls: list[str],
        question_hint: str,
    ) -> str:
        """
        Use the LLM to phrase a natural clarification question.

        Args:
            original_query: The user's original NL query.
            candidate_sqls: List of candidate SQL strings.
            question_hint: The detector's suggested question.

        Returns:
            A natural French clarification question string.
        """
        numbered = "\n".join(
            f"{i+1}. {sql.splitlines()[0]}..." for i, sql in enumerate(candidate_sqls[:4])
        )
        prompt = AMBIGUITY_CLARIFICATION.format(
            original_query=original_query,
            interpretations_list=numbered,
        )
        return self._client.complete(prompt, max_tokens=150)
