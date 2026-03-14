"""CLI commands for nanobot."""

import asyncio
import os
import select
import signal
import sys
from pathlib import Path

# Force UTF-8 encoding for Windows console
if sys.platform == "win32":
    import locale

    if sys.stdout.encoding != "utf-8":
        os.environ["PYTHONIOENCODING"] = "utf-8"
        # Re-open stdout/stderr with UTF-8 encoding
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

import typer
from prompt_toolkit import PromptSession
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.history import FileHistory
from prompt_toolkit.patch_stdout import patch_stdout
from rich.console import Console
from rich.markdown import Markdown
from rich.table import Table
from rich.text import Text

from weisensebot import __logo__, __version__
from weisensebot.config.schema import Config
from weisensebot.utils.helpers import sync_workspace_templates

app = typer.Typer(
    name="weisensebot",
    help=f"{__logo__} 维思机器人 (Weisensebot) - 个人AI助手",
    no_args_is_help=True,
)

console = Console()
EXIT_COMMANDS = {"exit", "quit", "/exit", "/quit", ":q"}

# ---------------------------------------------------------------------------
# CLI input: prompt_toolkit for editing, paste, history, and display
# ---------------------------------------------------------------------------

_PROMPT_SESSION: PromptSession | None = None
_SAVED_TERM_ATTRS = None  # original termios settings, restored on exit


def _flush_pending_tty_input() -> None:
    """Drop unread keypresses typed while the model was generating output."""
    try:
        fd = sys.stdin.fileno()
        if not os.isatty(fd):
            return
    except Exception:
        return

    try:
        import termios

        termios.tcflush(fd, termios.TCIFLUSH)
        return
    except Exception:
        pass

    try:
        while True:
            ready, _, _ = select.select([fd], [], [], 0)
            if not ready:
                break
            if not os.read(fd, 4096):
                break
    except Exception:
        return


def _restore_terminal() -> None:
    """Restore terminal to its original state (echo, line buffering, etc.)."""
    if _SAVED_TERM_ATTRS is None:
        return
    try:
        import termios

        termios.tcsetattr(sys.stdin.fileno(), termios.TCSADRAIN, _SAVED_TERM_ATTRS)
    except Exception:
        pass


def _init_prompt_session() -> None:
    """Create the prompt_toolkit session with persistent file history."""
    global _PROMPT_SESSION, _SAVED_TERM_ATTRS

    # Save terminal state so we can restore it on exit
    try:
        import termios

        _SAVED_TERM_ATTRS = termios.tcgetattr(sys.stdin.fileno())
    except Exception:
        pass

    history_file = Path.home() / ".weisensebot" / "history" / "cli_history"
    history_file.parent.mkdir(parents=True, exist_ok=True)

    _PROMPT_SESSION = PromptSession(
        history=FileHistory(str(history_file)),
        enable_open_in_editor=False,
        multiline=False,  # Enter submits (single line mode)
    )


def _print_agent_response(response: str, render_markdown: bool) -> None:
    """Render assistant response with consistent terminal styling."""
    content = response or ""
    body = Markdown(content) if render_markdown else Text(content)
    console.print()
    console.print(f"[cyan]{__logo__} weisensebot[/cyan]")
    console.print(body)
    console.print()


def _is_exit_command(command: str) -> bool:
    """Return True when input should end interactive chat."""
    return command.lower() in EXIT_COMMANDS


async def _read_interactive_input_async() -> str:
    """Read user input using prompt_toolkit (handles paste, history, display).

    prompt_toolkit natively handles:
    - Multiline paste (bracketed paste mode)
    - History navigation (up/down arrows)
    - Clean display (no ghost characters or artifacts)
    """
    if _PROMPT_SESSION is None:
        raise RuntimeError("Call _init_prompt_session() first")
    try:
        with patch_stdout():
            return await _PROMPT_SESSION.prompt_async(
                HTML("<b fg='ansiblue'>You:</b> "),
            )
    except EOFError as exc:
        raise KeyboardInterrupt from exc


