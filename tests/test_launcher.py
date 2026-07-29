"""Launcher model-fallback tests.

The CLI's --fallback-model flag only covers server overload/unavailability. A
per-account usage-limit exhaustion ("You've reached your Fable 5 limit") exits 1
with the message on stdout and is NOT caught by that flag, so run_role must
detect it and re-run on the fallback model itself. These tests pin that seam.
"""
from unittest import mock

import pytest

from orchestrator import launcher


LIMIT_MSG = ("You've reached your Fable 5 limit. Run /usage-credits to "
             "continue or switch models with /model.\n")


@pytest.fixture(autouse=True)
def _tmp_db(tmp_path, monkeypatch):
    """Point the cooldown meta store at a throwaway DB: launcher tests must
    never stamp cooldowns into the real datasets/earnings.sqlite3."""
    monkeypatch.setenv("EARNINGS_DB", str(tmp_path / "launcher-test.sqlite3"))


def _models_from_calls(calls):
    """Extract the --model value from each _run_capturing invocation."""
    out = []
    for c in calls:
        cmd = c.args[0] if c.args else c.kwargs["cmd"]
        out.append(cmd[cmd.index("--model") + 1])
    return out


def test_usage_limit_falls_back_to_opus():
    # Fable 5 usage-limited (exit 1 + limit message), Opus succeeds.
    scripted = [(1, LIMIT_MSG), (0, "done\n")]
    with mock.patch.object(launcher.shutil, "which", return_value="/x/claude"), \
         mock.patch.object(launcher, "_run_capturing",
                           side_effect=scripted) as rc:
        code = launcher.run_role("scout")
    assert code == 0
    assert _models_from_calls(rc.call_args_list) == [
        launcher.DEFAULT_MODEL, launcher.FALLBACK_MODEL]


def test_success_does_not_fall_back():
    with mock.patch.object(launcher.shutil, "which", return_value="/x/claude"), \
         mock.patch.object(launcher, "_run_capturing",
                           return_value=(0, "done\n")) as rc:
        code = launcher.run_role("scout")
    assert code == 0
    assert rc.call_count == 1  # never touched the fallback


def test_non_limit_failure_does_not_fall_back():
    # A real error (not a usage limit) must NOT burn the fallback quota.
    with mock.patch.object(launcher.shutil, "which", return_value="/x/claude"), \
         mock.patch.object(launcher, "_run_capturing",
                           return_value=(2, "some other error\n")) as rc:
        code = launcher.run_role("scout")
    assert code == 2
    assert rc.call_count == 1


def test_timeout_does_not_fall_back():
    # A hung run (124) is killed and reconciled next tick, not retried.
    with mock.patch.object(launcher.shutil, "which", return_value="/x/claude"), \
         mock.patch.object(launcher, "_run_capturing",
                           return_value=(124, "")) as rc:
        code = launcher.run_role("scout")
    assert code == 124
    assert rc.call_count == 1


def test_both_models_limited_returns_nonzero():
    scripted = [(1, LIMIT_MSG), (1, LIMIT_MSG)]
    with mock.patch.object(launcher.shutil, "which", return_value="/x/claude"), \
         mock.patch.object(launcher, "_run_capturing",
                           side_effect=scripted) as rc:
        code = launcher.run_role("scout")
    assert code == 1
    assert rc.call_count == 2


def test_fallback_flag_lists_downstream_models():
    # First attempt (Fable) must still pass --fallback-model=opus for the
    # server-overload class; the terminal Opus attempt passes none.
    scripted = [(1, LIMIT_MSG), (0, "done\n")]
    with mock.patch.object(launcher.shutil, "which", return_value="/x/claude"), \
         mock.patch.object(launcher, "_run_capturing",
                           side_effect=scripted) as rc:
        launcher.run_role("scout")
    first_cmd = rc.call_args_list[0].args[0]
    assert "--fallback-model" in first_cmd
    assert first_cmd[first_cmd.index("--fallback-model") + 1] == \
        launcher.FALLBACK_MODEL
    second_cmd = rc.call_args_list[1].args[0]
    assert "--fallback-model" not in second_cmd


# -- usage-limit cooldown (2026-07-27): a limited model must not burn a boot
# on every subsequent run in the tick. The stamp lives in meta so parallel
# analysts and later roles all see it.

