from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain.facts import BusinessFacts
from app.rules.types import RegulationConfig, RuleResult


class Rule(ABC):
    """One deterministic compliance rule.

    `regulation_code` must match a seeded Regulation.code -- the engine
    looks up that row and hands its config to `evaluate`. A rule that
    can't find its regulation is a configuration error, not something to
    silently skip (see RulesEngine).
    """

    rule_id: str
    regulation_code: str

    @abstractmethod
    def evaluate(self, facts: BusinessFacts, regulation: RegulationConfig) -> RuleResult: ...
