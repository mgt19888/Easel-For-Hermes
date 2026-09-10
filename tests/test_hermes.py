"""Hermes fork integration checks; no live model calls."""
import asyncio
import io
import json
import subprocess

import pytest

from easel import runtime
from web import app as web


def test_session_is_scoped_and_message_is_literal(monkeypatch, tmp_path):
    monkeypatch.setenv("EASEL_HERMES_PROFILE", "creative")
    message = "用户文本 $(touch never) `literal`\n第二行"
    command = runtime.hermes_command(message, "../../latest", 123)
    assert command[:3] == ["hermes", "--profile", "creative"]
    assert command[-1].endswith(message)
    assert "--ignore-rules" in command
    assert "--yolo" not in command
    name = runtime.session_name("../../latest")
    assert name != runtime.session_name("latest")
    assert "/" not in name
    monkeypatch.setattr(runtime, "ROOT", tmp_path)
    assert runtime.session_name("../../latest") != name


def test_sync_error_not_exposed_as_success(monkeypatch, tmp_path):
    monkeypatch.setenv("EASEL_RUNTIME", "hermes")
    monkeypatch.setattr(web, "SESSIONS_DIR", tmp_path)
    def failed(command, **kwargs):
        assert command[0] == "hermes"
        return subprocess.CompletedProcess(command, 1, "private diagnostic", "secret")
    monkeypatch.setattr(web.subprocess, "run", failed)
    response = web.run_agent_sync("test", session_id="sync-test")
    assert "执行失败" in response
    assert "private" not in response and "secret" not in response


@pytest.mark.parametrize("returncode,reply", [(0, "第一段\n\n第二段\n"), (1, ""), (0, "")])
def test_web_hermes_completion_and_recovery(monkeypatch, tmp_path, returncode, reply):
    monkeypatch.setenv("EASEL_RUNTIME", "hermes")
    for attr in ("SESSIONS_DIR", "DEBUG_DIR", "OUTPUTS_DIR"):
        monkeypatch.setattr(web, attr, tmp_path / attr)
    class Process:
        stdout = io.StringIO(reply)
        stderr = io.StringIO("diagnostic-not-a-reply\nsession_id: 20260910_test\n")
        def poll(self):
            return returncode
    def spawn(command, **kwargs):
        assert command[0] == "hermes"
        assert kwargs["stderr"] == subprocess.PIPE
        assert "OPENCLAW_RAW_STREAM" not in kwargs["env"]
        return Process()
    monkeypatch.setattr(web.subprocess, "Popen", spawn)
    turns = []
    monkeypatch.setattr(web, "_save_turn", lambda *args: turns.append(args))
    async def run():
        response = await web.api_chat_stream(web.ChatRequest(message="hello", sessionId="stream-test"))
        events = [event async for event in response.body_iterator]
        return events
    events = asyncio.run(run())
    text = "".join(json.loads(e["data"]) for e in events if e["event"] == "token")
    assert "diagnostic-not-a-reply" not in text
    assert "session_id" not in text
    assert events[-1]["event"] == "done"
    if returncode == 0 and reply:
        assert text == reply.strip()
        assert turns[-1][3]["clean_end"] is True
        assert web._hermes_session_file("stream-test").read_text() == "20260910_test"
    else:
        assert any(e["event"] == "error" for e in events)
        assert turns[-1][3]["clean_end"] is False
