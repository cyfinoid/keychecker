"""
Tests for SSH command construction in the base Git provider plugin.

These verify that the macOS-only ``UseKeychain`` OpenSSH option is emitted only
on macOS. On Linux/other platforms the ssh client aborts with
"Bad configuration option: usekeychain", which previously surfaced as a false
"authentication failed" for every server.
"""

import asyncio

import keychecker.plugins.base as base
from keychecker.plugins.base import BaseGitProvider, ServerConfig


class _DummyProvider(BaseGitProvider):
    """Minimal concrete provider so the ABC can be instantiated in tests."""

    async def validate_key(self, private_key_path):  # pragma: no cover - stub
        return {}

    async def identify_user(self, private_key_path):  # pragma: no cover - stub
        return None

    async def discover_organizations(self, private_key_path, username):
        return []  # pragma: no cover - stub

    async def test_repository_access(self, private_key_path, repo_name):
        return False  # pragma: no cover - stub


class _FakeProc:
    def __init__(self):
        self.returncode = 0

    async def communicate(self):
        return b"", b""


def _make_provider():
    return _DummyProvider(ServerConfig(name="test", hostname="example.com"))


def _capture_exec(monkeypatch):
    """Patch create_subprocess_exec and return a dict capturing the call."""
    captured = {}

    async def fake_exec(*args, **kwargs):
        captured["args"] = args
        captured["env"] = kwargs.get("env")
        return _FakeProc()

    monkeypatch.setattr(base.asyncio, "create_subprocess_exec", fake_exec)
    return captured


class TestUseKeychainPlatformGating:
    def test_ssh_command_omits_usekeychain_off_macos(self, monkeypatch):
        monkeypatch.setattr(base, "_IS_MACOS", False)
        captured = _capture_exec(monkeypatch)

        provider = _make_provider()
        asyncio.run(provider._run_ssh_command("/tmp/key"))

        assert "UseKeychain=no" not in captured["args"]

    def test_ssh_command_includes_usekeychain_on_macos(self, monkeypatch):
        monkeypatch.setattr(base, "_IS_MACOS", True)
        captured = _capture_exec(monkeypatch)

        provider = _make_provider()
        asyncio.run(provider._run_ssh_command("/tmp/key"))

        assert "UseKeychain=no" in captured["args"]
        # Ensure the trailing "user@host" target is still last.
        assert captured["args"][-1] == "git@example.com"

    def test_git_ssh_command_omits_usekeychain_off_macos(self, monkeypatch):
        monkeypatch.setattr(base, "_IS_MACOS", False)
        captured = _capture_exec(monkeypatch)

        provider = _make_provider()
        asyncio.run(provider._run_git_ls_remote("/tmp/key", "git@example.com:o/r"))

        assert "UseKeychain" not in captured["env"]["GIT_SSH_COMMAND"]

    def test_git_ssh_command_includes_usekeychain_on_macos(self, monkeypatch):
        monkeypatch.setattr(base, "_IS_MACOS", True)
        captured = _capture_exec(monkeypatch)

        provider = _make_provider()
        asyncio.run(provider._run_git_ls_remote("/tmp/key", "git@example.com:o/r"))

        assert "UseKeychain=no" in captured["env"]["GIT_SSH_COMMAND"]
