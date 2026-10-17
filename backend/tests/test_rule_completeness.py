from types import SimpleNamespace

import pytest

from app.services.rule_completeness import check_completeness


def rule(**overrides):
    values = dict(
        rule_code="TEST-001", rule_text="Text.", action="Do it.", source="Team",
        status="draft", condition=None, exception=None, escalation=None, source_section=None,
    )
    return SimpleNamespace(**{**values, **overrides})


def test_complete_rule_has_no_missing_fields():
    report = check_completeness(rule())
    assert report.complete is True
    assert report.missing_fields == []


def test_only_authoring_009_is_complete_in_the_seed_data(rules):
    reports = {r.rule_code: check_completeness(r) for r in rules}
    assert [code for code, rep in reports.items() if rep.complete] == ["AUTHOR-009"]
    for code, report in reports.items():
        if code != "AUTHOR-009":
            assert report.missing_fields == ["action"], code


def test_response_shape_matches_the_spec(rules):
    report = check_completeness(rules[0])
    assert report.model_dump()["rule_code"] == "AUTHOR-001"
    assert report.model_dump()["complete"] is False
    assert report.model_dump()["missing_fields"] == ["action"]


@pytest.mark.parametrize("field", ["rule_text", "action", "source", "status"])
@pytest.mark.parametrize("empty", [None, "", "   "])
def test_each_required_field_is_checked(field, empty):
    report = check_completeness(rule(**{field: empty}))
    assert report.complete is False
    assert report.missing_fields == [field]


def test_unknown_status_counts_as_missing():
    assert check_completeness(rule(status="approved")).missing_fields == ["status"]


def test_optional_information_is_reported_but_not_required():
    bare = check_completeness(rule())
    assert bare.complete is True
    assert (bare.has_exception, bare.has_escalation, bare.has_example, bare.has_condition) == (
        False, False, False, False,
    )

    full = check_completeness(
        rule(exception="E", escalation="Q", condition="C", source_section="1.2"), example_count=2
    )
    assert full.complete is True
    assert (full.has_exception, full.has_escalation, full.has_condition) == (True, True, True)
    assert full.has_source_section is True
    assert full.has_example is True and full.example_count == 2
