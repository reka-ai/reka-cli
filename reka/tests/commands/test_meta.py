# ABOUTME: Tests for the meta and configure leaf commands
# ABOUTME: Verifies machine-readable contract shape and configure command behavior

import json

from typer.testing import CliRunner

from reka.main import app

runner = CliRunner()


def _find_command(commands: list[dict], path: str):
    for command in commands:
        if command.get("path") == path:
            return command
        subcommands = command.get("subcommands", [])
        found = _find_command(subcommands, path)
        if found:
            return found
    return None


class TestMeta:
    def test_meta_returns_json_contract(self):
        result = runner.invoke(app, ["meta", "--format", "json"])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["name"] == "reka"
        assert "commands" in data
        assert "exit_codes" in data

    def test_meta_marks_wait_capable_commands(self):
        result = runner.invoke(app, ["meta", "--format", "json"])
        data = json.loads(result.stdout)
        upload = _find_command(data["commands"], "videos upload")
        assert upload is not None
        assert upload["supports_wait"] is True

    def test_meta_describes_configure_as_leaf_command(self):
        result = runner.invoke(app, ["meta", "--format", "json"])
        data = json.loads(result.stdout)
        configure = _find_command(data["commands"], "configure")
        assert configure is not None
        assert configure["kind"] == "command"

    def test_meta_rejects_unknown_format(self):
        result = runner.invoke(app, ["meta", "--format", "yaml"])
        assert result.exit_code == 1


class TestConfigure:
    def test_configure_writes_config_file(self, monkeypatch, tmp_path):
        config_path = tmp_path / "config.json"
        monkeypatch.setattr("reka.commands.configure.DEFAULT_CONFIG_PATH", config_path)

        result = runner.invoke(
            app,
            ["configure", "--token", "reka_test", "--env", "staging"],
        )
        assert result.exit_code == 0
        data = json.loads(config_path.read_text())
        assert data["token"] == "reka_test"
        assert data["env"] == "staging"

    def test_configure_help_shows_leaf_usage(self):
        result = runner.invoke(app, ["configure", "--help"])
        assert result.exit_code == 0
        assert "Usage: reka configure [OPTIONS]" in result.stdout
        assert "COMMAND [ARGS]" not in result.stdout
