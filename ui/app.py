"""TUI do KAWA-AI: conversa local inspirada em agentes de terminal modernos."""

from __future__ import annotations

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Footer, Header, Input, Label, RichLog, Static
from textual import work

from ui.service import ConversationService, UICommand


class KawaTUI(App):
    """Interface leve: conversa central, contexto à esquerda e estado à direita."""

    TITLE = "KAWA-AI"
    SUB_TITLE = "Interface local de agente"
    CSS = """
    Screen { background: #101317; color: #d7dde6; }
    #layout { height: 1fr; }
    #sidebar { width: 29; background: #151a20; border-right: solid #26313d; padding: 1 2; }
    #chat-pane { width: 1fr; padding: 1 2; }
    #context { width: 31; background: #151a20; border-left: solid #26313d; padding: 1 2; }
    #chat { height: 1fr; background: #0d1014; border: round #304152; padding: 1; }
    #prompt { margin-top: 1; border: round #426784; background: #111820; }
    .section { color: #6fc3df; text-style: bold; margin-top: 1; }
    .muted { color: #8b98a7; }
    .mode-plan { color: #f6c453; text-style: bold; }
    .mode-build { color: #6ee7b7; text-style: bold; }
    """
    BINDINGS = [
        ("ctrl+p", "toggle_plan", "Plano/Execução"),
        ("ctrl+l", "clear_chat", "Limpar"),
        ("ctrl+k", "focus_input", "Mensagem"),
    ]

    def __init__(self, config: dict, workspace: str | None = None):
        super().__init__()
        self.service = ConversationService(config, workspace)
        self.plan_mode = False
        self.history: list[tuple[str, str]] = []

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Horizontal(id="layout"):
            with Vertical(id="sidebar"):
                yield Label("KAWA-AI", classes="section")
                yield Static("Agente local\nWorkspace, memória e ferramentas sob seu controle.", classes="muted")
                yield Label("SESSÃO", classes="section")
                yield Static("Ctrl+P  Plano / Execução\nCtrl+L  Limpar\nCtrl+K  Escrever", classes="muted")
                yield Label("ATALHOS", classes="section")
                yield Static("/skills\n/plan  /build\n/status  /help", classes="muted")
            with Vertical(id="chat-pane"):
                yield RichLog(id="chat", wrap=True, markup=True, highlight=True)
                yield Input(placeholder="Converse com KAWA-AI ou use /help…", id="prompt")
            with Vertical(id="context"):
                yield Label("CONTEXTO", classes="section")
                yield Static(f"Workspace\n{self.service.workspace}", id="workspace", classes="muted")
                yield Label("MODO", classes="section")
                yield Static("EXECUÇÃO PROATIVA", id="mode", classes="mode-build")
                yield Label("CAPACIDADES", classes="section")
                yield Static("Terminal\nMemória\nDesign\nAuditoria\nPentest ético\nSkills", classes="muted")
                yield Label("SEGURANÇA", classes="section")
                yield Static("Registros locais\nPolítica ativa\nEscopo de pentest", classes="muted")
        yield Footer()

    def on_mount(self) -> None:
        chat = self.query_one("#chat", RichLog)
        chat.write("[bold #6fc3df]KAWA-AI[/] [dim]• interface local[/]")
        chat.write("Olá. Estou pronto para planejar, criar, revisar e executar tarefas no seu workspace.")
        self.query_one("#prompt", Input).focus()

    def _mode_label(self) -> None:
        label = self.query_one("#mode", Static)
        if self.plan_mode:
            label.update("MODO PLANO • SOMENTE LEITURA")
            label.set_classes("mode-plan")
        else:
            label.update("EXECUÇÃO PROATIVA")
            label.set_classes("mode-build")

    def action_toggle_plan(self) -> None:
        self.plan_mode = not self.plan_mode
        self._mode_label()
        state = "plano somente leitura" if self.plan_mode else "execução proativa"
        self.query_one("#chat", RichLog).write(f"[dim]Modo alterado para {state}.[/]")

    def action_clear_chat(self) -> None:
        self.history.clear()
        self.query_one("#chat", RichLog).clear()

    def action_focus_input(self) -> None:
        self.query_one("#prompt", Input).focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        text = event.value.strip()
        if not text:
            return
        event.input.value = ""
        command = UICommand.parse(text)
        chat = self.query_one("#chat", RichLog)
        if command:
            if command.name == "plan":
                self.plan_mode = True
                self._mode_label()
                chat.write("[dim]Modo plano ativado.[/]")
                return
            if command.name == "build":
                self.plan_mode = False
                self._mode_label()
                chat.write("[dim]Modo execução ativado.[/]")
                return
            if command.name == "clear":
                self.action_clear_chat()
                return
            local = self.service.local_command(command)
            if local is not None:
                chat.write(f"[bold #f6c453]KAWA[/]\n{local}")
                return
        self.history.append(("user", text))
        chat.write(f"[bold #6fc3df]VOCÊ[/]\n{text}")
        chat.write("[dim]KAWA está analisando…[/]")
        self.run_agent(text)

    @work(thread=True, exclusive=True)
    def run_agent(self, text: str) -> None:
        result = self.service.run(text, plan_mode=self.plan_mode)
        self.call_from_thread(self._render_result, result)

    def _render_result(self, result: str) -> None:
        self.history.append(("assistant", result))
        self.query_one("#chat", RichLog).write(f"[bold #6ee7b7]KAWA[/]\n{result}")


def run_ui(config: dict, workspace: str | None = None) -> None:
    KawaTUI(config, workspace).run()
