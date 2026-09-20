"""Deterministic rule matching. No LLM, no embeddings, no database access.

Given a trainee's question and a list of rules, decide which rule (if any)
the question is about.

How it works
1. Normalise the question (lower case, punctuation and the/a/an removed, plurals folded).
2. For every rule, find which of its terms appear in the question:
     - the rule's own topic ............ TOPIC_WEIGHT  (1.0)
     - "strong" phrases / all_of groups . STRONG_WEIGHT (0.75)
     - "weak" words .................... WEAK_WEIGHT   (0.15 each, capped)
   The terms come from rule_keywords.py.
3. A phrase is ignored if another rule matched a longer phrase that contains it
   ("common particle names" beats "particle names"). Within one rule the same
   words are never counted twice.
4. Sum the weights to get each rule's score.
5. Decide:
     - best score below MIN_SCORE ................. NO_MATCH
     - runner-up also >= MIN_SCORE and within
       AMBIGUITY_RATIO of the best score ........... AMBIGUOUS
     - otherwise ................................... MATCHED (best rule)
"""
import re
from dataclasses import dataclass
from enum import Enum
from typing import Sequence

from app.models import Rule
from app.services.rule_keywords import RULE_TERMS

TOPIC_WEIGHT = 1.0
STRONG_WEIGHT = 0.75
WEAK_WEIGHT = 0.15
WEAK_CAP = 0.3  # weak terms alone must stay below MIN_SCORE
MIN_SCORE = 0.5
AMBIGUITY_RATIO = 0.7  # runner-up >= 70% of the best score => ambiguous
MAX_CONFIDENCE = 0.95  # keyword matching is never certain

_IRREGULAR_SINGULARS = {"ids": "id"}
# Ignored when comparing, so "reorder the authors" still matches "reorder authors".
_ARTICLES = {"the", "a", "an"}


class MatchStatus(str, Enum):
    MATCHED = "matched"
    NO_MATCH = "no_match"
    AMBIGUOUS = "ambiguous"


@dataclass(frozen=True)
class Candidate:
    rule: Rule
    score: float
    matched_terms: tuple[str, ...]


@dataclass(frozen=True)
class MatchResult:
    status: MatchStatus
    best: Candidate | None  # set when MATCHED
    candidates: tuple[Candidate, ...]  # set when AMBIGUOUS (the rules that tie)
    confidence: float  # 0.0 unless MATCHED
    normalized_question: str


@dataclass(frozen=True)
class _Hit:
    """One term found in the question. `spans` are (start, end) token ranges."""

    rule: Rule
    label: str
    weight: float
    spans: tuple[tuple[int, int], ...]

    @property
    def is_contiguous(self) -> bool:
        return len(self.spans) == 1

    @property
    def is_strong(self) -> bool:
        return self.weight >= STRONG_WEIGHT

    def tokens(self) -> set[int]:
        return {i for start, end in self.spans for i in range(start, end)}


# ---------------------------------------------------------------- normalising


def _singular(token: str) -> str:
    if token in _IRREGULAR_SINGULARS:
        return _IRREGULAR_SINGULARS[token]
    if len(token) > 4 and token.endswith("s") and not token.endswith("ss"):
        return token[:-1]
    return token


@dataclass(frozen=True)
class _Question:
    raw: list[str]  # words as typed (lower case) - used to show what matched
    tokens: list[str]  # plurals folded - used for comparing

    def text(self, start: int, end: int) -> str:
        return " ".join(self.raw[start:end])


def _parse(text: str) -> _Question:
    """Lower-case, strip punctuation and articles, fold plurals: "The Author's Emails?" -> author / email."""
    text = text.lower().replace("\u2019", "'")
    text = re.sub(r"'s\b", "", text)  # possessive: author's -> author
    text = text.replace("'", "")  # don't -> dont
    text = re.sub(r"[^a-z0-9]+", " ", text)  # hyphens and other punctuation -> space
    raw = _merge_email([w for w in text.split() if w not in _ARTICLES])
    return _Question(raw=raw, tokens=[_singular(t) for t in raw])


def tokenize(text: str) -> list[str]:
    return _parse(text).tokens


def _merge_email(words: list[str]) -> list[str]:
    """Treat "e-mail" (split into e, mail) the same as "email"."""
    merged: list[str] = []
    for word in words:
        if word in ("mail", "mails") and merged and merged[-1] == "e":
            merged[-1] = "email" if word == "mail" else "emails"
        else:
            merged.append(word)
    return merged


def normalize_question(text: str) -> str:
    return " ".join(tokenize(text))


# ------------------------------------------------------------------- matching


