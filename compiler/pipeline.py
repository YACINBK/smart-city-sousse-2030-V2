"""
NLToSQLPipeline — single public entry point for the compiler.

Stages:
  1. NLLexer       → token list
  2. NLParser      → QueryNode AST
  3. SemanticAnalyzer → resolved QueryNode
  4. AmbiguityDetector → check for ambiguity
  5. SQLCodeGenerator → CompileResult (sql, params, description)
"""

from dataclasses import dataclass

from compiler.lexer import NLLexer
from compiler.parser import NLParser
from compiler.semantic_analyzer import SemanticAnalyzer
from compiler.codegen import SQLCodeGenerator, CompileResult
from compiler.ambiguity.detector import AmbiguityDetector
from compiler.ast_nodes import QueryNode
from compiler.errors import CompilerError, AmbiguityError


@dataclass
class PipelineResult:
    """Full result of the compilation pipeline, including intermediate representations."""
    original_query: str
    tokens: list          # raw Token list
    ast: QueryNode        # parsed AST
    compile_result: CompileResult  # SQL + params + description
    ambiguity_question: str | None = None  # set if ambiguous and resolved


class NLToSQLPipeline:
    """Stateless compiler pipeline. Thread-safe."""

    def __init__(self):
        self._lexer = NLLexer()
        self._parser = NLParser()
        self._semantic = SemanticAnalyzer()
        self._codegen = SQLCodeGenerator()
        self._ambiguity = AmbiguityDetector()

    def compile(self, query: str) -> PipelineResult:
        """
        Compile a French NL query to SQL.

        Raises:
            LexerError, ParseError, SemanticError — on compilation failure
            AmbiguityError — when the query is ambiguous (caller should present choices)
        """
        # Stage 1: Lex
        tokens = self._lexer.tokenize(query)

        # Stage 2: Parse
        ast = self._parser.parse(tokens)

        # Stage 3: Semantic analysis
        ast = self._semantic.analyze(ast)

        # Stage 4: Ambiguity detection (bonus feature)
        ambiguity_question = None
        ambiguity_result = self._ambiguity.detect(ast, query)
        if ambiguity_result:
            # Raise so the caller (dashboard / tests) can handle the clarification flow
            raise AmbiguityError(
                message=ambiguity_result.question,
                interpretations=ambiguity_result.candidate_sqls,
            )

        # Stage 5: Code generation
        result = self._codegen.generate(ast)

        return PipelineResult(
            original_query=query,
            tokens=tokens,
            ast=ast,
            compile_result=result,
        )

    def compile_safe(self, query: str) -> dict:
        """
        Like compile() but returns a dict with success/error keys.
        Useful for the dashboard to avoid try/except blocks everywhere.
        """
        try:
            pr = self.compile(query)
            return {
                "success": True,
                "sql": pr.compile_result.sql,
                "params": pr.compile_result.params,
                "description": pr.compile_result.description,
                "ast": pr.ast.to_dict(),
                "tokens": [{"type": t.type.name, "value": t.value} for t in pr.tokens],
                "ambiguous": False,
                "error": None,
            }
        except AmbiguityError as e:
            return {
                "success": False,
                "ambiguous": True,
                "question": str(e),
                "interpretations": e.interpretations,
                "error": None,
            }
        except CompilerError as e:
            return {
                "success": False,
                "ambiguous": False,
                "error": str(e),
            }
