"""Compiler error hierarchy with French messages."""
from dataclasses import dataclass


@dataclass
class CompilerError(Exception):
    message: str
    pos: int = 0

    def __str__(self) -> str:
        if self.pos:
            return f"{self.message} (position {self.pos})"
        return self.message


class LexerError(CompilerError):
    """Raised for unrecognized characters or malformed tokens."""


class ParseError(CompilerError):
    """Raised when the token stream doesn't match the grammar."""


class SemanticError(CompilerError):
    """Raised when the AST is structurally valid but semantically incorrect."""


class AmbiguityError(CompilerError):
    """Raised when the query maps to multiple valid SQL interpretations."""
    interpretations: list[str]

    def __init__(self, message: str, interpretations: list[str], pos: int = 0):
        super().__init__(message, pos)
        self.interpretations = interpretations
