# tests/test_workflow.py

import pytest
from pathlib import Path
from src.main import main
from src.workflows import run_all

def test_run_on_sample_project(tmp_path, capsys):
    """
    Smoke test: run the full pipeline on a minimal 'hello-world' sample project.
    Verifies that:
      • The workflow completes without raising.
      • The final recap mentions "New agent added" and the expected new file.
    """

    # Locate the sample ZIP in the tests directory
    tests_dir = Path(__file__).parent
    sample_zip = tests_dir / "sample_project.zip"
    assert sample_zip.exists(), f"Missing sample_project.zip at {sample_zip}"

    # Use run_all to execute the pipeline in offline/fallback mode.
    # We choose a prompt that triggers creation of a SampleAgent.
    prompt = "Add a new helper agent called SampleAgent"
    recap = run_all(str(sample_zip), prompt)

    # The recap should mention that a new agent was added
    assert "New agent added" in recap

    # The recap should refer to the newly created file:
    # src/agents/sampleagent.py  (case-insensitive check)
    assert "sampleagent.py" in recap.lower()

    # Optionally, verify that the file actually exists on disk now
    created_file = Path("src/agents/sampleagent.py")
    assert created_file.exists(), f"Expected agent file not found: {created_file}"

def test_cli_exit_code(tmp_path):
    """
    Test that invoking main() as a CLI returns exit code 0 for the sample project.
    This simulates: python -m src --zip tests/sample_project.zip --prompt "Add SampleAgent"
    """
    tests_dir = Path(__file__).parent
    sample_zip = tests_dir / "sample_project.zip"
    assert sample_zip.exists()

    # Capture SystemExit to inspect the exit code
    with pytest.raises(SystemExit) as excinfo:
        # We pass --quiet to suppress logs and only get the exit code
        main([f"--zip={sample_zip}", "--prompt=Add SampleAgent", "--quiet"])

    assert excinfo.value.code == 0
