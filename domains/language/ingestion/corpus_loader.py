"""
Corpus Loader
=============
Load text datasets from labs/cognition/language/corpus/.

Usage:
    from core.python_suite.language.corpus_loader import CorpusLoader
    loader = CorpusLoader()
    texts = loader.load(language="spanish", corpus="podcasts")
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Iterator

# Corpus root relative to repo root
_CORPUS_ROOT = Path(__file__).resolve().parents[3] / "labs" / "cognition" / "language" / "corpus"

# Supported corpus folder naming convention: {language}_{corpus_name}
_FOLDER_PATTERN = "{language}_{corpus}"


class CorpusLoader:
    """
    Resolves and loads text corpora from the language corpus directory.

    Corpus folders follow the naming convention:
        corpus/{language}_{corpus_name}/

    Each folder may contain:
        - .txt files  (one sentence or line per entry)
        - .json files (list of strings, or list of {text, ...} dicts)
        - .jsonl files (one JSON object per line with a "text" field)
    """

    def __init__(self, corpus_root: Path | str | None = None):
        self.root = Path(corpus_root) if corpus_root else _CORPUS_ROOT

    # ── Public API ────────────────────────────────────────────────────────────

    def load(self, language: str, corpus: str, max_samples: int | None = None) -> list[str]:
        """
        Load text samples for a given language and corpus name.

        Returns a flat list of strings (sentences / utterances).
        Raises FileNotFoundError if the corpus directory does not exist.
        """
        folder = self._resolve_folder(language, corpus)
        samples = list(self._iter_texts(folder))
        if max_samples:
            samples = samples[:max_samples]
        return samples

    def list_corpora(self) -> list[dict]:
        """Return available corpora as [{language, corpus, path, file_count}]."""
        result = []
        if not self.root.exists():
            return result
        for entry in sorted(self.root.iterdir()):
            if entry.is_dir() and "_" in entry.name:
                lang, _, corp = entry.name.partition("_")
                files = [f for f in entry.iterdir() if f.suffix in (".txt", ".json", ".jsonl")]
                result.append({
                    "language":   lang,
                    "corpus":     corp,
                    "path":       str(entry),
                    "file_count": len(files),
                })
        return result

    def corpus_stats(self, language: str, corpus: str) -> dict:
        """Return basic statistics for a corpus."""
        folder = self._resolve_folder(language, corpus)
        samples = list(self._iter_texts(folder))
        if not samples:
            return {"count": 0, "avg_length": 0, "total_tokens": 0}
        lengths = [len(s.split()) for s in samples]
        return {
            "count":        len(samples),
            "avg_length":   sum(lengths) / len(lengths),
            "total_tokens": sum(lengths),
        }

    # ── Internal ──────────────────────────────────────────────────────────────

    def _resolve_folder(self, language: str, corpus: str) -> Path:
        folder_name = _FOLDER_PATTERN.format(language=language.lower(), corpus=corpus.lower())
        folder = self.root / folder_name
        if not folder.exists():
            available = [d.name for d in self.root.iterdir() if d.is_dir()] if self.root.exists() else []
            raise FileNotFoundError(
                f"Corpus not found: '{folder_name}'\n"
                f"Available: {available}\n"
                f"Add data to: {folder}"
            )
        return folder

    def _iter_texts(self, folder: Path) -> Iterator[str]:
        for path in sorted(folder.iterdir()):
            if path.suffix == ".txt":
                yield from self._load_txt(path)
            elif path.suffix == ".json":
                yield from self._load_json(path)
            elif path.suffix == ".jsonl":
                yield from self._load_jsonl(path)

    @staticmethod
    def _load_txt(path: Path) -> Iterator[str]:
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    yield line

    @staticmethod
    def _load_json(path: Path) -> Iterator[str]:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            for item in data:
                if isinstance(item, str):
                    yield item
                elif isinstance(item, dict):
                    for key in ("text", "sentence", "utterance", "content"):
                        if key in item:
                            yield str(item[key])
                            break

    @staticmethod
    def _load_jsonl(path: Path) -> Iterator[str]:
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                obj = json.loads(line)
                for key in ("text", "sentence", "utterance", "content"):
                    if key in obj:
                        yield str(obj[key])
                        break
