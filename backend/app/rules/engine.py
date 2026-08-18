from __future__ import annotations

from app.domain.facts import BusinessFacts
from app.rules.base import Rule
from app.rules.registry import ALL_RULES
from app.rules.types import RegulationConfig, RuleResult


class RulesEngine:
    """Deterministic evaluator: structured facts + seeded regulation config
    in, explainable RuleResults out. No LLM involved anywhere in this path.
    """

    def __init__(self, rules: list[Rule] | None = None) -> None:
        self.rules = rules if rules is not None else ALL_RULES

    def evaluate(
        self, facts: BusinessFacts, regulations_by_code: dict[str, RegulationConfig]
    ) -> list[RuleResult]:
        results: list[RuleResult] = []
        for rule in self.rules:
            regulation = regulations_by_code.get(rule.regulation_code)
            if regulation is None:
                raise ValueError(
                    f"Regulation '{rule.regulation_code}' required by rule '{rule.rule_id}' "
                    "is not seeded. Run the regulation seed loader first."
                )
            results.append(rule.evaluate(facts, regulation))
        return results