def test_usage_limit_stamps_cooldown_and_next_run_skips_primary():
    scripted = [(1, LIMIT_MSG), (0, "done\n")]
    with mock.patch.object(launcher.shutil, "which", return_value="/x/claude"), \
         mock.patch.object(launcher, "_run_capturing", side_effect=scripted):
        assert launcher.run_role("scout") == 0
    assert launcher.model_limited_until(launcher.DEFAULT_MODEL) is not None

    # Next run: primary is skipped, ONE launch straight on the fallback.
    with mock.patch.object(launcher.shutil, "which", return_value="/x/claude"), \
         mock.patch.object(launcher, "_run_capturing",
                           return_value=(0, "done\n")) as rc:
        assert launcher.run_role("scout") == 0
    assert rc.call_count == 1
    assert _models_from_calls(rc.call_args_list) == [launcher.FALLBACK_MODEL]


def test_all_models_limited_still_tries_full_chain():
    launcher.stamp_model_limited(launcher.DEFAULT_MODEL)
    launcher.stamp_model_limited(launcher.FALLBACK_MODEL)
    with mock.patch.object(launcher.shutil, "which", return_value="/x/claude"), \
         mock.patch.object(launcher, "_run_capturing",
                           return_value=(0, "done\n")) as rc:
        assert launcher.run_role("scout") == 0
    # Chain not emptied: the primary is still attempted (trying beats failing).
    assert _models_from_calls(rc.call_args_list)[0] == launcher.DEFAULT_MODEL


def test_success_on_cooled_model_clears_cooldown():
    launcher.stamp_model_limited(launcher.DEFAULT_MODEL)
    launcher.stamp_model_limited(launcher.FALLBACK_MODEL)  # force all-limited path
    with mock.patch.object(launcher.shutil, "which", return_value="/x/claude"), \
         mock.patch.object(launcher, "_run_capturing", return_value=(0, "done\n")):
        launcher.run_role("scout")
    assert launcher.model_limited_until(launcher.DEFAULT_MODEL) is None


def test_cooldown_read_failure_never_blocks_launch(monkeypatch):
    monkeypatch.setenv("EARNINGS_DB", "/nonexistent-dir/nope/db.sqlite3")
    with mock.patch.object(launcher.shutil, "which", return_value="/x/claude"), \
         mock.patch.object(launcher, "_run_capturing",
                           return_value=(0, "done\n")) as rc:
        assert launcher.run_role("scout") == 0
    assert rc.call_count == 1


# -- transient overload retry (2026-07-29): "API Error: 529 Overloaded" killed
# the 16:20 exit-queueing run with exit 1; not a usage limit, so the chain
# loop (correctly) did not engage, and nothing retried a transient blip.

OVERLOAD_MSG = "API Error: 529 Overloaded. This is a server-side issue...\n"


def test_overload_retries_same_model_then_succeeds(monkeypatch):
    monkeypatch.setattr(launcher, "_sleep", lambda s: None)
    scripted = [(1, OVERLOAD_MSG), (0, "done\n")]
    with mock.patch.object(launcher.shutil, "which", return_value="/x/claude"), \
         mock.patch.object(launcher, "_run_capturing",
                           side_effect=scripted) as rc:
        assert launcher.run_role("scout") == 0
    # Same model both times — a blip must not burn the fallback leg.
    assert _models_from_calls(rc.call_args_list) == [
        launcher.DEFAULT_MODEL, launcher.DEFAULT_MODEL]


def test_persistent_overload_falls_back(monkeypatch):
    monkeypatch.setattr(launcher, "_sleep", lambda s: None)
    scripted = [(1, OVERLOAD_MSG), (1, OVERLOAD_MSG), (0, "done\n")]
    with mock.patch.object(launcher.shutil, "which", return_value="/x/claude"), \
         mock.patch.object(launcher, "_run_capturing",
                           side_effect=scripted) as rc:
        assert launcher.run_role("scout") == 0
    assert _models_from_calls(rc.call_args_list) == [
        launcher.DEFAULT_MODEL, launcher.DEFAULT_MODEL, launcher.FALLBACK_MODEL]


def test_non_overload_error_still_does_not_retry():
    with mock.patch.object(launcher.shutil, "which", return_value="/x/claude"), \
         mock.patch.object(launcher, "_run_capturing",
                           return_value=(2, "some real error\n")) as rc:
        assert launcher.run_role("scout") == 2
    assert rc.call_count == 1
