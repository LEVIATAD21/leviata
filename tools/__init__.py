"""
Ferramentas do Agente de IA
Cada ferramenta pode ser executada pelo agente para interagir com o sistema.
"""
import subprocess
import os
import requests
from pathlib import Path
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


def _network_settings() -> tuple[float, int, float]:
    """Lê parâmetros de rede sem exigir alteração de código ou de credenciais."""
    try:
        timeout = max(1.0, float(os.environ.get("KAWA_NETWORK_TIMEOUT", "30")))
    except ValueError:
        timeout = 30.0
    try:
        retries = max(0, min(10, int(os.environ.get("KAWA_NETWORK_RETRIES", "3"))))
    except ValueError:
        retries = 3
    try:
        backoff = max(0.0, min(30.0, float(os.environ.get("KAWA_NETWORK_BACKOFF", "0.5"))))
    except ValueError:
        backoff = 0.5
    return timeout, retries, backoff


def _network_session() -> requests.Session:
    """Cria uma sessão resiliente; requests respeita HTTP(S)_PROXY do ambiente."""
    _, retries, backoff = _network_settings()
    retry = Retry(
        total=retries,
        connect=retries,
        read=retries,
        status=retries,
        backoff_factor=backoff,
        status_forcelist=(408, 425, 429, 500, 502, 503, 504),
        allowed_methods=frozenset({"GET", "HEAD", "OPTIONS"}),
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session = requests.Session()
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


def _network_get(url: str, **kwargs):
    timeout, _, _ = _network_settings()
    kwargs.setdefault("timeout", timeout)
    return _network_session().get(url, **kwargs)


def shell_execute(command: str) -> str:
    """
    Executa um comando no terminal Linux.
    Suporta comandos complexos, pipes, redirecionamentos, etc.
    """
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=120,
            cwd=os.getcwd()
        )
        output = ""
        if result.stdout:
            output += result.stdout
        if result.stderr:
            output += f"\n[STDERR]: {result.stderr}"
        if not output.strip():
            output = f"Comando executado com sucesso. Código de saída: {result.returncode}"
        return output
    except subprocess.TimeoutExpired:
        return "Erro: Comando excedeu o tempo limite de 120 segundos."
    except Exception as e:
        return f"Erro ao executar comando: {str(e)}"


def read_file(path: str) -> str:
    """Lê o conteúdo de um arquivo."""
    try:
        with open(os.path.expanduser(path), 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
        return content if content else "(arquivo vazio)"
    except FileNotFoundError:
        return f"Erro: Arquivo '{path}' não encontrado."
    except Exception as e:
        return f"Erro ao ler arquivo: {str(e)}"


def write_file(path: str, content: str) -> str:
    """Escreve conteúdo em um arquivo, criando diretórios se necessário."""
    try:
        full_path = Path(os.path.expanduser(path))
        full_path.parent.mkdir(parents=True, exist_ok=True)
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"Arquivo '{path}' escrito com sucesso ({len(content)} caracteres)."
    except Exception as e:
        return f"Erro ao escrever arquivo: {str(e)}"


def web_search(query: str) -> str:
    """Busca via instância SearXNG local configurada ou fallback DuckDuckGo."""
    try:
        searx_url = os.environ.get("KAWA_SEARXNG_URL", "").rstrip("/")
        if searx_url:
            try:
                response = _network_get(
                    f"{searx_url}/search",
                    params={"q": query, "format": "json"},
                )
                response.raise_for_status()
                results = response.json().get("results", [])[:5]
                if results:
                    return "\n".join(
                        f"- {item.get('title', 'Sem título')}: {item.get('url', '')}\n  {item.get('content', '')[:300]}"
                        for item in results
                    )
            except Exception:
                # Uma instância local indisponível não deve bloquear o fallback público.
                pass
        url = "https://api.duckduckgo.com/"
        params = {
            "q": query,
            "format": "json",
            "no_html": "1",
            "skip_disambig": "1"
        }
        response = _network_get(url, params=params)
        data = response.json()
        
        results = []
        if data.get("AbstractText"):
            results.append(f"Resumo: {data['AbstractText']}")
        
        for topic in data.get("RelatedTopics", [])[:5]:
            if isinstance(topic, dict) and topic.get("Text"):
                results.append(f"- {topic['Text']}")
        
        if not results:
            return f"Nenhum resultado encontrado para: {query}"
        
        return "\n".join(results)
    except Exception as e:
        return f"Erro na busca: {str(e)}"


def web_fetch(url: str) -> str:
    """Acessa uma URL e retorna o conteúdo em texto."""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
        }
        response = _network_get(url, headers=headers, allow_redirects=True)
        if len(response.content) > 2_000_000:
            return "Erro: resposta excede o limite de 2 MB para leitura local."
        response.raise_for_status()
        
        # Tenta extrair texto limpo se for HTML
        content_type = response.headers.get("content-type", "")
        if "html" in content_type:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')
            # Remove scripts e estilos
            for tag in soup(["script", "style", "nav", "footer"]):
                tag.decompose()
            text = soup.get_text(separator='\n', strip=True)
            # Limita o tamanho
            return text[:8000] + ("..." if len(text) > 8000 else "")
        else:
            return response.text[:8000]
    except Exception as e:
        return f"Erro ao acessar URL: {str(e)}"


