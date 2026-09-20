"""Keyword map used by the rule engine. EDIT THIS FILE to tune matching.

Each rule code maps to a `RuleTerms` entry with three kinds of terms:

strong  Phrases specific enough that seeing one is good evidence the question is
        about this rule (e.g. "author order", "orcid"). Worth 0.75 each.
weak    Words/phrases that are related but common or ambiguous (e.g. "order",
        "email"). Worth 0.15 each and capped, so weak terms alone can NEVER
        trigger a match; they only add confidence to a strong match.
all_of  Groups of phrases that must ALL appear anywhere in the question, in any
        order (e.g. ("given name", "missing")). Worth the same as a strong term.
        Use these when the words are common but the combination is specific.

Notes
- The rule's own `topic` (from the database) is always matched automatically and
  is worth the most (1.0), so it does not need to be repeated here.
- Terms are normalised like the question is (lower case, punctuation removed,
  plurals folded), so write them in plain lower case: "email id" also matches
  "Email IDs".
- A rule with no entry here is still matched on its topic.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class RuleTerms:
    strong: tuple[str, ...] = ()
    weak: tuple[str, ...] = ()
    all_of: tuple[tuple[str, ...], ...] = ()


RULE_TERMS: dict[str, RuleTerms] = {
    "AUTHOR-001": RuleTerms(
        strong=(
            "multiple given names", "two given names", "three given names",
            "several given names", "more than one given name",
            "multiple first names", "two first names",
        ),
        weak=("given name", "first name", "middle name", "family name", "surname"),
    ),
    "AUTHOR-002": RuleTerms(
        strong=(
            "missing given name", "no given name", "no first name",
            "only one name", "single name", "only a single name",
        ),
        weak=("one name", "complete name", "full name"),
        all_of=(
            ("given name", "missing"),
            ("given name", "not provided"),
            ("given name", "not supplied"),
            ("first name", "missing"),
        ),
    ),
    "AUTHOR-003": RuleTerms(
        strong=("particle name", "particle"),
        weak=("de", "van", "von", "di"),
    ),
    "AUTHOR-004": RuleTerms(
        strong=(
            "number of corresponding authors", "how many corresponding authors",
            "multiple corresponding authors", "more than 5 corresponding authors",
            "more than five corresponding authors", "maximum corresponding authors",
            "corresponding authors limit",
        ),
        weak=("corresponding author",),
    ),
    "AUTHOR-005": RuleTerms(
        strong=(
            "multiple email", "two email addresses", "more than one email",
            "corresponding author email",
        ),
        weak=("email", "email address"),
        all_of=(("corresponding author", "email"),),
    ),
    "AUTHOR-006": RuleTerms(
        strong=(
            "equal contribution", "contributed equally", "equally contributed",
            "equal contributor", "contribution symbol",
        ),
        weak=("contribution", "symbol", "superscript"),
    ),
    "AUTHOR-007": RuleTerms(
        strong=(
            "common particle names", "common particles", "particle list",
            "list of particles", "list of particle names",
            "frequently encountered particle", "van der", "de la",
        ),
        weak=("de", "del", "den", "der", "bin", "ibn", "al", "el"),
    ),
    "AUTHOR-008": RuleTerms(
        strong=("nickname", "nick name", "other name"),
    ),
    "AUTHOR-009": RuleTerms(
        strong=(
            "author order", "order of authors", "change author order",
            "rearrange authors", "reorder authors",
        ),
        weak=("order", "rearrange", "reorder"),
    ),
    "AUTHOR-010": RuleTerms(
        strong=(
            "missing corresponding author", "no corresponding author",
            "corresponding author not mentioned", "corresponding author missing",
        ),
        weak=("corresponding author",),
        all_of=(
            ("corresponding author", "missing"),
            ("corresponding author", "not mentioned"),
            ("corresponding author", "not provided"),
            ("corresponding author", "not supplied"),
        ),
    ),
    "AUTHOR-011": RuleTerms(strong=("snippet",)),
    "AUTHOR-012": RuleTerms(strong=("orcid",)),
    "AUTHOR-013": RuleTerms(
        strong=(
            "all caps", "full caps", "uppercase", "upper case", "capital letters",
            "all capitals", "full capitals",
        ),
        weak=("capital", "caps"),
    ),
    "AUTHOR-014": RuleTerms(
        strong=(
            "swapped", "swap", "swapping", "name order", "family name first",
            "name reversed", "reversed name",
        ),
        weak=("family name", "given name", "reversed"),
    ),
    "AUTHOR-015": RuleTerms(
        strong=("email for every author", "all authors email"),
        weak=("author email", "email id", "email"),
        all_of=(
            ("email", "every author"),
            ("email", "each author"),
            ("email", "all authors"),
            ("email", "required"),
        ),
    ),
    "AUTHOR-016": RuleTerms(
        strong=("missing affiliation", "missing affiliation id"),
        weak=("affiliation id", "affiliation", "author affiliation", "superscript"),
        all_of=(
            ("affiliation", "missing"),
            ("affiliation", "not provided"),
            ("affiliation", "not supplied"),
        ),
    ),
    "AUTHOR-017": RuleTerms(
        strong=("no author group", "without author group"),
        weak=("article type", "author group", "news", "event", "acknowledgement", "abstract"),
        all_of=(
            ("article type", "author group"),
            ("news", "author group"),
            ("event", "author group"),
            ("acknowledgement", "author group"),
            ("abstract", "author group"),
        ),
    ),
    "AUTHOR-018": RuleTerms(
        strong=(
            "multiple family names", "more than two family names",
            "more than one family name", "two family names", "three family names",
            "family name tag",
        ),
        weak=("family name",),
    ),
    "AUTHOR-019": RuleTerms(
        strong=("hyphenated", "hyphen", "double barrelled"),
    ),
    "AUTHOR-020": RuleTerms(
        strong=(
            "abbreviated given name", "abbreviated middle name", "abbreviated name",
            "middle initial", "given name initial",
        ),
        weak=("initial", "abbreviated", "abbreviation", "middle name"),
        all_of=(("initial", "name"),),
    ),
}
