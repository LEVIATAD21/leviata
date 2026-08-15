"""
KAWA-AI Multiagent Orchestrator
Coordena múltiplos agentes especialistas em sequência, com atraso configurável
entre as respostas, transcript compartilhado e tomada de decisão colaborativa.
"""
import time
import sys
from typing import List, Dict, Any

class AgentSpecialist:
    def __init__(self, name: str, role: str, provider: Any):
        self.name = name
        self.role = role
        self.provider = provider
        self.memory: List[Dict[str, str]] = []

    def speak(self, task: str, shared_transcript: List[Dict[str, str]], delay: int = 50) -> str:
        """Especialista analisa o histórico compartilhado e gera sua contribuição."""
        system_prompt = f"""Você é {self.name}, atuando como {self.role} na equipe de IA autônoma KAWA-AI.
Sua missão é colaborar com outros agentes especialistas para resolver a tarefa do usuário do início ao fim.
Você tem acesso ao histórico de tudo o que os outros agentes já disseram (transcript compartilhado).
Analise o que foi dito, critique se necessário, construa sobre as ideias anteriores e decida os próximos passos sob a sua especialidade.
Responda de forma clara, técnica e objetiva.
"""
        # Constrói o contexto com o transcript compartilhado
        messages = shared_transcript.copy()
        messages.append({
            "role": "user",
            "content": f"[Tarefa Inicial]: {task}\n\n[Instrução]: Analise a conversa acima até o momento sob a perspectiva do seu papel ({self.role}) e apresente suas conclusões, decisões ou código."
        })

        try:
            print(f"\n💬 [{self.name} - {self.role}] Analisando histórico e preparando resposta...")
            response = self.provider.generate(system=system_prompt, messages=messages)
            
            # Aplica o atraso configurável entre as respostas (padrão 50 segundos)
            if delay > 0:
                print(f"⏳ [{self.name}] Aguardando intervalo de {delay} segundos antes de liberar para o próximo agente...")
                time.sleep(delay)
                
            return response
        except Exception as e:
            return f"Erro no agente {self.name}: {str(e)}"

class MultiAgentOrchestrator:
    def __init__(self, providers: List[Dict[str, Any]], delay: int = 50):
        """
        providers: Lista de dicionários com {"name": "...", "role": "...", "provider": provider_instance}
        delay: Atraso em segundos entre cada agente (padrão 50s)
        """
        self.specialists = [
            AgentSpecialist(p["name"], p["role"], p["provider"])
            for p in providers
        ]
        self.delay = delay
        self.transcript: List[Dict[str, str]] = []

    def run_workflow(self, task: str) -> str:
        """Executa o pipeline colaborativo sequencial entre os agentes especialistas."""
        print(f"\n🚀 [KAWA-AI Multiagent] Iniciando pipeline colaborativo para a tarefa: '{task}'")
        print(f"👥 Equipe com {len(self.specialists)} especialistas. Atraso entre turnos: {self.delay}s.\n")

        self.transcript = []
        
        # Adiciona a tarefa inicial ao transcript
        self.transcript.append({"role": "user", "content": task})

        final_summary = ""

        for i, specialist in enumerate(self.specialists):
            print(f"\n--- Turno {i+1}/{len(self.specialists)}: {specialist.name} ({specialist.role}) ---")
            
            # Cada agente lê tudo o que foi dito anteriormente
            response = specialist.speak(task, self.transcript, delay=self.delay if i < len(self.specialists) - 1 else 0)
            
            print(f"\n✨ [{specialist.name}]:\n{response}\n")

            # Atualiza o transcript compartilhado
            self.transcript.append({"role": "assistant", "content": f"[{specialist.name} - {specialist.role}]: {response}"})
            final_summary = response

        return final_summary
