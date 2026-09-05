"""Shared paths for the deterministic tests."""

from __future__ import annotations

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
PLUGIN = ROOT / "plugins" / "oss-maintainer"
FIXTURES = PLUGIN / "evals" / "fixtures"


@pytest.fixture(scope="session")
def root() -> Path:
    return ROOT


@pytest.fixture(scope="session")
def plugin() -> Path:
    return PLUGIN


@pytest.fixture(scope="session")
def fixtures() -> Path:
    return FIXTURES
