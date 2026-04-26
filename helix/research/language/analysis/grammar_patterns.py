"""
Grammar Patterns
================
Identify grammar structures and dependency patterns in text corpora.

Usage:
    from core.python_suite.language.grammar_patterns import GrammarPatterns
    patterns = GrammarPatterns(language="spanish")
    report = patterns.extract(texts)
"""
from __future__ import annotations

import re
from collections import Counter
from typing import Sequence


class GrammarPatterns:
    """
    Identifies grammar structures from surface features of text.

    Does not require a dependency parser — uses rule-based heuristics
    that work on raw tokenized text. Suitable for corpus statistics
    before introducing heavier NLP tools.

    Patterns extracted:
        - clause boundaries (subordinators, coordinators)
        - question patterns
        - negation patterns
        - determiner + noun phrases
        - common grammatical function word distributions
    """

    # Language-specific function word lists
    _FUNCTION_WORDS: dict[str, dict[str, list[str]]] = {
        "spanish": {
            "articles":         ["el", "la", "los", "las", "un", "una", "unos", "unas"],
            "prepositions":     ["de", "en", "a", "por", "para", "con", "sin", "sobre",
                                 "entre", "hasta", "desde", "hacia"],
            "coordinators":     ["y", "o", "pero", "sino", "ni", "aunque", "porque"],
            "subordinators":    ["que", "cuando", "como", "donde", "si", "aunque",
                                 "mientras", "porque", "después"],
            "negations":        ["no", "nunca", "jamás", "nada", "nadie", "tampoco"],
            "question_words":   ["qué", "cómo", "dónde", "cuándo", "quién", "cuál",
                                 "cuánto"],
            "subject_pronouns": ["yo", "tú", "él", "ella", "nosotros", "vosotros",
                                 "ellos", "ellas", "usted", "ustedes"],
        },
        "english": {
            "articles":         ["the", "a", "an"],
            "prepositions":     ["in", "on", "at", "of", "to", "for", "with",
                                 "by", "from", "about", "as", "into"],
            "coordinators":     ["and", "or", "but", "nor", "so", "yet", "for"],
            "subordinators":    ["that", "when", "because", "if", "although",
                                 "while", "after", "before", "since", "unless"],
            "negations":        ["not", "never", "no", "nothing", "nobody", "neither"],
            "question_words":   ["what", "how", "where", "when", "who", "which",
                                 "why", "whose"],
            "subject_pronouns": ["i", "you", "he", "she", "we", "they", "it"],
        },
        "french": {
            "articles":         ["le", "la", "les", "un", "une", "des", "l"],
            "prepositions":     ["de", "en", "à", "par", "pour", "avec", "sans",
                                 "sur", "dans", "sous", "entre", "chez", "vers"],
            "coordinators":     ["et", "ou", "mais", "ni", "or", "donc", "car"],
            "subordinators":    ["que", "quand", "comme", "où", "si", "bien",
                                 "parce", "pour", "depuis", "après", "avant"],
            "negations":        ["ne", "pas", "jamais", "rien", "personne",
                                 "plus", "aucun", "aucune"],
            "question_words":   ["quoi", "comment", "où", "quand", "qui", "quel",
                                 "quelle", "combien", "pourquoi"],
            "subject_pronouns": ["je", "tu", "il", "elle", "nous", "vous",
                                 "ils", "elles", "on"],
        },
        "italian": {
            "articles":         ["il", "lo", "la", "i", "gli", "le", "un",
                                 "uno", "una", "del", "della", "dei", "degli", "delle"],
            "prepositions":     ["di", "in", "a", "per", "con", "su", "da", "tra", "fra"],
            "coordinators":     ["e", "o", "ma", "né", "però", "eppure", "dunque"],
            "subordinators":    ["che", "quando", "come", "dove", "se", "sebbene",
                                 "perché", "mentre", "dopo"],
            "negations":        ["non", "mai", "niente", "nessuno", "né", "affatto"],
            "question_words":   ["cosa", "come", "dove", "quando", "chi", "quale",
                                 "quanto", "perché"],
            "subject_pronouns": ["io", "tu", "lui", "lei", "noi", "voi", "loro"],
        },
        "portuguese": {
            "articles":         ["o", "a", "os", "as", "um", "uma", "uns", "umas"],
            "prepositions":     ["de", "em", "a", "por", "para", "com", "sem",
                                 "sobre", "entre", "até", "após"],
            "coordinators":     ["e", "ou", "mas", "nem", "pois", "porém", "contudo"],
            "subordinators":    ["que", "quando", "como", "onde", "se", "embora",
                                 "porque", "enquanto", "após"],
            "negations":        ["não", "nunca", "jamais", "nada", "ninguém", "nem"],
            "question_words":   ["que", "como", "onde", "quando", "quem", "qual",
                                 "quanto", "por"],
            "subject_pronouns": ["eu", "tu", "ele", "ela", "nós", "vós",
                                 "eles", "elas", "você", "vocês"],
        },
        "german": {
            "articles":         ["der", "die", "das", "den", "dem", "des",
                                 "ein", "eine", "einen", "einem", "einer", "eines"],
            "prepositions":     ["in", "an", "auf", "von", "mit", "zu", "bei",
                                 "für", "durch", "gegen", "nach", "vor", "über",
                                 "unter", "zwischen", "ab", "aus"],
            "coordinators":     ["und", "oder", "aber", "denn", "noch",
                                 "sondern", "jedoch", "doch"],
            "subordinators":    ["dass", "wenn", "weil", "ob", "als", "obwohl",
                                 "während", "damit", "seit", "nachdem", "bevor"],
            "negations":        ["nicht", "kein", "keine", "nie", "niemals",
                                 "nichts", "niemand", "keinen"],
            "question_words":   ["was", "wie", "wo", "wann", "wer", "welcher",
                                 "welche", "welches", "warum", "woher", "wohin"],
            "subject_pronouns": ["ich", "du", "er", "sie", "es", "wir", "ihr"],
        },
        "russian": {
            "articles":         [],
            "prepositions":     ["в", "на", "с", "по", "за", "от", "до", "при",
                                 "без", "для", "из", "под", "над", "о", "об", "между"],
            "coordinators":     ["и", "или", "но", "ни", "а", "однако", "зато", "либо"],
            "subordinators":    ["что", "когда", "как", "где", "если", "хотя",
                                 "потому", "пока", "чтобы", "который", "которая"],
            "negations":        ["не", "ни", "никогда", "ничего", "никого",
                                 "нет", "нельзя"],
            "question_words":   ["что", "как", "где", "когда", "кто", "какой",
                                 "сколько", "почему", "зачем"],
            "subject_pronouns": ["я", "ты", "он", "она", "оно", "мы", "вы", "они"],
        },
        # CJK note: texts should be space-tokenized (spaces between word units)
        # for the \b\w+\b tokenizer to match function words correctly.
        "mandarin": {
            "articles":         [],
            "prepositions":     ["在", "从", "到", "向", "用", "给", "对", "为", "把", "被"],
            "coordinators":     ["和", "与", "或", "但", "而", "所以", "因此"],
            "subordinators":    ["如果", "虽然", "因为", "当", "即使", "要是", "尽管"],
            "negations":        ["不", "没", "别", "莫", "非"],
            "question_words":   ["什么", "怎么", "哪", "谁", "哪个", "多少", "为什么"],
            "subject_pronouns": ["我", "你", "他", "她", "它", "我们", "你们", "他们"],
        },
        "japanese": {
            "articles":         [],
            "prepositions":     ["は", "が", "を", "に", "で", "から", "まで", "へ", "と", "も", "の"],
            "coordinators":     ["と", "や", "または", "でも", "しかし", "そして", "それから"],
            "subordinators":    ["から", "ので", "けど", "が", "たら", "ば", "ながら"],
            "negations":        ["ない", "ません", "じゃない", "ではない", "なかった"],
            "question_words":   ["何", "どう", "どこ", "いつ", "誰", "どの", "いくら", "なぜ"],
            "subject_pronouns": ["私", "あなた", "彼", "彼女", "私たち", "彼ら"],
        },
        "korean": {
            "articles":         [],
            "prepositions":     ["은", "는", "이", "가", "을", "를", "에", "에서",
                                 "로", "와", "과", "도", "의", "한테", "에게"],
            "coordinators":     ["와", "과", "그리고", "또는", "하지만", "그러나", "그래서"],
            "subordinators":    ["때문에", "면", "지만", "는데", "아서", "어서", "고", "려고"],
            "negations":        ["안", "못", "않", "없", "아니", "아니다"],
            "question_words":   ["뭐", "어떻게", "어디", "언제", "누구", "어느", "얼마", "왜"],
            "subject_pronouns": ["나", "저", "너", "그", "그녀", "우리", "그들"],
        },
        "arabic": {
            "articles":         ["ال"],
            "prepositions":     ["في", "من", "إلى", "على", "عن", "مع", "بين",
                                 "تحت", "فوق", "قبل", "بعد", "عند"],
            "coordinators":     ["و", "أو", "لكن", "بل", "أما", "ولا"],
            "subordinators":    ["أن", "إن", "لما", "حين", "إذا", "لأن",
                                 "حتى", "كي", "الذي", "التي", "الذين"],
            "negations":        ["لا", "ليس", "لم", "لن", "ما", "لات"],
            "question_words":   ["ما", "ماذا", "كيف", "أين", "متى", "من", "كم", "لماذا"],
            "subject_pronouns": ["أنا", "أنت", "أنتِ", "هو", "هي", "نحن", "أنتم", "هم"],
        },
        "turkish": {
            "articles":         [],
            "prepositions":     ["ile", "için", "gibi", "kadar", "göre", "karşı",
                                 "önce", "sonra", "beri", "doğru", "hakkında"],
            "coordinators":     ["ve", "veya", "ama", "fakat", "hem", "ya", "da",
                                 "de", "ki", "ne", "ancak"],
            "subordinators":    ["ki", "çünkü", "eğer", "ise", "diye", "zira",
                                 "oysa", "gerçi", "sanki", "madem"],
            "negations":        ["değil", "yok", "hiç", "hiçbir", "asla",
                                 "hayır", "olmaz"],
            "question_words":   ["ne", "nasıl", "nerede", "neden", "kim",
                                 "hangi", "kaç", "niçin", "niye"],
            "subject_pronouns": ["ben", "sen", "o", "biz", "siz", "onlar"],
        },
        "finnish": {
            "articles":         [],
            "prepositions":     ["kanssa", "ilman", "aikana", "jälkeen", "ennen",
                                 "välillä", "alla", "päällä", "lähellä", "takana",
                                 "edessä", "vieressä", "mukaan"],
            "coordinators":     ["ja", "tai", "mutta", "sekä", "vaan", "eli",
                                 "joko", "sekä"],
            "subordinators":    ["että", "kun", "koska", "jos", "vaikka", "jotta",
                                 "joten", "kuin", "kunnes", "jollei"],
            "negations":        ["ei", "en", "et", "emme", "ette", "eivät",
                                 "eikä", "älä", "ellei"],
            "question_words":   ["mitä", "miten", "missä", "milloin", "kuka",
                                 "mikä", "kuinka", "miksi", "kuinka"],
            "subject_pronouns": ["minä", "sinä", "hän", "me", "te", "he",
                                 "se", "ne"],
        },
        "indonesian": {
            "articles":         [],
            "prepositions":     ["di", "ke", "dari", "pada", "untuk", "dengan",
                                 "oleh", "tentang", "antara", "sebelum",
                                 "sesudah", "selama", "terhadap"],
            "coordinators":     ["dan", "atau", "tapi", "tetapi", "namun",
                                 "serta", "maupun", "baik", "melainkan"],
            "subordinators":    ["bahwa", "ketika", "karena", "jika", "kalau",
                                 "meskipun", "agar", "supaya", "sejak",
                                 "walaupun", "setelah", "sebelum"],
            "negations":        ["tidak", "bukan", "jangan", "belum", "tak",
                                 "tanpa"],
            "question_words":   ["apa", "bagaimana", "mana", "kapan", "siapa",
                                 "berapa", "mengapa", "kenapa"],
            "subject_pronouns": ["saya", "aku", "kamu", "anda", "dia", "ia",
                                 "kami", "kita", "mereka"],
        },
        "tagalog": {
            "articles":         ["ang", "si", "mga", "sina"],
            "prepositions":     ["sa", "ng", "para", "mula", "tungkol",
                                 "kasama", "pagkatapos", "bago", "habang"],
            "coordinators":     ["at", "o", "pero", "ngunit", "kundi", "ni",
                                 "pati", "kahit"],
            "subordinators":    ["na", "kung", "dahil", "habang", "kapag",
                                 "upang", "bago", "pagkatapos", "kahit"],
            "negations":        ["hindi", "wala", "huwag", "walang", "di"],
            "question_words":   ["ano", "paano", "saan", "kailan", "sino",
                                 "ilan", "bakit", "alin"],
            "subject_pronouns": ["ako", "ikaw", "ka", "siya", "kami",
                                 "tayo", "kayo", "sila"],
        },
        "hindi": {
            "articles":         [],
            "prepositions":     ["में", "पर", "से", "को", "के", "की", "का",
                                 "तक", "साथ", "लिए", "बाद", "पहले", "पास"],
            "coordinators":     ["और", "या", "लेकिन", "किंतु", "परन्तु", "तथा", "अथवा"],
            "subordinators":    ["कि", "जब", "जैसे", "जहाँ", "अगर", "हालांकि",
                                 "क्योंकि", "जबकि", "यदि"],
            "negations":        ["नहीं", "मत", "न", "ना"],
            "question_words":   ["क्या", "कैसे", "कहाँ", "कब", "कौन", "कितना", "क्यों"],
            "subject_pronouns": ["मैं", "तुम", "आप", "वह", "वे", "हम", "यह", "ये"],
        },
    }

    def __init__(self, language: str = "unknown"):
        self.language = language.lower()
        self._fw = self._FUNCTION_WORDS.get(self.language, {})

    def extract(self, texts: Sequence[str]) -> dict:
        """Run all grammar pattern extractors on a text corpus."""
        tokenized = [self._tokenize(t) for t in texts]
        return {
            "language":             self.language,
            "sample_count":         len(texts),
            "function_word_dist":   self.function_word_distribution(tokenized),
            "clause_types":         self.clause_type_distribution(tokenized),
            "sentence_types":       self.sentence_type_distribution(texts),
            "negation_rate":        self.negation_rate(tokenized),
            "pro_drop_evidence":    self.pro_drop_evidence(tokenized),
            "top_frames":           self.top_sentence_frames(tokenized),
        }

    # ── Extractors ────────────────────────────────────────────────────────────

    def function_word_distribution(self, tokenized: list[list[str]]) -> dict:
        """Count occurrences of each grammatical category's function words."""
        all_tokens = [t for sent in tokenized for t in sent]
        total = len(all_tokens) or 1
        result = {}
        for category, words in self._fw.items():
            count = sum(all_tokens.count(w) for w in words)
            result[category] = {
                "count": count,
                "rate":  round(count / total, 4),
            }
        return result

    def clause_type_distribution(self, tokenized: list[list[str]]) -> dict:
        """Count subordinate vs coordinate clause markers."""
        subs = self._fw.get("subordinators", [])
        coords = self._fw.get("coordinators", [])
        sub_count = coord_count = 0
        for sent in tokenized:
            sub_count   += sum(1 for t in sent if t in subs)
            coord_count += sum(1 for t in sent if t in coords)
        total = sub_count + coord_count or 1
        return {
            "subordinate":  {"count": sub_count,   "ratio": round(sub_count / total, 4)},
            "coordinate":   {"count": coord_count, "ratio": round(coord_count / total, 4)},
            "sub_to_coord": round(sub_count / (coord_count or 1), 4),
        }

    def sentence_type_distribution(self, texts: Sequence[str]) -> dict:
        """Classify sentences as declarative, interrogative, or exclamatory."""
        counts = Counter()
        for text in texts:
            stripped = text.strip()
            if stripped.endswith("?") or stripped.startswith("¿"):
                counts["interrogative"] += 1
            elif stripped.endswith("!") or stripped.startswith("¡"):
                counts["exclamatory"] += 1
            else:
                counts["declarative"] += 1
        total = len(texts) or 1
        return {k: {"count": v, "ratio": round(v / total, 4)} for k, v in counts.items()}

    def negation_rate(self, tokenized: list[list[str]]) -> float:
        """Fraction of sentences containing at least one negation marker."""
        neg_words = self._fw.get("negations", [])
        if not neg_words or not tokenized:
            return 0.0
        neg_sents = sum(1 for sent in tokenized if any(t in neg_words for t in sent))
        return round(neg_sents / len(tokenized), 4)

    def pro_drop_evidence(self, tokenized: list[list[str]]) -> dict:
        """
        Evidence for pro-drop: compare explicit subject pronoun rate.
        High rate → subject pronouns usually explicit (English-like).
        Low rate  → pro-drop likely (Spanish-like for many contexts).
        """
        pronouns = self._fw.get("subject_pronouns", [])
        if not pronouns or not tokenized:
            return {}
        pronoun_sents = sum(
            1 for sent in tokenized if any(t in pronouns for t in sent)
        )
        rate = round(pronoun_sents / len(tokenized), 4)
        return {
            "pronoun_sentence_rate": rate,
            "pro_drop_likely": rate < 0.5,
        }

    @staticmethod
    def top_sentence_frames(
        tokenized: list[list[str]], top_n: int = 20
    ) -> list[tuple[str, int]]:
        """
        Extract the most common 3-token sentence frames (first 3 tokens).
        Reveals dominant syntactic construction patterns.
        """
        frames: Counter = Counter()
        for sent in tokenized:
            if len(sent) >= 3:
                frames[" ".join(sent[:3])] += 1
        return frames.most_common(top_n)

    # ── Helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        return re.findall(r"\b\w+\b", text.lower())
