from pathlib import Path
from collections.abc import Callable

import pytest

from paperweave.cli import _initialize
from paperweave.config import ConfigError, load_config


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def test_example_configuration_is_valid() -> None:
    config = load_config(PROJECT_ROOT / "config.example.toml")

    assert config.api.port == 18741
    assert config.ui.port == 18742
    assert config.ui.api_base_url == "http://127.0.0.1:18741"
    assert config.timeouts.health_poll_seconds == 10.0
    assert config.deployment.bind_host == "127.0.0.1"


def test_invalid_configuration_does_not_echo_password(tmp_path: Path) -> None:
    source = (PROJECT_ROOT / "config.example.toml").read_text(encoding="utf-8")
    secret = "private-password-value"
    invalid = source.replace('port = 18741', 'port = "invalid"').replace('password = "change_me"', f'password = "{secret}"')
    path = tmp_path / "invalid.toml"
    path.write_text(invalid, encoding="utf-8")

    with pytest.raises(ConfigError) as error:
        load_config(path)

    assert "api.port" in str(error.value)
    assert secret not in str(error.value)


@pytest.mark.parametrize(
    ("source", "field"),
    [
        (lambda text: text.replace('name = "PaperWeave"\n', "", 1), "app.name"),
        (lambda text: text.replace("port = 18741", "port = 70000", 1), "api.port"),
        (lambda text: text.replace("health_seconds = 2.0", "health_seconds = 0", 1), "health_seconds"),
    ],
)
def test_required_fields_ports_and_timeouts_are_validated(
    tmp_path: Path, source: Callable[[str], str], field: str
) -> None:
    invalid = source((PROJECT_ROOT / "config.example.toml").read_text(encoding="utf-8"))
    path = tmp_path / "invalid.toml"
    path.write_text(invalid, encoding="utf-8")

    with pytest.raises(ConfigError) as error:
        load_config(path)

    assert field in str(error.value)


def test_non_loopback_bind_host_is_rejected(tmp_path: Path) -> None:
    source = (PROJECT_ROOT / "config.example.toml").read_text(encoding="utf-8")
    path = tmp_path / "public-bind.toml"
    path.write_text(source.replace('bind_host = "127.0.0.1"', 'bind_host = "0.0.0.0"'), encoding="utf-8")

    with pytest.raises(ConfigError, match="loopback"):
        load_config(path)


def test_init_does_not_overwrite_existing_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    target = tmp_path / "config.toml"
    target.write_text("owner data\n", encoding="utf-8")
    monkeypatch.setattr("paperweave.cli.ROOT", PROJECT_ROOT)

    assert _initialize(target) == 0
    assert target.read_text(encoding="utf-8") == "owner data\n"
