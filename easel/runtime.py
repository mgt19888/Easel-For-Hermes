"""Hermes integration for the Easel fork (modified September 2026).

Uses the public CLI, not Hermes' private Python/database interfaces.
EASEL_RUNTIME=openclaw retains the upstream runtime for migration.
"""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def is_hermes() -> bool:
    value = os.environ.get("EASEL_RUNTIME", "hermes").strip().lower()
    if value not in {"hermes", "openclaw"}:
        raise ValueError("EASEL_RUNTIME must be hermes or openclaw")
    return value == "hermes"


def hermes_base() -> list[str]:
    cmd = [os.environ.get("EASEL_HERMES_BIN", "hermes")]
    profile = os.environ.get("EASEL_HERMES_PROFILE", "").strip()
    if profile:
        cmd += ["--profile", profile]
    return cmd


def session_name(key: str) -> str:
    # Scope to the checkout and hash untrusted web IDs; never use latest.
    digest = hashlib.sha256(f"{ROOT.resolve()}\0{key}".encode()).hexdigest()
    return f"easel-{digest}"


def prompt(message: str) -> str:
    rules = (ROOT / "openclaw/workspace/AGENTS.md").read_text(encoding="utf-8")
    rules = rules.replace("OpenClaw gateway", "Hermes Agent").replace("OpenClaw", "Hermes")
    rules = rules.replace("easel-profiles/", "profiles/")
    skills = sorted((ROOT / "skills/openclaw").glob("*/SKILL.md"))
    index = "\n".join(str(p.relative_to(ROOT)) for p in skills)
    return (f"{rules}\n\n## 运行时项目根\n{ROOT}\n"
            "在这个目录直接读取下面的 SKILL.md，并调用本项目脚本。"
            "skills/openclaw 是兼容保留的目录名，运行时为 Hermes。"
            "仅使用本轮指定画像，禁止读取或写入 Hermes 全局用户记忆。\n"
            "工具适配：旧技能的 web_search 对应 Hermes web_search；web_fetch 读取网页时"
            "使用 Hermes web_extract，读取 JSON API 时通过 terminal 运行 Python urllib.request。"
            "读取文件使用 read_file，执行脚本使用 terminal；按当前工具实际参数定义调用。"
            "不要调用不存在的 OpenClaw 工具或启动 OpenClaw 网关。\n"
            f"## 本地技能索引\n{index}\n\n## 本轮请求\n{message}")


def hermes_command(message: str, key: str, timeout: int,
                   *, interactive: bool = False) -> list[str]:
    cmd = hermes_base() + ["chat", "--continue", session_name(key),
                           "--create-if-missing", "--in", str(ROOT),
                           "--ignore-rules", "--run-budget", str(timeout)]
    if not interactive:
        cmd += ["--quiet", "--oneshot"]
    for variable, flag in (("EASEL_HERMES_MODEL", "--model"),
                           ("EASEL_HERMES_PROVIDER", "--provider")):
        if os.environ.get(variable):
            cmd += [flag, os.environ[variable]]
    return cmd + ["--query", prompt(message)]


def capability_check() -> tuple[bool, str]:
    if not shutil.which(hermes_base()[0]):
        return False, "未找到 Hermes；请按 docs/hermes.md 安装。"
    try:
        r = subprocess.run(hermes_base() + ["chat", "--help"],
                           capture_output=True, text=True, timeout=10)
        required = ("--create-if-missing", "--ignore-rules", "--run-budget", "--oneshot")
        if r.returncode or any(flag not in r.stdout for flag in required):
            return False, "Hermes 版本不支持所需 CLI 参数，请更新 Hermes。"
    except (OSError, subprocess.TimeoutExpired):
        return False, "Hermes CLI 无法启动。"
    return True, "Hermes CLI 可用；模型连通性请运行 easel ping。"


def doctor() -> int:
    ok, detail = capability_check()
    print(f"{'✓' if ok else '✗'} {detail}")
    for name in ("fastapi", "uvicorn", "sse_starlette", "multipart", "playwright"):
        import importlib.util
        found = importlib.util.find_spec(name) is not None
        print(f"{'✓' if found else '✗'} Python: {name}")
        ok &= found
    frontend = (ROOT / "web/frontend/dist/index.html").is_file()
    print(f"{'✓' if frontend else '✗'} Web 前端构建（npm ci && npm run build）")
    ok &= frontend
    ffmpeg = shutil.which("ffmpeg") is not None
    print(f"{'✓' if ffmpeg else '✗'} FFmpeg（媒体处理）")
    ok &= ffmpeg
    print("媒体生成所需 Key 仍在项目 .env；Hermes 模型配置使用 hermes setup。")
    return 0 if ok else 1
