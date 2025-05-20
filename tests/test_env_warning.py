import subprocess
import sys
import time
from pathlib import Path
import os


def test_fail_missing_env(monkeypatch):
    root = Path(__file__).resolve().parents[1]
    monkeypatch.delenv("BOOMI_ACCOUNT", raising=False)
    monkeypatch.delenv("BOOMI_USER", raising=False)
    monkeypatch.delenv("BOOMI_SECRET", raising=False)
    env = os.environ.copy()
    env["PYTHONPATH"] = os.pathsep.join([str(root), str(root / "src")])
    proc = subprocess.Popen(
        [sys.executable, "-m", "boomi_mcp_server.server"],
        cwd=root,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env,
    )
    stdout, stderr = proc.communicate(timeout=5)
    assert proc.returncode != 0
    assert "Missing Boomi credentials" in stderr
