"""
NLLexer — tokenizes French natural-language queries into a Token stream.

Key design decisions:
  - Phrase-first scan: multi-word phrases are checked before single words.
  - Unicode-aware: accented characters handled natively.
  - Stop-word swallowing: articles / prepositions are silently dropped.
  - Position tracking: every token carries its start index for error messages.
"""

import re
import unicodedata
from typing import Iterator

from compiler.tokens import (
    Token, TokenType, PHRASE_MAP, KEYWORD_MAP, STOP_WORDS
)
from compiler.errors import LexerError


def _normalize(text: str) -> str:
    """Lowercase and strip leading/trailing whitespace."""
    return text.strip().lower()


def _strip_accents(text: str) -> str:
    """Return NFD-normalized text with combining characters removed."""
    return "".join(
        c for c in unicodedata.normalize("NFD", text)
        if unicodedata.category(c) != "Mn"
    )


class NLLexer:
    """
    Converts a French NL query string into a flat list of Token objects.

    Usage:
        lexer = NLLexer()
        tokens = lexer.tokenize("Affiche les 5 capteurs les plus polluées")
    """

    # Regex that splits on whitespace, punctuation, apostrophes
    _SPLIT_RE = re.compile(r"[,;!?\s''\u2019]+")
    _NUMBER_RE = re.compile(r"^-?\d+(\.\d+)?$")
    _QUOTED_RE = re.compile(r"^['\"](.+)['\"]$")

    def __init__(self):
        # Pre-compute normalized phrase list sorted by descending length (greedy)
        self._phrases = sorted(
            ((p, t) for p, t in PHRASE_MAP.items()),
            key=lambda x: -len(x[0].split())
        )

    # ──────────────────────────────────────────────────────────
    # Public API
    # ──────────────────────────────────────────────────────────

    def tokenize(self, query: str) -> list[Token]:
        """Return a token list ending with EOF."""
        if not query or not query.strip():
            raise LexerError("La requête est vide.", pos=0)

        tokens: list[Token] = []
        words = self._split_into_words(query)

        i = 0
        while i < len(words):
            word, pos = words[i]
            norm = _normalize(word)

            # 1. Try to match a multi-word phrase starting at position i
            phrase_match = self._match_phrase(words, i)
            if phrase_match:
                token_type, consumed = phrase_match
                tokens.append(Token(type=token_type, value=" ".join(w for w, _ in words[i:i+consumed]), pos=pos))
                i += consumed
                continue

            # 2. Quoted string literal
            m = self._QUOTED_RE.match(norm)
            if m:
                tokens.append(Token(type=TokenType.STRING, value=m.group(1), pos=pos))
                i += 1
                continue

            # 3. Number literal
            if self._NUMBER_RE.match(norm):
                tokens.append(Token(type=TokenType.NUMBER, value=norm, pos=pos))
                i += 1
                continue

            # 4. Stop words → silently skip
            if norm in STOP_WORDS or _strip_accents(norm) in STOP_WORDS:
                i += 1
                continue

            # 5. Keyword map (with accent-stripped fallback)
            token_type = KEYWORD_MAP.get(norm) or KEYWORD_MAP.get(_strip_accents(norm))
            if token_type is not None:
                tokens.append(Token(type=token_type, value=norm, pos=pos))
                i += 1
                continue

            # 6. Unknown → IDENTIFIER (semantic analyzer will resolve or reject)
            if norm and norm not in {"=", ">", "<", ">=", "<="}:
                tokens.append(Token(type=TokenType.IDENTIFIER, value=norm, pos=pos))
            elif norm in {"=", ">", "<", ">=", "<="}:
                cmp_map = {"=": TokenType.CMP_EQ, ">": TokenType.CMP_GT,
                           "<": TokenType.CMP_LT, ">=": TokenType.CMP_GTE, "<=": TokenType.CMP_LTE}
                tokens.append(Token(type=cmp_map[norm], value=norm, pos=pos))

            i += 1

        tokens.append(Token(type=TokenType.EOF, value="", pos=len(query)))
        return tokens

    # ──────────────────────────────────────────────────────────
    # Internal helpers
    # ──────────────────────────────────────────────────────────

    def _split_into_words(self, query: str) -> list[tuple[str, int]]:
        """Split query into (word, char_offset) pairs, preserving operators."""
        # First split on whitespace/commas
        result: list[tuple[str, int]] = []
        pos = 0
        for token_str in self._SPLIT_RE.split(query):
            if token_str:
                # Sub-split on comparison operators but keep them
                for part in re.split(r"(>=|<=|>|<|=)", token_str):
                    if part:
                        result.append((part, pos))
                pos += len(token_str)
            pos += 1  # for the splitter character
        return result

    def _match_phrase(self, words: list[tuple[str, int]], i: int) -> tuple[TokenType, int] | None:
        """Try to match a multi-word phrase starting at index i. Returns (type, words_consumed)."""
        for phrase, token_type in self._phrases:
            phrase_words = phrase.split()
            n = len(phrase_words)
            if i + n > len(words):
                continue
            candidate = " ".join(_normalize(w) for w, _ in words[i:i+n])
            candidate_stripped = " ".join(_strip_accents(_normalize(w)) for w, _ in words[i:i+n])
            if candidate == phrase or candidate_stripped == _strip_accents(phrase):
                return token_type, n
        return None
