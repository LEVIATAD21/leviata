import tempfile
import unittest
from pathlib import Path

from agent.rag import LocalRag, RagError, _cosine_pure


class StubRag(LocalRag):
    """RAG com embeddings determinísticos (sem Ollama nos testes)."""

    def __init__(self, db_path):
        super().__init__(db_path)

    def _embed(self, text):
        # vetor pseudo-semântico: posição por palavra-chave presente
        tokens = ["memória", "voz", "backup", "segurança", "projeto"]
        return [1.0 if token in text.lower() else 0.0 for token in tokens]


class RagTests(unittest.TestCase):
    def setUp(self):
        self.db = Path(tempfile.mkdtemp()) / "rag.sqlite3"
        self.rag = StubRag(self.db)

    def test_cosine_pure_matches_and_orthogonal_zero(self):
        self.assertAlmostEqual(_cosine_pure([1, 0], [1, 0]), 1.0)
        self.assertAlmostEqual(_cosine_pure([1, 0], [0, 1]), 0.0)

    def test_add_and_search_finds_related_entry(self):
        self.rag.add("O projeto tem memória semântica local.")
        self.rag.add("Receita de bolo de chocolate.")
        results = self.rag.search("como funciona a memória do projeto?", top_k=1)
        self.assertEqual(len(results), 1)
        self.assertIn("memória", results[0]["text"])

    def test_stats_counts_entries(self):
        self.rag.add("texto um")
        self.rag.add("texto dois")
        self.assertEqual(self.rag.stats()["entries"], 2)

    def test_add_rejects_empty_text(self):
        with self.assertRaises(RagError):
            self.rag.add("   ")

    def test_rejects_too_long_text(self):
        with self.assertRaises(RagError):
            self.rag.add("a" * 20_000)

    def test_context_returns_empty_without_matches(self):
        self.assertEqual(self.rag.context("xyz sem nada em comum"), "")

    def test_context_formats_matches(self):
        self.rag.add("backup automático local diário")
        context = self.rag.context("fazer backup", top_k=1)
        self.assertIn("[memória", context)
        self.assertIn("backup automático", context)


if __name__ == "__main__":
    unittest.main()