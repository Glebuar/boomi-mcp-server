import subprocess
import sys
from pathlib import Path
import os
import tempfile


def test_fail_missing_env(monkeypatch):
    root = Path(__file__).resolve().parents[1]
    monkeypatch.delenv("BOOMI_ACCOUNT", raising=False)
    monkeypatch.delenv("BOOMI_USER", raising=False)
    monkeypatch.delenv("BOOMI_SECRET", raising=False)
    
    # Create a temporary directory to run the test without .env file
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        
        # Copy src directory to temp location
        import shutil
        temp_src = temp_root / "src"
        shutil.copytree(root / "src", temp_src)
        
        env = os.environ.copy()
        # Remove the credentials from the environment completely
        for key in ["BOOMI_ACCOUNT", "BOOMI_USER", "BOOMI_SECRET"]:
            env.pop(key, None)
        env["PYTHONPATH"] = os.pathsep.join([str(temp_root), str(temp_src)])
        
        proc = subprocess.Popen(
            [sys.executable, "-m", "boomi_mcp_server.server"],
            cwd=temp_root,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env,
        )
        stdout, stderr = proc.communicate(timeout=5)
        assert proc.returncode != 0
        assert "Missing Boomi credentials" in stderr
