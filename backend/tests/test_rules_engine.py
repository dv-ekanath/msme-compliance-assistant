from __future__ import annotations

import pytest

from app.rules.engine import RulesEngine
from app.rules.registry import ALL_RULES, REGULATION_CODES
from tests.conftest import make_facts


def test_engine_returns_one_result_per_rule(regulation_configs):
    results = RulesEngine().evaluate(make_facts(), regulation_configs)
    assert len(results) == len(ALL_RULES)
    assert {r.rule_id for r in results} == {rule.rule_id for rule in ALL_RULES}


def test_engine_raises_on_missing_regulation(regulation_configs):
    incomplete = {code: cfg for code, cfg in regulation_configs.items() if code != "GST"}
    with pytest.raises(ValueError, match="GST"):
        RulesEngine().evaluate(make_facts(), incomplete)


def test_all_rule_regulation_codes_are_seeded(regulation_configs):
    assert REGULATION_CODES <= set(regulation_configs.keys())
