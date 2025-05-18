import subprocess
import sys
import time
from pathlib import Path
import os


def test_warn_missing_env(monkeypatch):
    root = Path(__file__).resolve().parents[1]
    monkeypatch.delenv("BOOMI_ACCOUNT", raising=False)
    monkeypatch.delenv("BOOMI_USER", raising=False)
    monkeypatch.delenv("BOOMI_SECRET", raising=False)
    env = os.environ.copy()
    env["PYTHONPATH"] = str(root)
    proc = subprocess.Popen(
        [sys.executable, "server.py"],
        cwd=root,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env,
    )
    try:
        time.sleep(0.5)
        stderr_line = proc.stderr.readline()
        assert "Missing Boomi credentials" in stderr_line
    finally:
        proc.terminate()
        proc.wait(timeout=5)
