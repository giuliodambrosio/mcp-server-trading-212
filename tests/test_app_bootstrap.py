from __future__ import annotations

from dataclasses import dataclass

import server.app as app_module


@dataclass
class FakeMCPWithPrompt:
    name: str
    instructions: str

    def prompt(self, **kwargs):
        def decorator(fn):
            return fn

        return decorator


@dataclass
class FakeMCPWithoutPrompt:
    name: str
    instructions: str


def test_create_app_registers_resources_tools_and_prompts(monkeypatch):
    calls = {"load_dotenv": 0, "register_resources": 0, "register_tools": 0, "register_prompts": 0}

    def fake_load_dotenv():
        calls["load_dotenv"] += 1

    def fake_build_clients_from_env():
        return {"isa": object()}, "isa"

    def fake_register_resources(mcp, read_service):
        calls["register_resources"] += 1

    def fake_register_tools(mcp, read_service):
        calls["register_tools"] += 1

    def fake_register_prompts(mcp):
        calls["register_prompts"] += 1

    monkeypatch.setattr(app_module, "load_dotenv", fake_load_dotenv)
    monkeypatch.setattr(app_module, "build_clients_from_env", fake_build_clients_from_env)
    monkeypatch.setattr(app_module, "register_resources", fake_register_resources)
    monkeypatch.setattr(app_module, "register_tools", fake_register_tools)
    monkeypatch.setattr(app_module, "register_prompts", fake_register_prompts)
    monkeypatch.setattr(app_module, "FastMCP", FakeMCPWithPrompt)

    app = app_module.create_app()

    assert app.name == "212-trading"
    assert "Supported account aliases are isa and invest" in app.instructions
    assert calls == {"load_dotenv": 1, "register_resources": 1, "register_tools": 1, "register_prompts": 1}


def test_create_app_skips_prompt_registration_when_unsupported(monkeypatch):
    calls = {"register_prompts": 0}

    def fake_load_dotenv():
        return None

    def fake_build_clients_from_env():
        return {"isa": object()}, "isa"

    def fake_register_resources(mcp, read_service):
        return None

    def fake_register_tools(mcp, read_service):
        return None

    def fake_register_prompts(mcp):
        calls["register_prompts"] += 1

    monkeypatch.setattr(app_module, "load_dotenv", fake_load_dotenv)
    monkeypatch.setattr(app_module, "build_clients_from_env", fake_build_clients_from_env)
    monkeypatch.setattr(app_module, "register_resources", fake_register_resources)
    monkeypatch.setattr(app_module, "register_tools", fake_register_tools)
    monkeypatch.setattr(app_module, "register_prompts", fake_register_prompts)
    monkeypatch.setattr(app_module, "FastMCP", FakeMCPWithoutPrompt)

    app_module.create_app()

    assert calls["register_prompts"] == 0
