# Easel · Hermes edition

本分支基于 [ZJU-REAL/Easel](https://github.com/ZJU-REAL/Easel) 二次开发，
原项目采用 Apache-2.0，保留原许可证和第三方来源声明。
2026-09 修改：默认运行时改为 Nous Research Hermes Agent。

## 安装与启动

先按 [Hermes 官方文档](https://hermes-agent.nousresearch.com/docs/) 安装 Hermes，
执行 `hermes setup` 配置模型。要求 `hermes chat --help` 包含
`--create-if-missing`、`--ignore-rules`、`--run-budget`、`--oneshot`。
还需要 Python >= 3.10、Node.js >= 22.19 和 FFmpeg。

macOS / Linux：

```bash
bash setup.sh
.venv/bin/python -m easel doctor
.venv/bin/python -m easel ping
.venv/bin/python -m easel web
```

Windows：使用 `python scripts/setup_hermes.py` 或 `./setup.ps1`，
后续命令中的 Python 换成 `.venv\Scripts\python.exe`。
Hermes 本身的平台支持以其官方安装说明为准。

打开 http://localhost:7860。命令行入口 `easel chat`、`easel skill` 同样使用 Hermes。
`easel ping` 会真实调用模型并产生相应费用；`easel doctor` 不调用模型。

## 配置

默认复用当前 Hermes 的模型/凭证配置，不复制或覆盖个人配置。
以下是启动 Easel 前设置的**进程环境变量**，不会从项目 `.env` 自动读取：

| 变量 | 用途 |
| --- | --- |
| `EASEL_RUNTIME` | 默认 `hermes`；设 `openclaw` 可使用保留的上游实现 |
| `EASEL_HERMES_BIN` | Hermes 可执行文件路径，默认 `hermes` |
| `EASEL_HERMES_PROFILE` | 可选，选择一个已创建的 Hermes profile |
| `EASEL_HERMES_MODEL` | 可选，仅覆盖本次模型 |
| `EASEL_HERMES_PROVIDER` | 可选，仅覆盖本次 provider |

媒体生成、发布服务的 Key 仍由 Easel 项目 `.env` 管理。
若使用独立 Hermes profile，请先通过 Hermes 自身配置该 profile，
并在 Easel 启动和 `ping` 时使用相同的 `EASEL_HERMES_PROFILE`。

## 接入行为与限制

- Web、技能执行、画像生成均通过 Hermes 公共 CLI 调用。无需 OpenClaw 网关。
- 每个 Easel 会话映射为包含项目路径的唯一 Hermes 会话名，支持跨轮续聊。
- 网页保留排队、停止、超时和断线后恢复。CLI 当前只给最终回复，所以等待期间显示执行状态，不伪造 token 流。
- 每轮注入 Easel 规则和本地技能路径索引；`--ignore-rules` 阻止自动注入个人全局规则/记忆。账号记忆仍在 `profiles/<画像>/memory.md`。
- `skills/openclaw/` 作为内容目录保留，以兼容技能间引用和共享脚本。目录名不表示依赖 OpenClaw；个别上游技能若直接调用 OpenClaw 专属工具，仍需逐项适配。
- 不自动迁移 OpenClaw 历史。旧网页会话第一次切到 Hermes 会建立新历史；建议新建对话。
- 状态灯仅表示 CLI 可用，模型/凭证是否有效用 `easel ping` 验证。
- Web 对话完成时记录 Hermes 返回的 session ID，删除操作调用 Hermes 自己的 session 删除命令，不修改其数据库。

## 验证记录

2026-09-10：67 项自动测试通过；React/TypeScript 生产构建通过；
本机 Hermes 真实模型 PONG 检查通过；通过 Web 的对话接口完成两轮续聊、
验证上一轮代号记忆，并成功调用 Hermes 删除该测试会话。
测试覆盖 CLI 参数和消息原样传递、项目会话隔离、成功/失败/空回复的 Web 回传与落盘。
当前测试 Python 环境缺少 Playwright，未实测平台登录与真实发布；
安装脚本会安装项目依赖和 Chromium。Windows 安装路径尚未实测。

迁移参考：[Hermes CLI](https://hermes-agent.nousresearch.com/docs/reference/cli-commands)。
