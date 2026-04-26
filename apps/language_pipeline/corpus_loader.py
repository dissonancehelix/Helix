"""
Corpus Loader
=============
Resolve language corpora from the repository's canonical fixture paths.

Supports:
    - folder corpora: ``{language}_{corpus}/``
    - direct files:  ``{language}_{corpus}.json`` or ``{corpus}.json``
    - JSON lists of strings or records with a ``text`` field
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Iterator

REPO_ROOT = Path(__file__).resolve().parents[3]

_DEFAULT_ROOTS: tuple[Path, ...] = (
    REPO_ROOT / "domains" / "language" / "data" / "corpus",
    REPO_ROOT / "domains" / "language" / "data" / "datasets",
)

_TEXT_KEYS: tuple[str, ...] = ("text", "sentence", "utterance", "content")


class CorpusLoader:
    """
    Resolves and loads text corpora from the repo's canonical fixture roots.
    """

    def __init__(self, corpus_root: Path | str | None = None):
        if corpus_root:
            self.roots = (Path(corpus_root),)
        else:
            self.roots = _DEFAULT_ROOTS

    # ── Public API ────────────────────────────────────────────────────────────

    def load(self, language: str, corpus: str, max_samples: int | None = None) -> list[str]:
        """
        Load text samples for a given language/corpus.
        """
        records = self.load_records(language=language, corpus=corpus, max_samples=max_samples)
        return [record["text"] for record in records if record.get("text")]

    def load_records(
        self, language: str, corpus: str, max_samples: int | None = None
    ) -> list[dict]:
        """
        Load a corpus and preserve record metadata when available.

        Normalized record shape:
            {"id": str, "text": str, "language": str, ...}
        """
        source = self._resolve_source(language, corpus)
        records = list(self._iter_records(source, language=language))
        if max_samples is not None:
            records = records[:max_samples]
        return records

    def list_corpora(self) -> list[dict]:
        """Return available corpora as [{language, corpus, path, file_count}]."""
        result = []
        for root in self.roots:
            if not root.exists():
                continue
            for entry in sorted(root.iterdir()):
                if entry.is_dir() and "_" in entry.name:
                    lang, _, corp = entry.name.partition("_")
                    files = [f for f in entry.iterdir() if f.suffix in (".txt", ".json", ".jsonl")]
                    result.append({
                        "language": lang,
                        "corpus": corp,
                        "path": str(entry),
                        "file_count": len(files),
                    })
                    continue

                if entry.is_file() and entry.suffix in (".txt", ".json", ".jsonl"):
                    stem = entry.stem
                    if "_" in stem:
                        lang, _, corp = stem.partition("_")
                    else:
                        lang, corp = "unknown", stem
                    result.append({
                        "language": lang,
                        "corpus": corp,
                        "path": str(entry),
                        "file_count": 1,
                    })
        return result

    def corpus_stats(self, language: str, corpus: str) -> dict:
        """Return basic statistics for a corpus."""
        samples = self.load(language=language, corpus=corpus)
        if not samples:
            return {"count": 0, "avg_length": 0, "total_tokens": 0}
        lengths = [len(s.split()) for s in samples]
        return {
            "count":        len(samples),
            "avg_length":   sum(lengths) / len(lengths),
            "total_tokens": sum(lengths),
        }

    # ── Internal ──────────────────────────────────────────────────────────────

    def _resolve_source(self, language: str, corpus: str) -> Path:
        lang = language.lower()
        corp = corpus.lower()

        candidates: list[Path] = []
        for root in self.roots:
            candidates.extend((
                root / f"{lang}_{corp}",
                root / f"{lang}_{corp}.json",
                root / f"{lang}_{corp}.jsonl",
                root / f"{lang}_{corp}.txt",
                root / f"{corp}.json",
                root / f"{corp}.jsonl",
                root / f"{corp}.txt",
            ))

        for candidate in candidates:
            if candidate.exists():
                return candidate

        available: list[str] = []
        for root in self.roots:
            if root.exists():
                available.extend(sorted(entry.name for entry in root.iterdir()))

        raise FileNotFoundError(
            f"Corpus not found for language={lang!r} corpus={corp!r}\n"
            f"Available: {available}\n"
            f"Searched roots: {[str(root) for root in self.roots]}"
        )

    def _iter_records(self, source: Path, language: str) -> Iterator[dict]:
        if source.is_dir():
            index = 0
            for path in sorted(source.iterdir()):
                if path.suffix == ".txt":
                    for text in self._load_txt(path):
                        index += 1
                        yield {
                            "id": f"{path.stem}_{index:03d}",
                            "text": text,
                            "language": language.lower(),
                            "source_path": str(path),
                        }
                elif path.suffix == ".json":
                    yield from self._load_json_records(path, language=language)
                elif path.suffix == ".jsonl":
                    yield from self._load_jsonl_records(path, language=language)
            return

        if source.suffix == ".txt":
            for index, text in enumerate(self._load_txt(source), 1):
                yield {
                    "id": f"{source.stem}_{index:03d}",
                    "text": text,
                    "language": language.lower(),
                    "source_path": str(source),
                }
            return

        if source.suffix == ".json":
            yield from self._load_json_records(source, language=language)
            return

        if source.suffix == ".jsonl":
            yield from self._load_jsonl_records(source, language=language)
            return

    @staticmethod
    def _load_txt(path: Path) -> Iterator[str]:
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    yield line

    def _load_json_records(self, path: Path, language: str) -> Iterator[dict]:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            for index, item in enumerate(data, 1):
                if isinstance(item, str):
                    yield {
                        "id": f"{path.stem}_{index:03d}",
                        "text": item,
                        "language": language.lower(),
                        "source_path": str(path),
                    }
                elif isinstance(item, dict):
                    text = None
                    for key in _TEXT_KEYS:
                        if key in item:
                            text = str(item[key])
                            break
                    if text:
                        record = dict(item)
                        record.setdefault("id", f"{path.stem}_{index:03d}")
                        record["text"] = text
                        record.setdefault("language", language.lower())
                        record.setdefault("source_path", str(path))
                        yield record

    def _load_jsonl_records(self, path: Path, language: str) -> Iterator[dict]:
        with open(path, encoding="utf-8") as f:
            for index, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                obj = json.loads(line)
                for key in _TEXT_KEYS:
                    if key in obj:
                        record = dict(obj)
                        record.setdefault("id", f"{path.stem}_{index:03d}")
                        record["text"] = str(obj[key])
                        record.setdefault("language", language.lower())
                        record.setdefault("source_path", str(path))
                        yield record
                        break
