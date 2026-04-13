"""
AmbiguityResolver — takes ambiguity candidates and generates a natural-language
clarification question via the AI module (or returns a template if AI unavailable).
"""

from __future__ import annotations


class AmbiguityResolver:
    """
    Given a list of candidate SQL strings, asks the AI module to phrase a
    natural French clarification question for the user.
    """

    def __init__(self, ai_ambiguity_handler=None):
        self._ai = ai_ambiguity_handler

    def resolve(self, original_query: str, candidate_sqls: list[str],
                question_hint: str) -> str:
        """Return a French clarification question string."""
        if self._ai:
            try:
                return self._ai.generate_clarification(
                    original_query=original_query,
                    candidate_sqls=candidate_sqls,
                    question_hint=question_hint,
                )
            except Exception:
                pass
        # Fallback: use the hint directly
        return question_hint
