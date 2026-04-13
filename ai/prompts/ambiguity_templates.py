"""Ambiguity resolution prompt template."""

AMBIGUITY_CLARIFICATION = """\
Un utilisateur a formulé une requête en langage naturel qui peut correspondre
à plusieurs interprétations différentes en SQL.

Requête originale : "{original_query}"

Interprétations possibles :
{interpretations_list}

Génère une question de clarification courte et naturelle en français pour demander
à l'utilisateur laquelle de ces interprétations il souhaite.

Règles :
- Maximum 2 phrases
- Ton conversationnel et professionnel
- Ne mentionne pas SQL, AST ou termes techniques
- Propose des options numérotées si plusieurs choix

Réponds uniquement avec la question de clarification.
"""
