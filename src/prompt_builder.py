"""
Construtor de prompts para o LLM.

Este módulo é responsável por construir prompts estruturados
e otimizados para a tarefa de triagem de artigos científicos.
"""

from typing import Optional
from src.models import Article


class PromptBuilder:
    """
    Construtor de prompts para avaliação de artigos.
    
    Permite criar prompts estruturados e versionar diferentes estratégias de avaliação.
    """
    
    # Definição dos critérios de inclusão
    INCLUSION_CRITERIA = """
    CRITÉRIOS DE INCLUSÃO:
    
    IC1. Artigos onde Digital Twin é um conceito central da arquitetura, sistema ou framework proposto.
    
    IC2. Artigos que propõem, implementam, avaliam ou discutem formalmente técnicas de explicabilidade,
         interpretabilidade, transparência ou XAI (eXplainable AI) no contexto de Digital Twins.
    
    IC3. Artigos que explicitamente definem papéis humanos (ex: operador, tomador de decisão) ou
         incorporam mecanismos de human-in-the-loop, human-on-the-loop ou interação centrada no
         humano dentro do sistema de Digital Twin.
    
    IC4. Artigos que descrevem ou avaliam o processo de explicação, arquitetura ou design de
         interação dentro de um sistema de Digital Twin.
    """
    
    EXCLUSION_CRITERIA = """
    CRITÉRIOS DE EXCLUSÃO:
    
    EC1. Artigos não relacionados a Digital Twins.
    
    EC2. Artigos que aplicam modelos preditivos dentro de Digital Twins sem propor, avaliar ou
         discutir mecanismos de explicabilidade ou interpretabilidade.
    
    EC3. Resumos curtos, posters, tutoriais, material não revisado por pares, estudos secundários
         ou revisões sistemáticas.
    
    EC4. Publicações em idiomas que não inglês (artigos em português ou espanhol devem ter
         versão ou resumo em inglês).
    """
    
    def __init__(self, version: str = "1.0"):
        """
        Inicializa o construtor de prompts.
        
        Args:
            version: Versão do prompt (para rastreabilidade científica).
        """
        self.version = version
    
    def build_evaluation_prompt(
        self, 
        article: Article,
        criteria_context: Optional[str] = None
    ) -> str:
        """
        Constrói um prompt para avaliação de um artigo.
        
        Args:
            article: Artigo a ser avaliado.
            criteria_context: Contexto adicional sobre critérios (opcional).
        
        Returns:
            str: Prompt estruturado para o LLM.
        """
        prompt = f"""
TAREFA: Avaliar se um artigo científico deve ser incluído em uma revisão sistemática sobre Digital Twins.

{self.INCLUSION_CRITERIA}

{self.EXCLUSION_CRITERIA}

ARTIGO A AVALIAR:
---
ID: {article.bibtex_id}
Título: {article.title}
Ano: {article.year}
Autores: {article.authors if article.authors else "Não fornecidos"}
Periódico: {article.journal if article.journal else "Não fornecido"}
DOI: {article.doi if article.doi else "Não fornecido"}
URL: {article.url if article.url else "Não fornecida"}
Resumo: {article.abstract if article.abstract else "Não fornecido"}
---

{f"CONTEXTO ADICIONAL:\\n{criteria_context}\\n" if criteria_context else ""}

INSTRUÇÃO DE RESPOSTA:
Você DEVE responder EXCLUSIVAMENTE em JSON válido, sem texto adicional.
Não inclua marcadores de código (```), apenas o JSON puro.

Analise o artigo baseado nos critérios acima e forneça:
1. "decision": Uma das três opções: "entra", "não entra" ou "pode ser"
   - "entra": O artigo claramente atende aos critérios de inclusão
   - "não entra": O artigo claramente não atende aos critérios
   - "pode ser": Há dúvida e o artigo needs revisão adicional

2. "justification": Uma justificativa clara e concisa (mínimo 20 caracteres)
   explicando o motivo da decisão baseado nos critérios

RESPOSTA (JSON VÁLIDO SEM BACKTICKS):
{{
  "decision": "entra|não entra|pode ser",
  "justification": "sua justificativa aqui"
}}
"""
        return prompt.strip()
    
    def get_version(self) -> str:
        """
        Retorna a versão atual do prompt.
        
        Returns:
            str: Versão do prompt.
        """
        return self.version
    
    @staticmethod
    def create_v1_0() -> "PromptBuilder":
        """Factory method para criar um PromptBuilder versão 1.0."""
        return PromptBuilder(version="1.0")
