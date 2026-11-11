"""Answers for complete, incomplete, draft, reviewed and confirmed rules."""
import copy

from app.models import Example
from app.services import answer_builder
from app.services.rule_engine import match_question

DRAFT_TEXT = "Draft team guidance \u2014 not yet confirmed against the official style manual."


def answer_for(question, rules, examples=()):
    return answer_builder.build_answer(match_question(question, rules), examples)


def with_status(rules, code, status):
    changed = copy.deepcopy(rules)
    next(r for r in changed if r.rule_code == code).status = status
    return changed


def test_complete_rule_returns_usable_guidance(rules, seed_items):
    answer = answer_for("Can I change the author order?", rules)  # AUTHOR-009 is complete
    assert answer.rule_complete is True
    assert answer.missing_fields == []
    assert answer.incomplete_notice is None
    assert answer.decision == "Do not change the author order without author approval."
    assert answer.action == seed_items["AUTHOR-009"]["action"]


def test_incomplete_rule_is_clearly_marked_incomplete(rules, seed_items):
    answer = answer_for("How should I process an author with multiple given names?", rules)

    assert answer.matched is True and answer.rule_code == "AUTHOR-001"
    assert answer.rule_complete is False
    assert answer.missing_fields == ["action"]
    assert answer.incomplete_notice == "Guidance found, but this rule is incomplete."
    # The recorded rule text may still be shown...
    assert answer.decision == seed_items["AUTHOR-001"]["rule_text"]
    # ...but the trainee is sent onwards, and the escalation says why.
    assert answer.action == "Check the style manual or raise the question with a lead."
    assert answer.escalation_required is True
    assert "incomplete" in answer.escalation_reason and "action" in answer.escalation_reason


def test_missing_action_is_never_fabricated(rules):
    checked = 0
    for rule in rules:
        if rule.action:
            continue
        # Find a question for the rule from its own topic, then check the action.
        answer = answer_for(rule.topic, rules)
        if answer.rule_code == rule.rule_code:
            assert answer.action == answer_builder.INCOMPLETE_ACTION
            assert answer.action != rule.rule_text
            checked += 1
    assert checked >= 10  # most topics match themselves, so most rules were checked


def test_an_action_is_only_shown_when_the_rule_stores_one(rules):
    shown = {
        answer.rule_code
        for answer in (answer_for(q, rules) for q in ["Can I change the author order?", "What is a snippet?"])
        if answer.action != answer_builder.INCOMPLETE_ACTION
    }
    assert shown == {"AUTHOR-009"}


def test_incomplete_rule_that_also_has_an_escalation_mentions_both(rules, seed_items):
    answer = answer_for("What should I do if the author's given name is missing?", rules)
    assert answer.rule_code == "AUTHOR-002" and answer.rule_complete is False
    assert seed_items["AUTHOR-002"]["escalation"] in answer.escalation_reason


def test_draft_status_is_displayed(rules):
    answer = answer_for("Can I change the author order?", rules)
    assert answer.status == "draft"
    assert answer.status_notice == DRAFT_TEXT
    assert answer.source == "Initial team guidance"


def test_incomplete_draft_rule_also_shows_the_draft_notice(rules):
    assert answer_for("What is a snippet?", rules).status_notice == DRAFT_TEXT


def test_reviewed_status_is_not_described_as_confirmed(rules):
    answer = answer_for("Can I change the author order?", with_status(rules, "AUTHOR-009", "reviewed"))
    assert "not yet confirmed" in answer.status_notice
    assert answer.status_notice != "Confirmed guidance."


def test_confirmed_rule_shows_confirmed_guidance(rules):
    answer = answer_for("Can I change the author order?", with_status(rules, "AUTHOR-009", "confirmed"))
    assert answer.status == "confirmed"
    assert answer.status_notice == "Confirmed guidance."


def test_unknown_status_is_treated_as_unconfirmed(rules):
    answer = answer_for("Can I change the author order?", with_status(rules, "AUTHOR-009", "approved"))
    assert "not confirmed" in answer.status_notice
    assert answer.rule_complete is False and "status" in answer.missing_fields


def test_missing_example_is_reported_as_no_examples(rules):
    answer = answer_for("How should I process an author with multiple given names?", rules)
    assert answer.examples == []


def test_examples_are_included_when_they_exist(rules):
    example = Example(
        rule_id=9, input_text="Can I reorder the authors?",
        correct_output="Do not change the author order without author approval.",
        explanation="Author order should not be changed without approval.",
    )
    answer = answer_for("Can I change the author order?", rules, [example])
    assert len(answer.examples) == 1
    assert answer.examples[0].input_text == "Can I reorder the authors?"
    assert answer.examples[0].explanation == "Author order should not be changed without approval."


def test_no_match_and_ambiguous_answers_have_no_rule_state(rules):
    none = answer_for("What is the weather today?", rules)
    assert none.rule_complete is None and none.examples == [] and none.status_notice is None
    ambiguous = answer_for("Is 'van der' a particle name?", rules)
    assert ambiguous.rule_complete is None and ambiguous.match_status == "ambiguous"
