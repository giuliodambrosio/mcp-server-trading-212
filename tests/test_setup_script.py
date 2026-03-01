from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path


def _copy_setup_project(tmp_path: Path, repo_root: Path) -> Path:
    project_dir = tmp_path / "project"
    project_dir.mkdir(parents=True, exist_ok=True)

    shutil.copy2(repo_root / "setup.sh", project_dir / "setup.sh")
    shutil.copy2(repo_root / ".env.template", project_dir / ".env.template")
    (project_dir / "main.py").write_text("print('ok')\n", encoding="utf-8")

    os.chmod(project_dir / "setup.sh", 0o755)
    return project_dir


def _run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)


def test_setup_help_works(repo_root: Path) -> None:
    result = _run([str(repo_root / "setup.sh"), "--help"], repo_root)

    assert result.returncode == 0
    assert "Usage: ./setup.sh" in result.stdout


def test_setup_unknown_arg_fails(repo_root: Path) -> None:
    result = _run([str(repo_root / "setup.sh"), "--unknown"], repo_root)

    assert result.returncode != 0
    assert "Unknown argument" in (result.stdout + result.stderr)


def test_non_interactive_bootstrap_creates_env(tmp_path: Path, repo_root: Path) -> None:
    project_dir = _copy_setup_project(tmp_path, repo_root)
    claude_dir = project_dir / "claude"

    result = _run(
        [
            "./setup.sh",
            "--non-interactive",
            "--skip-install",
            "--skip-validation",
            "--update-claude-config",
            "skip",
            "--claude-config-dir",
            str(claude_dir),
        ],
        project_dir,
    )

    assert result.returncode == 0
    assert (project_dir / ".env").exists()


def test_claude_config_auto_update_is_idempotent_and_preserves_other_keys(
    tmp_path: Path, repo_root: Path
) -> None:
    project_dir = _copy_setup_project(tmp_path, repo_root)
    claude_dir = project_dir / "claude"
    claude_dir.mkdir(parents=True, exist_ok=True)
    config_file = claude_dir / "claude_desktop_config.json"

    initial = {
        "mcpServers": {
            "weather": {
                "command": "uv",
                "args": ["--directory", "/tmp/weather", "run", "main.py"],
            }
        },
        "preferences": {"sidebarMode": "chat"},
    }
    config_file.write_text(json.dumps(initial), encoding="utf-8")

    cmd = [
        "./setup.sh",
        "--non-interactive",
        "--skip-install",
        "--skip-validation",
        "--update-claude-config",
        "auto",
        "--claude-config-dir",
        str(claude_dir),
    ]

    run1 = _run(cmd, project_dir)
    run2 = _run(cmd, project_dir)

    assert run1.returncode == 0
    assert run2.returncode == 0
    assert "already up to date" in run2.stdout

    updated = json.loads(config_file.read_text(encoding="utf-8"))
    assert "weather" in updated.get("mcpServers", {})
    assert "212-trading" in updated.get("mcpServers", {})
    assert updated.get("preferences", {}).get("sidebarMode") == "chat"

    entry = updated["mcpServers"]["212-trading"]
    assert entry["command"] == "uv"
    assert entry["args"][0] == "--directory"
    assert entry["args"][2:4] == ["run", "main.py"]


def test_claude_config_skip_mode_does_not_change_file(tmp_path: Path, repo_root: Path) -> None:
    project_dir = _copy_setup_project(tmp_path, repo_root)
    claude_dir = project_dir / "claude"
    claude_dir.mkdir(parents=True, exist_ok=True)
    config_file = claude_dir / "claude_desktop_config.json"

    original = {"mcpServers": {"x": {"command": "node", "args": ["a.js"]}}}
    config_file.write_text(json.dumps(original), encoding="utf-8")

    result = _run(
        [
            "./setup.sh",
            "--non-interactive",
            "--skip-install",
            "--skip-validation",
            "--update-claude-config",
            "skip",
            "--claude-config-dir",
            str(claude_dir),
        ],
        project_dir,
    )

    assert result.returncode == 0
    assert json.loads(config_file.read_text(encoding="utf-8")) == original


def test_invalid_claude_config_recovers_to_valid_json(tmp_path: Path, repo_root: Path) -> None:
    project_dir = _copy_setup_project(tmp_path, repo_root)
    claude_dir = project_dir / "claude"
    claude_dir.mkdir(parents=True, exist_ok=True)
    config_file = claude_dir / "claude_desktop_config.json"

    config_file.write_text("{ invalid json", encoding="utf-8")

    result = _run(
        [
            "./setup.sh",
            "--non-interactive",
            "--skip-install",
            "--skip-validation",
            "--update-claude-config",
            "auto",
            "--claude-config-dir",
            str(claude_dir),
        ],
        project_dir,
    )

    assert result.returncode == 0
    parsed = json.loads(config_file.read_text(encoding="utf-8"))
    assert "mcpServers" in parsed
    assert "212-trading" in parsed["mcpServers"]
