from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def test_app_loads_environment_before_market_route_import(tmp_path: Path) -> None:
    fake_dotenv = tmp_path / "dotenv.py"
    fake_dotenv.write_text(
        """
import os

def load_dotenv(*args, **kwargs):
    os.environ["DHAN_CLIENT_ID"] = "test-client"
    os.environ["DHAN_ACCESS_TOKEN"] = "test-token"
    os.environ.pop("DHAN_OPTION_EXPIRY", None)
    return True
""".strip()
    )

    project_root = Path(__file__).resolve().parents[1]

    script = """
from src.api.routes import market

names = [
    getattr(
        getattr(provider, "provider", None),
        "name",
        provider.name,
    )
    for provider in market.provider_manager.providers
]

assert "DHAN" in names, names
assert "BROKER" not in names, names
"""

    env = os.environ.copy()
    env.pop("DHAN_CLIENT_ID", None)
    env.pop("DHAN_ACCESS_TOKEN", None)
    env.pop("DHAN_OPTION_EXPIRY", None)
    env["PYTHONPATH"] = os.pathsep.join(
        [str(tmp_path), str(project_root)]
    )

    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "import src.api.app\n" + script,
        ],
        cwd=project_root,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr or result.stdout
