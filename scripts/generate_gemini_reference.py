"""Gera a imagem de referência da animação KAWA-AI por Gemini.

Requer GEMINI_API_KEY no ambiente. A chave nunca é escrita em arquivos ou saída.
"""

from __future__ import annotations

import os
from pathlib import Path

from google import genai
from google.genai import types


OUTPUT = Path("/home/ubuntu/webdev-static-assets/kawa-ai-animation/kawa-ai-reference.png")
PROMPT = """Create one 16:9 primary reference image for a motion graphic called KAWA-AI.
Subject: a premium local AI orchestration control panel viewed frontally, with a centered cyan hexagonal core and five balanced geometric modules around it, all connected by clean luminous data paths. The five modules must be visually distinct through shape only, not text.
Composition: the central core stays prominent at the center; ample dark negative space around the system; a small resource meter is visible near the lower section; a subtle translucent protective shield encloses one module. Everything is visible in a single stable wide composition.
Style: sophisticated technical product visualization, clean 3D geometric panels with vector-like precision, matte materials, subtle depth, near-black navy background with a very restrained grid, cyan and aqua for trusted flows, tiny amber accents only on the resource meter, soft controlled lighting.
Text/content to render: no text.
Constraints: horizontal 16:9, no people, no humanoid robots, no skulls, no hacker imagery, no random code, no logos, no watermarks, no labels, no annotations, no floating particles, no interface typography.
"""


def main() -> None:
    if not os.environ.get("GEMINI_API_KEY"):
        raise RuntimeError("GEMINI_API_KEY não está disponível no ambiente.")
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    response = client.models.generate_content(
        model="gemini-2.5-flash-image",
        contents=PROMPT,
        config=types.GenerateContentConfig(response_modalities=["IMAGE", "TEXT"]),
    )
    for candidate in response.candidates or []:
        for part in candidate.content.parts or []:
            if part.inline_data and part.inline_data.data:
                OUTPUT.write_bytes(part.inline_data.data)
                print(f"Imagem de referência salva em: {OUTPUT}")
                return
    raise RuntimeError("O Gemini não retornou uma imagem de referência.")


if __name__ == "__main__":
    main()