def _find_phrase(phrase_tokens: list[str], question_tokens: list[str]) -> list[tuple[int, int]]:
    """All places where the phrase appears as consecutive tokens."""
    size = len(phrase_tokens)
    if size == 0:
        return []
    return [
        (i, i + size)
        for i in range(len(question_tokens) - size + 1)
        if question_tokens[i : i + size] == phrase_tokens
    ]


def _phrase_hits(rule: Rule, phrase: str, weight: float, question: _Question) -> list[_Hit]:
    return [
        _Hit(rule, question.text(*span), weight, (span,))
        for span in _find_phrase(tokenize(phrase), question.tokens)
    ]


def _group_hit(rule: Rule, group: tuple[str, ...], question: _Question) -> _Hit | None:
    """An all_of group matches only if every part is present."""
    spans = []
    for part in group:
        found = _find_phrase(tokenize(part), question.tokens)
        if not found:
            return None
        spans.append(found[0])
    label = " + ".join(question.text(*span) for span in spans)
    return _Hit(rule, label, STRONG_WEIGHT, tuple(spans))


def _collect_hits(rule: Rule, question: _Question) -> list[_Hit]:
    terms = RULE_TERMS.get(rule.rule_code)
    hits = _phrase_hits(rule, rule.topic, TOPIC_WEIGHT, question)
    if terms is None:
        return hits
    for phrase in terms.strong:
        hits += _phrase_hits(rule, phrase, STRONG_WEIGHT, question)
    for phrase in terms.weak:
        hits += _phrase_hits(rule, phrase, WEAK_WEIGHT, question)
    for group in terms.all_of:
        group_hit = _group_hit(rule, group, question)
        if group_hit:
            hits.append(group_hit)
    return hits


def _remove_shadowed(hits: list[_Hit]) -> list[_Hit]:
    """Drop a hit when another rule matched a longer, strong phrase containing it."""
    shadowers = [h for h in hits if h.is_contiguous and h.is_strong]
    kept = []
    for hit in hits:
        if hit.is_contiguous and _is_shadowed(hit, shadowers):
            continue
        kept.append(hit)
    return kept


def _is_shadowed(hit: _Hit, shadowers: list[_Hit]) -> bool:
    start, end = hit.spans[0]
    for other in shadowers:
        if other.rule.rule_code == hit.rule.rule_code:
            continue
        o_start, o_end = other.spans[0]
        contains = o_start <= start and end <= o_end
        if contains and (o_end - o_start) > (end - start):
            return True
    return False


def _score_rule(hits: list[_Hit]) -> tuple[float, tuple[str, ...]]:
    """Add up a rule's hits, never counting the same words twice."""
    used: set[int] = set()
    labels: list[str] = []
    strong_total = 0.0
    weak_total = 0.0
    # Highest weight first, then the longest match, so specific terms win.
    ordered = sorted(hits, key=lambda h: (-h.weight, -len(h.tokens())))
    for hit in ordered:
        tokens = hit.tokens()
        if tokens & used:
            continue
        used |= tokens
        labels.append(hit.label)
        if hit.is_strong:
            strong_total += hit.weight
        else:
            weak_total += hit.weight
    return strong_total + min(weak_total, WEAK_CAP), tuple(labels)


def score_rules(question: str, rules: Sequence[Rule]) -> list[Candidate]:
    """Score every rule against the question, best first. Rules with score 0 are omitted."""
    parsed = _parse(question)
    all_hits = [hit for rule in rules for hit in _collect_hits(rule, parsed)]
    hits_by_code: dict[str, list[_Hit]] = {}
    for hit in _remove_shadowed(all_hits):
        hits_by_code.setdefault(hit.rule.rule_code, []).append(hit)

    rules_by_code = {r.rule_code: r for r in rules}
    candidates = []
    for code, hits in hits_by_code.items():
        score, labels = _score_rule(hits)
        if score > 0:
            candidates.append(Candidate(rules_by_code[code], round(score, 2), labels))
    return sorted(candidates, key=lambda c: (-c.score, c.rule.rule_code))


def match_question(question: str, rules: Sequence[Rule]) -> MatchResult:
    """Find the rule a question is about, or say that no rule (or several) apply."""
    normalized = normalize_question(question)
    candidates = score_rules(question, rules)

    if not candidates or candidates[0].score < MIN_SCORE:
        return MatchResult(MatchStatus.NO_MATCH, None, (), 0.0, normalized)

    best = candidates[0]
    close = tuple(
        c for c in candidates if c.score >= MIN_SCORE and c.score >= best.score * AMBIGUITY_RATIO
    )
    if len(close) > 1:
        return MatchResult(MatchStatus.AMBIGUOUS, None, close, 0.0, normalized)

    confidence = round(min(best.score, MAX_CONFIDENCE), 2)
    return MatchResult(MatchStatus.MATCHED, best, (), confidence, normalized)
