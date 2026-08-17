"""TUI do Leviatã: conversa local inspirada em agentes de terminal modernos."""

from __future__ import annotations

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Footer, Header, Input, Label, RichLog, Static
from textual import work

from ui.service import ConversationService, UICommand


class LeviataTUI(App):
    """Interface leve: conversa central, contexto à esquerda e estado à direita."""

    TITLE = "LEVIATÃ"
    SUB_TITLE = "Núcleo local de orquestração"
    CSS = """
    Screen { background: #07111f; color: #d8fff7; }
    #layout { height: 1fr; }
    #sidebar { width: 29; background: #0b1d2b; border-right: solid #165166; padding: 1 2; }
    #chat-pane { width: 1fr; padding: 1 2; }
    #context { width: 31; background: #0b1d2b; border-left: solid #165166; padding: 1 2; }
    #chat { height: 1fr; background: #06101a; border: round #267c88; padding: 1; }
    #prompt { margin-top: 1; border: round #31bca9; background: #0b1d2b; }
    .section { color: #70f0d2; text-style: bold; margin-top: 1; }
    .muted { color: #9ac7d0; }
    .mode-plan { color: #f3c969; text-style: bold; }
    .mode-build { color: #70f0d2; text-style: bold; }
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
                yield Label("LEVIATÃ", classes="section")
                yield Static("Agente local\nWorkspace, memória e ferramentas sob seu controle.", classes="muted")
                yield Label("SESSÃO", classes="section")
                yield Static("Ctrl+P  Plano / Execução\nCtrl+L  Limpar\nCtrl+K  Escrever", classes="muted")
                yield Label("ATALHOS", classes="section")
                yield Static("/skills\n/plan  /build\n/status  /help", classes="muted")
            with Vertical(id="chat-pane"):
                yield RichLog(id="chat", wrap=True, markup=True, highlight=True)
                yield Input(placeholder="Converse com Leviatã ou use /help…", id="prompt")
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
        chat.write("[bold #70f0d2]LEVIATÃ[/] [dim]• núcleo local de orquestração[/]")
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
                chat.write(f"[bold #f3c969]LEVIATÃ[/]\n{local}")
                return
        self.history.append(("user", text))
        chat.write(f"[bold #6fc3df]VOCÊ[/]\n{text}")
        chat.write("[dim]Leviatã está analisando…[/]")
        self.run_agent(text)

    @work(thread=True, exclusive=True)
    def run_agent(self, text: str) -> None:
        result = self.service.run(text, plan_mode=self.plan_mode)
        self.call_from_thread(self._render_result, result)

    def _render_result(self, result: str) -> None:
        self.history.append(("assistant", result))
        self.query_one("#chat", RichLog).write(f"[bold #70f0d2]LEVIATÃ[/]\n{result}")


def run_ui(config: dict, workspace: str | None = None) -> None:
    LeviataTUI(config, workspace).run()