def version_callback(value: bool):
    if value:
        console.print(f"{__logo__} weisensebot v{__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(None, "--version", "-v", callback=version_callback, is_eager=True),
):
    """维思机器人 (Weisensebot) - 个人AI助手。"""
    pass


# ============================================================================
# Onboard / Setup
# ============================================================================


@app.command()
def onboard():
    """初始化维思机器人配置和工作区。"""
    from weisensebot.config.loader import get_config_path, load_config, save_config
    from weisensebot.config.schema import Config
    from weisensebot.utils.helpers import get_workspace_path

    config_path = get_config_path()

    if config_path.exists():
        console.print(f"[yellow]配置文件已存在: {config_path}[/yellow]")
        console.print("  [bold]y[/bold] = 覆盖为默认值（现有值将丢失）")
        console.print("  [bold]N[/bold] = 刷新配置，保留现有值并添加新字段")
        if typer.confirm("是否覆盖？"):
            config = Config()
            save_config(config)
            console.print(f"[green]✓[/green] 已在 {config_path} 重置配置为默认值")
        else:
            config = load_config()
            save_config(config)
            console.print(f"[green]✓[/green] 已在 {config_path} 刷新配置（保留了现有值）")
    else:
        save_config(Config())
        console.print(f"[green]✓[/green] 已在 {config_path} 创建配置")

    # 创建工作区
    workspace = get_workspace_path()

    if not workspace.exists():
        workspace.mkdir(parents=True, exist_ok=True)
        console.print(f"[green]✓[/green] 已在工作区创建: {workspace}")

    sync_workspace_templates(workspace)

    console.print(f"\n{__logo__} 维思机器人已就绪！")
    console.print("\n下一步:")
    console.print("  1. 将您的API密钥添加到 [cyan]~/.weisensebot/config.json[/cyan]")
    console.print("     获取密钥: https://openrouter.ai/keys")
    console.print('  2. 开始聊天: [cyan]weisensebot agent -m "你好！[/cyan]')
    console.print(
        "\n[dim]微妙物联人工智能实验室 2026.03 Gaoshine.[/dim]"
    )


def _make_provider(config: Config):
    """Create the appropriate LLM provider from config."""
    from weisensebot.providers.openai_codex_provider import OpenAICodexProvider
    from weisensebot.providers.azure_openai_provider import AzureOpenAIProvider
    from weisensebot.providers.registry import find_by_name

    model = config.agents.defaults.model
    provider_name = config.get_provider_name(model)
    p = config.get_provider(model)

    spec = find_by_name(provider_name) if provider_name else None

    if config.agents.defaults.provider != "auto" and spec is None:
        console.print(f"[red]Error: Unknown provider: {config.agents.defaults.provider}[/red]")
        console.print("Check ~/.weisensebot/config.json under agents.defaults.provider")
        raise typer.Exit(1)
    
    # OpenAI Codex (OAuth)
    if provider_name == "openai_codex" or model.startswith("openai-codex/"):
        return OpenAICodexProvider(default_model=model)

    # Custom: direct OpenAI-compatible endpoint, bypasses LiteLLM
    from weisensebot.providers.custom_provider import CustomProvider

    api_base = config.get_api_base(model)
    if provider_name == "ollama":
        api_base = (api_base or "http://localhost:11434").rstrip("/")
        return CustomProvider(
            api_key=p.api_key if p else "no-key",
            api_base=api_base,
            default_model=model,
        )

    if provider_name == "custom":
        return CustomProvider(
            api_key=p.api_key if p else "no-key",
            api_base=config.get_api_base(model) or "http://localhost:8000/v1",
            default_model=model,
        )

    # Azure OpenAI: direct Azure OpenAI endpoint with deployment name
    if provider_name == "azure_openai":
        if not p or not p.api_key or not p.api_base:
            console.print("[red]错误：Azure OpenAI 需要 api_key 和 api_base。[/red]")
            console.print("在 ~/.weisensebot/config.json 的 providers.azure_openai 部分设置它们")
            console.print("使用 model 字段指定部署名称。")
            raise typer.Exit(1)

        return AzureOpenAIProvider(
            api_key=p.api_key,
            api_base=p.api_base,
            default_model=model,
        )

    from weisensebot.providers.litellm_provider import LiteLLMProvider
    from weisensebot.providers.registry import find_by_name

    spec = find_by_name(provider_name)
    if not model.startswith("bedrock/") and not (p and p.api_key) and not (spec and spec.is_oauth):
        console.print("[red]错误：未配置 API 密钥。[/red]")
        console.print("在 ~/.weisensebot/config.json 的 providers 部分设置一个")
        raise typer.Exit(1)

    return LiteLLMProvider(
        api_key=p.api_key if p else None,
        api_base=config.get_api_base(model),
        default_model=model,
        extra_headers=p.extra_headers if p else None,
        provider_name=provider_name,
    )


