"""Unit tests for the rule engine and answer builder. No database, no HTTP."""
import pytest

from app.services import answer_builder
from app.services.rule_engine import MatchStatus, match_question, normalize_question, score_rules

# The rules whose stored `escalation` field asks for a query / lead confirmation.
RULES_WITH_ESCALATION = {"AUTHOR-002", "AUTHOR-004", "AUTHOR-009", "AUTHOR-010", "AUTHOR-016"}

# (question, expected rule code) - one representative question per rule.
INTENT_CASES = [
    ("How should I process an author with multiple given names?", "AUTHOR-001"),
    ("What should I do if the author's given name is missing?", "AUTHOR-002"),
    ("What is a particle name in an author name?", "AUTHOR-003"),
    ("How many corresponding authors can there be?", "AUTHOR-004"),
    ("Can a corresponding author have multiple email IDs?", "AUTHOR-005"),
    ("How do I process equal contribution?", "AUTHOR-006"),
    ("What are common particle names?", "AUTHOR-007"),
    ("How should I tag a nickname?", "AUTHOR-008"),
    ("Can I change the author order?", "AUTHOR-009"),
    ("What if no corresponding author is mentioned?", "AUTHOR-010"),
    ("What is a snippet?", "AUTHOR-011"),
    ("Can I process ORCID for all authors?", "AUTHOR-012"),
    ("What should I do if the author name is in all caps?", "AUTHOR-013"),
    ("What if the given and family names are swapped?", "AUTHOR-014"),
    ("Does every author need an email ID?", "AUTHOR-015"),
    ("What if an author's affiliation ID is missing?", "AUTHOR-016"),
    ("Which article types don't need an author group?", "AUTHOR-017"),
    ("How should I process more than two family names?", "AUTHOR-018"),
    ("How should I handle a hyphenated author name?", "AUTHOR-019"),
    ("What should I do with an abbreviated middle name?", "AUTHOR-020"),
]


def test_intent_cases_cover_all_twenty_rules():
    assert len({code for _, code in INTENT_CASES}) == 20


@pytest.mark.parametrize("question, expected_code", INTENT_CASES)
def test_question_matches_expected_rule(rules, seed_items, question, expected_code):
    result = match_question(question, rules)

    assert result.status == MatchStatus.MATCHED
    assert result.best.rule.rule_code == expected_code
    assert 0.5 <= result.confidence <= 0.95

    answer = answer_builder.build_answer(result)
    seed = seed_items[expected_code]
    assert answer.matched is True
    assert answer.rule_code == expected_code
    assert answer.decision == seed["rule_text"]  # the decision is the stored rule, unchanged
    assert answer.source == "Initial team guidance"
    assert answer.status == "draft"
    assert "not yet been confirmed" in answer.status_notice
    assert answer.escalation_required is (expected_code in RULES_WITH_ESCALATION)
    assert (answer.escalation_reason is not None) is (expected_code in RULES_WITH_ESCALATION)


def test_action_comes_from_rule_when_stored_otherwise_generic(rules, seed_items):
    stored = answer_builder.build_answer(match_question("Can I change the author order?", rules))
    assert stored.action == seed_items["AUTHOR-009"]["action"]
    assert stored.action != stored.decision  # decision and action are kept separate

    generic = answer_builder.build_answer(match_question("What is a snippet?", rules))
    assert generic.action == answer_builder.DEFAULT_ACTION


def test_escalation_reason_quotes_the_rule_field(rules, seed_items):
    answer = answer_builder.build_answer(
        match_question("How many corresponding authors can there be?", rules)
    )
    assert answer.escalation_required is True
    assert "requires a query/lead confirmation" in answer.escalation_reason
    assert seed_items["AUTHOR-004"]["escalation"] in answer.escalation_reason


# ------------------------------------------------------------------ no match


@pytest.mark.parametrize(
    "question",
    [
        "What is the weather today?",
        "How do I format a reference?",
        "How do I edit an image?",
        "What is the capital of France?",
        "Hello",
        "???",
    ],
)
def test_unrelated_questions_do_not_match(rules, question):
    result = match_question(question, rules)
    assert result.status == MatchStatus.NO_MATCH
    assert result.best is None
    assert result.confidence == 0.0

    answer = answer_builder.build_answer(result)
    assert answer.matched is False
    assert answer.decision == "No approved rule matched this question."
    assert answer.action == "Please check the style manual or raise the question with a lead."
    assert answer.reason == "No sufficiently relevant rule was found."
    assert answer.escalation_required is True  # the system could not identify a rule
    assert answer.rule_code is None and answer.source is None


@pytest.mark.parametrize(
    "question",
    [
        "How do I tag an author's affiliation?",  # related words only
        "Where does the abstract go?",
        "What does de mean?",
        "How should I process an author name?",  # too general to pick a rule
    ],
)
def test_weak_keywords_alone_never_trigger_a_match(rules, question):
    assert match_question(question, rules).status == MatchStatus.NO_MATCH


