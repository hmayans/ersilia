from unittest.mock import MagicMock, patch
import pytest
from click.testing import CliRunner

from ersilia.cli.commands.performance import performance_cmd

MODEL_ID = "eos4e40"

@pytest.fixture
def mock_fetch():
    with patch("ersilia.cli.commands.performance.fetch_cmd") as mock_cmd:
        mock_instance = MagicMock()
        mock_instance.callback = MagicMock(side_effect=lambda *a, **k: None)
        mock_cmd.return_value = mock_instance
        yield mock_instance

@pytest.fixture
def mock_serve():
    with patch("ersilia.cli.commands.performance.serve_cmd") as mock_cmd:
        mock_instance = MagicMock()
        mock_cmd.return_value = mock_instance
        yield mock_instance

@pytest.fixture
def mock_example():
    with patch("ersilia.cli.commands.performance.example_cmd") as mock_cmd:
        mock_instance = MagicMock()
        mock_cmd.return_value = mock_instance
        yield mock_instance

@pytest.fixture
def mock_run():
    with patch("ersilia.cli.commands.performance.run_cmd") as mock_cmd:
        mock_instance = MagicMock()
        mock_cmd.return_value = mock_instance
        yield mock_instance

@pytest.fixture
def mock_close():
    with patch("ersilia.cli.commands.performance.close_cmd") as mock_cmd:
        mock_instance = MagicMock()
        mock_cmd.return_value = mock_instance
        yield mock_instance

@pytest.fixture
def mock_docker():
    # Patch docker.from_env so no real Docker calls happen
    with patch("ersilia.cli.commands.performance.docker.from_env", return_value=MagicMock()) as mock_docker_env:
        yield mock_docker_env

def test_performance_cmd(
    mock_fetch, mock_serve, mock_example, mock_run, mock_close
):
    runner = CliRunner()
    result = runner.invoke(performance_cmd(), [MODEL_ID])

    print(result.output) 

    assert result.exit_code == 0

    assert mock_fetch.callback.called
    assert mock_serve.callback.called
    assert mock_example.callback.called
    assert mock_run.callback.called
    assert mock_close.callback.called

def test_performance_no_mock():
    runner = CliRunner()
    result = runner.invoke(performance_cmd(), [MODEL_ID])

    print(result.output)

    # Command should exit cleanly
    assert result.exit_code == 0

    assert "Performance Report" in result.output
    assert f'Model:    {MODEL_ID}' in result.output