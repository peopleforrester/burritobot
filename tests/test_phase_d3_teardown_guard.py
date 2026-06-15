# ABOUTME: Phase D3 test — teardown.sh --yes requires a second env-var signal (C13).
# ABOUTME: A stray CI run with --yes alone must still prompt; both signals proceed silently.

from __future__ import annotations

import os
import shutil
import stat
import subprocess
from pathlib import Path

import pytest

from conftest import PROJECT_ROOT


TEARDOWN = PROJECT_ROOT / "scripts" / "teardown.sh"
ALLOW_ENV = "CAST_NET_ALLOW_DESTROY"


@pytest.mark.static
def test_teardown_script_references_allow_env() -> None:
    """The script must mention the env var or the guard is missing."""
    text = TEARDOWN.read_text()
    assert ALLOW_ENV in text, (
        f"scripts/teardown.sh must gate --yes on {ALLOW_ENV}=true (C13). "
        f"Without it, a stray CI invocation with --yes destroys the cluster."
    )


@pytest.mark.static
def test_yes_without_env_var_still_prompts(tmp_path: Path) -> None:
    """Behaviour: --yes alone must NOT skip the confirmation prompt."""
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    for cmd in ("terraform", "kubectl", "gcloud"):
        stub = bin_dir / cmd
        stub.write_text("#!/usr/bin/env bash\nexit 0\n")
        stub.chmod(stub.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

    env = os.environ.copy()
    env["PATH"] = f"{bin_dir}:{env.get('PATH', '')}"
    env.pop(ALLOW_ENV, None)

    proc = subprocess.run(
        ["bash", str(TEARDOWN), "--yes"],
        input="",  # no interactive answer — prompt should still fire
        capture_output=True,
        text=True,
        env=env,
        timeout=10,
    )
    # Without the env var, --yes should still hit the prompt and abort
    # (because stdin is empty / not 'DESTROY').
    assert proc.returncode != 0, (
        f"--yes without {ALLOW_ENV}=true must NOT skip the prompt; "
        f"got exit {proc.returncode}\nstderr: {proc.stderr}"
    )
    assert "aborted" in proc.stderr.lower() or "destroy" in proc.stderr.lower(), (
        f"expected an abort/prompt-related message in stderr; got: {proc.stderr}"
    )


@pytest.mark.static
def test_yes_with_env_var_skips_prompt(tmp_path: Path) -> None:
    """Behaviour: --yes plus the env var proceeds without prompting."""
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    for cmd in ("terraform", "kubectl", "gcloud"):
        stub = bin_dir / cmd
        stub.write_text("#!/usr/bin/env bash\nexit 0\n")
        stub.chmod(stub.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

    env = os.environ.copy()
    env["PATH"] = f"{bin_dir}:{env.get('PATH', '')}"
    env[ALLOW_ENV] = "true"

    proc = subprocess.run(
        ["bash", str(TEARDOWN), "--yes"],
        input="",  # if the script prompts, this empty stdin will abort
        capture_output=True,
        text=True,
        env=env,
        timeout=30,
    )
    assert proc.returncode == 0, (
        f"--yes plus {ALLOW_ENV}=true must complete without prompting; "
        f"got exit {proc.returncode}\nstderr: {proc.stderr}"
    )
    assert "teardown complete" in proc.stderr.lower(), (
        f"expected 'teardown complete' in stderr; got: {proc.stderr}"
    )