def test_weak_terms_alone_can_never_reach_the_threshold(rules):
    # Many weak AUTHOR-017 words at once (news, events, abstract, acknowledgements)
    # add up to at most the weak cap, which is below the match threshold.
    text = "news events abstract acknowledgements"
    scores = {c.rule.rule_code: c.score for c in score_rules(text, rules)}
    assert scores["AUTHOR-017"] == 0.3
    assert match_question(text, rules).status == MatchStatus.NO_MATCH


# ----------------------------------------------------------------- ambiguity


@pytest.mark.parametrize(
    "question, expected_codes",
    [
        ("Is 'van der' a particle name?", {"AUTHOR-003", "AUTHOR-007"}),
        (
            "Does the corresponding author need multiple email IDs when there are "
            "more than 5 corresponding authors?",
            {"AUTHOR-004", "AUTHOR-005"},
        ),
        (
            "The given and family names are swapped and there are multiple given names",
            {"AUTHOR-001", "AUTHOR-014"},
        ),
        ("The corresponding author's affiliation ID is missing", {"AUTHOR-010", "AUTHOR-016"}),
    ],
)
def test_overlapping_topics_are_ambiguous(rules, question, expected_codes):
    result = match_question(question, rules)
    assert result.status == MatchStatus.AMBIGUOUS
    assert result.best is None
    assert {c.rule.rule_code for c in result.candidates} == expected_codes

    answer = answer_builder.build_answer(result)
    assert answer.matched is False
    assert answer.match_status == "ambiguous"
    assert answer.decision.startswith("Multiple rules may apply.")
    assert answer.escalation_required is True
    assert {c.rule_code for c in answer.candidates} == expected_codes
    assert answer.rule_code is None  # it does not guess between them


def test_more_specific_phrase_beats_general_one(rules):
    # "common particle names" (AUTHOR-007) must win over "particle names" (AUTHOR-003).
    result = match_question("What are common particle names?", rules)
    assert result.best.rule.rule_code == "AUTHOR-007"
    # ...while the general question still goes to AUTHOR-003.
    assert match_question("What is a particle name?", rules).best.rule.rule_code == "AUTHOR-003"


def test_clearly_stronger_rule_wins_over_a_weak_overlap(rules):
    result = match_question("How many corresponding authors are allowed?", rules)
    assert result.status == MatchStatus.MATCHED
    assert result.best.rule.rule_code == "AUTHOR-004"


# ------------------------------------------------------------ normalisation


def test_normalisation_handles_case_whitespace_punctuation_and_plurals():
    assert normalize_question("  Can a Corresponding   Author's E-mails, be  ok?? ") == (
        "can corresponding author email be ok"
    )
    assert normalize_question("Double-barrelled NAME") == "double barrelled name"
    assert normalize_question("email IDs") == "email id"


@pytest.mark.parametrize(
    "question",
    ["CAN I CHANGE THE AUTHOR ORDER???", "  can   i change the   author-order ", "author order?"],
)
def test_matching_ignores_case_spacing_and_punctuation(rules, question):
    assert match_question(question, rules).best.rule.rule_code == "AUTHOR-009"


def test_alternative_wordings_from_the_keyword_list(rules):
    cases = {
        "Can I rearrange authors?": "AUTHOR-009",
        "Can I reorder the authors?": "AUTHOR-009",
        "Should I change the order of the authors?": "AUTHOR-009",
        "What is the order of authors rule?": "AUTHOR-009",
        "Do I need to expand an ORCID iD?": "AUTHOR-012",
        "What does snippet mean?": "AUTHOR-011",
        "How do I treat a double-barrelled name?": "AUTHOR-019",
        "What is the contribution symbol?": "AUTHOR-006",
        "The author contributed equally, what now?": "AUTHOR-006",
        "There is a single name for the author": "AUTHOR-002",
        "What about a middle initial?": "AUTHOR-020",
        "Is uppercase allowed for an author name?": "AUTHOR-013",
        "Do News articles need an author group?": "AUTHOR-017",
    }
    for question, code in cases.items():
        result = match_question(question, rules)
        assert result.best is not None, question
        assert result.best.rule.rule_code == code, question


def test_rule_without_keyword_entry_still_matches_on_its_topic(rules):
    from app.models import Rule

    new_rule = Rule(
        id=99, rule_code="AUTHOR-099", category="Author", topic="Suffixes such as Jr",
        rule_text="x", source="Initial team guidance", status="draft", version=1,
    )
    result = match_question("How do I handle suffixes such as Jr?", [*rules, new_rule])
    assert result.best.rule.rule_code == "AUTHOR-099"


def test_approved_rules_have_no_draft_notice(rules):
    result = match_question("What is a snippet?", rules)
    result.best.rule.status = "approved"
    try:
        answer = answer_builder.build_answer(result)
        assert answer.status_notice is None
    finally:
        result.best.rule.status = "draft"