# ============================================================================
# Gateway / Server
# ============================================================================


@app.command()
def gateway(
    port: int = typer.Option(18790, "--port", "-p", help="Gateway port"),
    workspace: str | None = typer.Option(None, "--workspace", "-w", help="Workspace directory"),
    config: str | None = typer.Option(None, "--config", "-c", help="Config file path"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
):
    """启动维思机器人网关服务器。"""
    from weisensebot.agent.loop import AgentLoop
    from weisensebot.bus.queue import MessageBus
    from weisensebot.channels.manager import ChannelManager
    from weisensebot.config.loader import load_config
    from weisensebot.cron.service import CronService
    from weisensebot.cron.types import CronJob
    from weisensebot.heartbeat.service import HeartbeatService
    from weisensebot.session.manager import SessionManager

    if verbose:
        import logging

        logging.basicConfig(level=logging.DEBUG)

    config_path = Path(config) if config else None
    config = load_config(config_path)
    if workspace:
        config.agents.defaults.workspace = workspace

    console.print(f"{__logo__} 正在启动维思机器人网关，端口 {port}...")
    sync_workspace_templates(config.workspace_path)
    bus = MessageBus()
    provider = _make_provider(config)
    session_manager = SessionManager(config.workspace_path)

    # Create cron service first (callback set after agent creation)
    # Use workspace path for per-instance cron store
    cron_store_path = config.workspace_path / "cron" / "jobs.json"
    cron = CronService(cron_store_path)

    # Create agent with cron service
    agent = AgentLoop(
        bus=bus,
        provider=provider,
        workspace=config.workspace_path,
        model=config.agents.defaults.model,
        temperature=config.agents.defaults.temperature,
        max_tokens=config.agents.defaults.max_tokens,
        max_iterations=config.agents.defaults.max_tool_iterations,
        memory_window=config.agents.defaults.memory_window,
        reasoning_effort=config.agents.defaults.reasoning_effort,
        brave_api_key=config.tools.web.search.api_key or None,
        web_proxy=config.tools.web.proxy or None,
        exec_config=config.tools.exec,
        cron_service=cron,
        restrict_to_workspace=config.tools.restrict_to_workspace,
        session_manager=session_manager,
        mcp_servers=config.tools.mcp_servers,
        channels_config=config.channels,
    )

    # Set cron callback (needs agent)
    async def on_cron_job(job: CronJob) -> str | None:
        """Execute a cron job through the agent."""
        from weisensebot.agent.tools.cron import CronTool
        from weisensebot.agent.tools.message import MessageTool

        reminder_note = (
            "[Scheduled Task] Timer finished.\n\n"
            f"Task '{job.name}' has been triggered.\n"
            f"Scheduled instruction: {job.payload.message}"
        )

        # Prevent the agent from scheduling new cron jobs during execution
        cron_tool = agent.tools.get("cron")
        cron_token = None
        if isinstance(cron_tool, CronTool):
            cron_token = cron_tool.set_cron_context(True)
        try:
            response = await agent.process_direct(
                reminder_note,
                session_key=f"cron:{job.id}",
                channel=job.payload.channel or "cli",
                chat_id=job.payload.to or "direct",
            )
        finally:
            if isinstance(cron_tool, CronTool) and cron_token is not None:
                cron_tool.reset_cron_context(cron_token)

        message_tool = agent.tools.get("message")
        if isinstance(message_tool, MessageTool) and message_tool._sent_in_turn:
            return response

        if job.payload.deliver and job.payload.to and response:
            from weisensebot.bus.events import OutboundMessage

            await bus.publish_outbound(
                OutboundMessage(
                    channel=job.payload.channel or "cli", chat_id=job.payload.to, content=response
                )
            )
        return response

    cron.on_job = on_cron_job

    # Create channel manager
    channels = ChannelManager(config, bus)

    def _pick_heartbeat_target() -> tuple[str, str]:
        """Pick a routable channel/chat target for heartbeat-triggered messages."""
        enabled = set(channels.enabled_channels)
        # Prefer the most recently updated non-internal session on an enabled channel.
        for item in session_manager.list_sessions():
            key = item.get("key") or ""
            if ":" not in key:
                continue
            channel, chat_id = key.split(":", 1)
            if channel in {"cli", "system"}:
                continue
            if channel in enabled and chat_id:
                return channel, chat_id
        # Fallback keeps prior behavior but remains explicit.
        return "cli", "direct"

    # Create heartbeat service
    async def on_heartbeat_execute(tasks: str) -> str:
        """Phase 2: execute heartbeat tasks through the full agent loop."""
        channel, chat_id = _pick_heartbeat_target()

        async def _silent(*_args, **_kwargs):
            pass

        return await agent.process_direct(
            tasks,
            session_key="heartbeat",
            channel=channel,
            chat_id=chat_id,
            on_progress=_silent,
        )

    async def on_heartbeat_notify(response: str) -> None:
        """Deliver a heartbeat response to the user's channel."""
        from weisensebot.bus.events import OutboundMessage

        channel, chat_id = _pick_heartbeat_target()
        if channel == "cli":
            return  # No external channel available to deliver to
        await bus.publish_outbound(
            OutboundMessage(channel=channel, chat_id=chat_id, content=response)
        )

    hb_cfg = config.gateway.heartbeat
    heartbeat = HeartbeatService(
        workspace=config.workspace_path,
        provider=provider,
        model=agent.model,
        on_execute=on_heartbeat_execute,
        on_notify=on_heartbeat_notify,
        interval_s=hb_cfg.interval_s,
        enabled=hb_cfg.enabled,
    )

    if channels.enabled_channels:
        console.print(f"[green]✓[/green] 已启用的频道: {', '.join(channels.enabled_channels)}")
    else:
        console.print("[yellow]警告：未启用任何频道[/yellow]")

    cron_status = cron.status()
    if cron_status["jobs"] > 0:
        console.print(f"[green]✓[/green] 定时任务: {cron_status['jobs']} 个已安排的任务")

        console.print(f"[green]✓[/green] 心跳: 每 {hb_cfg.interval_s} 秒")

    async def run():
        try:
            await cron.start()
            await heartbeat.start()
            await asyncio.gather(
                agent.run(),
                channels.start_all(),
            )
        except KeyboardInterrupt:
            console.print("\n正在关闭...")
        finally:
            await agent.close_mcp()
            heartbeat.stop()
            cron.stop()
            agent.stop()
            await channels.stop_all()

    asyncio.run(run())


# ============================================================================
# Agent Commands
# ============================================================================


@app.command()
def agent(
    message: str = typer.Option(None, "--message", "-m", help="Message to send to the agent"),
    session_id: str = typer.Option("cli:direct", "--session", "-s", help="Session ID"),
    markdown: bool = typer.Option(
        True, "--markdown/--no-markdown", help="Render assistant output as Markdown"
    ),
    logs: bool = typer.Option(
        False, "--logs/--no-logs", help="Show weisensebot  runtime logs during chat"
    ),
):
    """与AI智能体直接交互。"""
    from loguru import logger

    from weisensebot.agent.loop import AgentLoop
    from weisensebot.bus.queue import MessageBus
    from weisensebot.config.loader import get_data_dir, load_config
    from weisensebot.cron.service import CronService

    config = load_config()
    sync_workspace_templates(config.workspace_path)

    bus = MessageBus()
    provider = _make_provider(config)

    # Create cron service for tool usage (no callback needed for CLI unless running)
    cron_store_path = get_data_dir() / "cron" / "jobs.json"
    cron = CronService(cron_store_path)

    if logs:
        logger.enable("weisensebot")
    else:
        logger.disable("weisensebot")

    agent_loop = AgentLoop(
        bus=bus,
        provider=provider,
        workspace=config.workspace_path,
        model=config.agents.defaults.model,
        temperature=config.agents.defaults.temperature,
        max_tokens=config.agents.defaults.max_tokens,
        max_iterations=config.agents.defaults.max_tool_iterations,
        memory_window=config.agents.defaults.memory_window,
        reasoning_effort=config.agents.defaults.reasoning_effort,
        brave_api_key=config.tools.web.search.api_key or None,
        web_proxy=config.tools.web.proxy or None,
        exec_config=config.tools.exec,
        cron_service=cron,
        restrict_to_workspace=config.tools.restrict_to_workspace,
        mcp_servers=config.tools.mcp_servers,
        channels_config=config.channels,
    )

    # Show spinner when logs are off (no output to miss); skip when logs are on
    def _thinking_ctx():
        if logs:
            from contextlib import nullcontext

            return nullcontext()
        # Animated spinner is safe to use with prompt_toolkit input handling
        return console.status("[dim]维思机器人正在思考...[/dim]", spinner="dots")

    async def _cli_progress(content: str, *, tool_hint: bool = False) -> None:
        ch = agent_loop.channels_config
        if ch and tool_hint and not ch.send_tool_hints:
            return
        if ch and not tool_hint and not ch.send_progress:
            return
        console.print(f"  [dim]↳ {content}[/dim]")

    if message:
        # Single message mode — direct call, no bus needed
        async def run_once():
            with _thinking_ctx():
                response = await agent_loop.process_direct(
                    message, session_id, on_progress=_cli_progress
                )
            _print_agent_response(response, render_markdown=markdown)
            await agent_loop.close_mcp()

        asyncio.run(run_once())
    else:
        # Interactive mode — route through bus like other channels
        from weisensebot.bus.events import InboundMessage

        _init_prompt_session()
        console.print(
            f"{__logo__} 交互模式 (输入 [bold]exit[/bold] 或 [bold]Ctrl+C[/bold] 可以退出)\n [dim]微妙物联人工智能实验室 2026.03 Gaoshine.[/dim]"
        )

        if ":" in session_id:
            cli_channel, cli_chat_id = session_id.split(":", 1)
        else:
            cli_channel, cli_chat_id = "cli", session_id

        def _handle_signal(signum, frame):
            sig_name = signal.Signals(signum).name
            _restore_terminal()
            console.print(f"\n收到 {sig_name} 信号，再见！")
            sys.exit(0)

        signal.signal(signal.SIGINT, _handle_signal)
        signal.signal(signal.SIGTERM, _handle_signal)
        # SIGHUP is not available on Windows
        if hasattr(signal, "SIGHUP"):
            signal.signal(signal.SIGHUP, _handle_signal)
        # Ignore SIGPIPE to prevent silent process termination when writing to closed pipes
        # SIGPIPE is not available on Windows
        if hasattr(signal, "SIGPIPE"):
            signal.signal(signal.SIGPIPE, signal.SIG_IGN)

        async def run_interactive():
            bus_task = asyncio.create_task(agent_loop.run())
            turn_done = asyncio.Event()
            turn_done.set()
            turn_response: list[str] = []

            async def _consume_outbound():
                while True:
                    try:
                        msg = await asyncio.wait_for(bus.consume_outbound(), timeout=1.0)
                        if msg.metadata.get("_progress"):
                            is_tool_hint = msg.metadata.get("_tool_hint", False)
                            ch = agent_loop.channels_config
                            if ch and is_tool_hint and not ch.send_tool_hints:
                                pass
                            elif ch and not is_tool_hint and not ch.send_progress:
                                pass
                            else:
                                console.print(f"  [dim]↳ {msg.content}[/dim]")
                        elif not turn_done.is_set():
                            if msg.content:
                                turn_response.append(msg.content)
                            turn_done.set()
                        elif msg.content:
                            console.print()
                            _print_agent_response(msg.content, render_markdown=markdown)
                    except asyncio.TimeoutError:
                        continue
                    except asyncio.CancelledError:
                        break

            outbound_task = asyncio.create_task(_consume_outbound())

            try:
                while True:
                    try:
                        _flush_pending_tty_input()
                        user_input = await _read_interactive_input_async()
                        command = user_input.strip()
                        if not command:
                            continue

                        if _is_exit_command(command):
                            _restore_terminal()
                            console.print("\n再见！")
                            break

                        turn_done.clear()
                        turn_response.clear()

                        await bus.publish_inbound(
                            InboundMessage(
                                channel=cli_channel,
                                sender_id="user",
                                chat_id=cli_chat_id,
                                content=user_input,
                            )
                        )

                        with _thinking_ctx():
                            await turn_done.wait()

                        if turn_response:
                            _print_agent_response(turn_response[0], render_markdown=markdown)
                    except KeyboardInterrupt:
                        _restore_terminal()
                        console.print("\n再见！")
                        break
                    except EOFError:
                        _restore_terminal()
                        console.print("\n再见！")
                        break
            finally:
                agent_loop.stop()
                outbound_task.cancel()
                await asyncio.gather(bus_task, outbound_task, return_exceptions=True)
                await agent_loop.close_mcp()

        asyncio.run(run_interactive())


# ============================================================================
# Channel Commands
# ============================================================================


channels_app = typer.Typer(help="管理聊天频道")
app.add_typer(channels_app, name="channels")


@channels_app.command("status")
def channels_status():
    """显示频道状态。"""
    from weisensebot.config.loader import load_config

    config = load_config()

    table = Table(title="频道状态")
    table.add_column("Channel", style="cyan")
    table.add_column("Enabled", style="green")
    table.add_column("Configuration", style="yellow")

    dc = config.channels.discord
    table.add_row("Discord", "✓" if dc.enabled else "✗", dc.gateway_url)

    # Feishu
    fs = config.channels.feishu
    fs_config = f"app_id: {fs.app_id[:10]}..." if fs.app_id else "[dim]not configured[/dim]"
    table.add_row("Feishu", "✓" if fs.enabled else "✗", fs_config)

    # Mochat
    mc = config.channels.mochat
    mc_base = mc.base_url or "[dim]not configured[/dim]"
    table.add_row("Mochat", "✓" if mc.enabled else "✗", mc_base)

    # Mochat
    slack = config.channels.slack
    slack_config = "socket" if slack.app_token and slack.bot_token else "[dim]not configured[/dim]"
    table.add_row("Slack", "✓" if slack.enabled else "✗", slack_config)

    # DingTalk
    dt = config.channels.dingtalk
    dt_config = (
        f"client_id: {dt.client_id[:10]}..." if dt.client_id else "[dim]not configured[/dim]"
    )
    table.add_row("DingTalk", "✓" if dt.enabled else "✗", dt_config)

    # Wecom
    wx = config.channels.wecom
    wx_config = (
        f"bot_id: {wx.bot_id[:10]}..." if wx.bot_id else "[dim]not configured[/dim]"
    )
    table.add_row("Wecom", "✓" if wx.enabled else "✗", wx_config)

    # QQ
    qq = config.channels.qq
    qq_config = f"app_id: {qq.app_id[:10]}..." if qq.app_id else "[dim]not configured[/dim]"
    table.add_row("QQ", "✓" if qq.enabled else "✗", qq_config)

    # Email
    em = config.channels.email
    em_config = em.imap_host if em.imap_host else "[dim]not configured[/dim]"
    table.add_row("Email", "✓" if em.enabled else "✗", em_config)

    # Matrix
    mx = config.channels.matrix
    mx_config = (
        f"homeserver: {mx.homeserver[:20]}..." if mx.homeserver else "[dim]not configured[/dim]"
    )
    table.add_row("Matrix", "✓" if mx.enabled else "✗", mx_config)

    console.print(table)


# ============================================================================
# Status Commands
# ============================================================================


@app.command()
def status():
    """显示维思机器人状态。"""
    from weisensebot.config.loader import get_config_path, load_config

    config_path = get_config_path()
    config = load_config()
    workspace = config.workspace_path

    console.print(f"{__logo__} 维思机器人状态\n")

    console.print(
        f"配置文件: {config_path} {'[green]✓[/green]' if config_path.exists() else '[red]✗[/red]'}"
    )
    console.print(
        f"工作空间: {workspace} {'[green]✓[/green]' if workspace.exists() else '[red]✗[/red]'}"
    )

    if config_path.exists():
        from weisensebot.providers.registry import PROVIDERS

        console.print(f"模型: {config.agents.defaults.model}")

        # 从注册表检查 API keys
        for spec in PROVIDERS:
            p = getattr(config.providers, spec.name, None)
            if p is None:
                continue
            if spec.is_local:
                # 本地部署显示 api_base 而不是 api_key
                if p.api_base:
                    console.print(f"{spec.label}: [green]✓ {p.api_base}[/green]")
                else:
                    console.print(f"{spec.label}: [dim]未设置[/dim]")
            else:
                has_key = bool(p.api_key)
                console.print(
                    f"{spec.label}: {'[green]✓[/green]' if has_key else '[dim]未设置[/dim]'}"
                )


# ============================================================================
# OAuth Login - OAuth认证登录
# ============================================================================

provider_app = typer.Typer(help="管理LLM提供商")
app.add_typer(provider_app, name="provider")

_LOGIN_HANDLERS: dict[str, callable] = {}


def _register_login(name: str):
    def decorator(fn):
        _LOGIN_HANDLERS[name] = fn
        return fn

    return decorator


@provider_app.command("login")
def provider_login(
    provider: str = typer.Argument(
        ..., help="OAuth provider (e.g. 'openai-codex', 'github-copilot')"
    ),
):
    """使用OAuth提供商进行认证。"""
    from weisensebot.providers.registry import PROVIDERS

    key = provider.replace("-", "_")
    spec = next((s for s in PROVIDERS if s.name == key and s.is_oauth), None)
    if not spec:
        names = ", ".join(s.name.replace("_", "-") for s in PROVIDERS if s.is_oauth)
        console.print(f"[red]未知的 OAuth 提供商: {provider}[/red]  支持的: {names}")
        raise typer.Exit(1)

    handler = _LOGIN_HANDLERS.get(spec.name)
    if not handler:
        console.print(f"[red]尚未实现 {spec.label} 的登录功能[/red]")
        raise typer.Exit(1)

    handler = _LOGIN_HANDLERS.get(spec.name)
    if not handler:
        console.print(f"[red]尚未实现 {spec.label} 的登录功能[/red]")
        raise typer.Exit(1)

    console.print(f"{__logo__} OAuth 登录 - {spec.label}\n")
    handler()


@_register_login("openai_codex")
def _login_openai_codex() -> None:
    try:
        from oauth_cli_kit import get_token, login_oauth_interactive

        token = None
        try:
            token = get_token()
        except Exception:
            pass
        if not (token and token.access):
            console.print("[cyan]启动交互式 OAuth 登录...[/cyan]\n")
            token = login_oauth_interactive(
                print_fn=lambda s: console.print(s),
                prompt_fn=lambda s: typer.prompt(s),
            )
        if not (token and token.access):
            console.print("[red]✗ 身份验证失败[/red]")
            raise typer.Exit(1)
        console.print(f"[green]✓ 已通过 OpenAI Codex 验证[/green]  [dim]{token.account_id}[/dim]")
    except ImportError:
        console.print("[red]未安装 oauth_cli_kit。运行: pip install oauth-cli-kit[/red]")
        raise typer.Exit(1)


@_register_login("github_copilot")
def _login_github_copilot() -> None:
    import asyncio

    console.print("[cyan]启动 GitHub Copilot 设备流程...[/cyan]\n")

    async def _trigger():
        from litellm import acompletion

        await acompletion(
            model="github_copilot/gpt-4o",
            messages=[{"role": "user", "content": "hi"}],
            max_tokens=1,
        )

    try:
        asyncio.run(_trigger())
        console.print("[green]✓ 已通过 GitHub Copilot 验证[/green]")
    except Exception as e:
        console.print(f"[red]身份验证错误: {e}[/red]")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
