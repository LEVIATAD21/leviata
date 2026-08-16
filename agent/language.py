"""Normalização conservadora de linguagem natural para o KAWA-AI."""

from __future__ import annotations

import re
import unicodedata
from difflib import get_close_matches

# Apenas abreviações e erros recorrentes de intenção; palavras desconhecidas não
# são alteradas para não deformar nomes de arquivos, APIs ou projetos.
_COMMON_REPLACEMENTS = {
    "vc": "você",
    "vcs": "vocês",
    "q": "que",
    "pq": "porque",
    "tb": "também",
    "tbm": "também",
    "pra": "para",
    "pro": "para o",
    "agr": "agora",
    "dps": "depois",
    "msg": "mensagem",
    "ia": "inteligência artificial",
    "faca": "faça",
    "fazer": "fazer",
    "fazr": "fazer",
    "cria": "crie",
    "criar": "criar",
    "executa": "execute",
    "executar": "executar",
    "pesquiza": "pesquisa",
    "pesquizae": "pesquise",
    "seguranca": "segurança",
    "cyberseguranca": "cibersegurança",
    "ciberseguranca": "cibersegurança",
    "autonomo": "autônomo",
    "autonoma": "autônoma",
    "desenvolve": "desenvolva",
    "desenvolver": "desenvolver",
}

_DOMAIN_WORDS = {
    "crie", "criar", "corrija", "corrigir", "edite", "editar", "execute", "executar",
    "instale", "instalar", "pesquise", "pesquisa", "investigue", "explique", "aprenda",
    "código", "codigo", "site", "aplicativo", "segurança", "seguranca", "pentest",
    "autônomo", "autonomo", "memória", "memoria", "documentação", "documentacao",
    "skill", "skills", "workflow", "agente", "agentes", "supabase", "github",
}


def _fold(value: str) -> str:
    value = unicodedata.normalize("NFKD", value)
    return "".join(char for char in value if not unicodedata.combining(char)).lower()


def _repair_known_word(token: str) -> str:
    folded = _fold(token.strip(".,!?;:()[]{}\"'`"))
    if not folded or len(folded) < 4:
        return token
    candidates = {_fold(word): word for word in _DOMAIN_WORDS}
    match = get_close_matches(folded, candidates, n=1, cutoff=0.82)
    return candidates[match[0]] if match else token


def normalize_user_message(text: str) -> str:
    """Preserva a mensagem, corrigindo apenas ruído textual conhecido."""
    content = re.sub(r"\s+", " ", text.replace("\u00a0", " ")).strip()
    if not content:
        return ""
    tokens = []
    for token in content.split(" "):
        bare = token.strip(".,!?;:()[]{}\"'`").lower()
        replacement = _COMMON_REPLACEMENTS.get(bare)
        tokens.append(replacement or _repair_known_word(token))
    return " ".join(tokens)


def routing_text(text: str) -> str:
    """Texto sem acentos e com abreviações expandidas para classificação."""
    return _fold(normalize_user_message(text))
