# ABOUTME: Phase C5 test — each .co rail must parse with the nemoguardrails Colang 1.0 parser.
# ABOUTME: Skips cleanly if the package is not installed; otherwise the parse failure is loud.

from __future__ import annotations

from pathlib import Path

import pytest

from conftest import PROJECT_ROOT


RAILS_DIR = PROJECT_ROOT / "ai-gateway" / "nemo-guardrails" / "rails"
RAIL_FILES = sorted(RAILS_DIR.glob("*.co"))


nemoguardrails = pytest.importorskip(
    "nemoguardrails",
    reason="nemoguardrails not installed in dev env; live container "
    "verification remains a Phase D obligation",
)


@pytest.mark.static
@pytest.mark.parametrize("rail", RAIL_FILES, ids=lambda p: p.name)
def test_colang_v1_rail_parses(rail: Path) -> None:
    """Every rail must parse under the Colang 1.0 grammar declared in config.yaml."""
    from nemoguardrails.colang.v1_0.lang.colang_parser import ColangParser

    parser = ColangParser(filename=rail.name, content=rail.read_text())
    try:
        parser.parse()
    except Exception as exc:  # parser raises bare Exception with a message
        pytest.fail(
            f"{rail.name}: Colang 1.0 parse error: {exc}\n"
            f"colang_version is declared '1.0' in config.yaml — the rails "
            f"must match. See docs/PHASE-C-GREENFIELD-PLAN.md (Phase C5)."
        )