def register_all_tools(agent, knowledge_brain=None, browser=None, media=None, quality=None, design=None, pentest=None, adversary=None, skill_builder=None, cybersecurity_catalog=None, secure_site=None):
    """Registra todas as ferramentas no agente."""
    agent.register_tool(
        "shell",
        lambda command: shell_execute(command),
        "Executa qualquer comando no terminal Linux. Input: {command: 'ls -la'}"
    )
    agent.register_tool(
        "read_file",
        lambda path: read_file(path),
        "Lê o conteúdo de um arquivo. Input: {path: '/caminho/arquivo.txt'}"
    )
    agent.register_tool(
        "write_file",
        lambda path, content: write_file(path, content),
        "Escreve conteúdo em um arquivo. Input: {path: '...', content: '...'}"
    )
    agent.register_tool(
        "web_search",
        lambda query: web_search(query),
        "Busca na web. Input: {query: 'sua busca aqui'}"
    )
    agent.register_tool(
        "web_fetch",
        lambda url: web_fetch(url),
        "Acessa uma URL e retorna o conteúdo. Input: {url: 'https://...'}"
    )
    if knowledge_brain:
        agent.register_tool(
            "knowledge_inquiry",
            lambda topic: knowledge_brain.inquire(topic, persist=True),
            "Investiga e registra um assunto por perguntas e fontes, sem executar comandos. Input: {topic: '...'}"
        )
    if browser:
        agent.register_tool(
            "browser_navigate",
            lambda url: browser.navigate(url),
            "Abre uma URL http(s) no Chromium local isolado. Input: {url: 'https://...'}"
        )
        agent.register_tool(
            "browser_read",
            lambda: browser.read(),
            "Lê texto visível da página atual do Chromium isolado. Input: {}"
        )
        agent.register_tool(
            "browser_click",
            lambda selector: browser.click(selector),
            "Clica em um seletor CSS após confirmação. Input: {selector: 'button'}"
        )
        agent.register_tool(
            "browser_type",
            lambda selector, text: browser.type(selector, text),
            "Preenche um seletor CSS após confirmação; conteúdo digitado é redigido na auditoria. Input: {selector: 'input', text: '...'}"
        )
        agent.register_tool(
            "browser_close",
            lambda: browser.close(),
            "Fecha a sessão isolada do navegador. Input: {}"
        )
    if media:
        agent.register_tool(
            "media_extract_frames",
            lambda input_path, fps=0.2: media.extract_frames(input_path, fps),
            "Extrai 0,05 a 2 quadros por segundo para a pasta de trabalho após confirmação. Input: {input_path: 'video.mp4', fps: 0.2}"
        )
        agent.register_tool(
            "media_transcribe",
            lambda input_path: media.transcribe(input_path),
            "Transcreve áudio ou vídeo por whisper.cpp após confirmação. Input: {input_path: 'audio.mp3'}"
        )
    if quality:
        agent.register_tool(
            "quality_audit",
            lambda target_path=".", tools=None: quality.audit(target_path, tools),
            "Executa Ruff, Bandit e Semgrep de modo estático dentro do diretório de trabalho. Input: {target_path: '.', tools: ['ruff', 'bandit']}"
        )
    if design:
        agent.register_tool(
            "design_brief",
            lambda request, medium="produto-digital": design.create_brief(request, medium),
            "Cria brief de design e diagrama Mermaid editáveis dentro do diretório de trabalho. Input: {request: '...', medium: 'site'}"
        )
    if secure_site:
        agent.register_tool(
            "secure_site_cycle",
            lambda site_name="site-seguro", title=None, maximum_cycles=3: secure_site.run(site_name, title, maximum_cycles),
            "Cria um site de referência somente local, executa gate estático de segurança, registra evidências e bloqueia conclusão se houver achados. Não publica, não abre portas públicas e não executa ataques de rede. Input: {site_name: 'portfolio', title: 'Meu site', maximum_cycles: 3}"
        )
    if pentest:
        agent.register_tool(
            "ethical_pentest",
            lambda target_path=".", tools=None: pentest.audit(target_path, tools),
            "Audita somente um projeto local já autorizado pelo arquivo de escopo; não faz varredura de rede, exploração ou ataque de credenciais. Input: {target_path: '.', tools: ['ruff', 'bandit', 'semgrep']}"
        )
    if adversary:
        agent.register_tool(
            "adversary_simulate",
            lambda target_path=".": adversary.simulate(target_path),
            "Simula ameaças (OWASP Top 10 e MITRE ATT&CK) e gera recomendações preventivas de hardening. Input: {target_path: '.'}"
        )
    if skill_builder:
        agent.register_tool(
            "skill_materialize",
            lambda source_path, skill_name=None, output_dir=None: skill_builder.build(source_path, skill_name, output_dir),
            "Estrutura material local fornecido pelo usuário em um pacote SKILL.md com capítulos dentro do workspace. Input: {source_path: 'docs/manual.md', skill_name: 'manual'}"
        )
    if cybersecurity_catalog:
        agent.register_tool(
            "cybersecurity_reference",
            lambda topic, include_restricted=False, limit=8: cybersecurity_catalog.render(topic, include_restricted, limit),
            "Consulta o catálogo local de referências de cibersegurança. É somente leitura: separa referências defensivas, técnicas que exigem escopo autorizado e itens restritos; não executa scripts, scanners ou exploits. Input: {topic: 'hardening de API', include_restricted: false, limit: 8}"
        )
