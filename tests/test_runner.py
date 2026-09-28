import importlib.util
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location(
    "asr_runner", Path(__file__).parents[1] / "part-a-asr/src/main.py"
)
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


def test_steps_share_state_and_resolve_sibling_files(tmp_path):
    (tmp_path / "input.txt").write_text("42")
    (tmp_path / "one.py").write_text("value = int(open('input.txt').read())")
    (tmp_path / "two.py").write_text("answer = value + 1")
    original = Path.cwd()
    result = runner.run_pipeline(tmp_path, ["one.py", "two.py"])
    assert result["answer"] == 43
    assert Path.cwd() == original


def test_working_directory_restored_after_failure(tmp_path):
    (tmp_path / "fail.py").write_text("raise RuntimeError('failed')")
    original = Path.cwd()
    with pytest.raises(RuntimeError, match="failed"):
        runner.run_pipeline(tmp_path, ["fail.py"])
    assert Path.cwd() == original


def test_missing_step_is_detected_before_any_execution(tmp_path):
    (tmp_path / "first.py").write_text("open('marker', 'w').close()")
    with pytest.raises(FileNotFoundError):
        runner.run_pipeline(tmp_path, ["first.py", "missing.py"])
    assert not (tmp_path / "marker").exists()
