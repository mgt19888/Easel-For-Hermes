"""Install the Hermes edition of Easel; modified September 2026."""
from pathlib import Path
import os
import shutil
import subprocess
import sys
import venv

ROOT = Path(__file__).resolve().parents[1]


def main():
    if not shutil.which(os.environ.get("EASEL_HERMES_BIN", "hermes")):
        print("请先安装 Hermes Agent：https://hermes-agent.nousresearch.com/docs/", file=sys.stderr)
        return 1
    if not shutil.which("npm"):
        print("请先安装 Node.js >= 22.19（包含 npm）。", file=sys.stderr)
        return 1
    target = ROOT / ".venv"
    python = target / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    if not python.exists():
        venv.EnvBuilder(with_pip=True).create(target)
    npm = shutil.which("npm")
    subprocess.run([str(python), "-m", "pip", "install", "-e", str(ROOT)], check=True)
    subprocess.run([npm, "ci"], cwd=ROOT / "web/frontend", check=True)
    subprocess.run([npm, "run", "build"], cwd=ROOT / "web/frontend", check=True)
    subprocess.run([str(python), "-m", "playwright", "install", "chromium"], check=True)
    if not (ROOT / ".env").exists() and (ROOT / ".env.example").exists():
        shutil.copyfile(ROOT / ".env.example", ROOT / ".env")
    print("Easel Hermes 依赖安装完成。模型首次配置：hermes setup")
    print(f"检查：{python} -m easel doctor")
    print(f"启动：{python} -m easel web")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
