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
TASK:
Evaluate whether a scientific article should be included in a Systematic Literature Review (SLR) focused on:

Digital Twins + Explainable AI (XAI) + Human-centered approaches.

You must carefully assess the article based strictly on the inclusion and exclusion criteria provided below.

-----------------------------
INCLUSION CRITERIA:
{self.INCLUSION_CRITERIA}

EXCLUSION CRITERIA:
{self.EXCLUSION_CRITERIA}
-----------------------------

ARTICLE TO EVALUATE:
---
ID: {article.bibtex_id}
Title: {article.title}
Year: {article.year}
Authors: {article.authors if article.authors else "Not provided"}
Journal: {article.journal if article.journal else "Not provided"}
DOI: {article.doi if article.doi else "Not provided"}
URL: {article.url if article.url else "Not provided"}
Abstract: {article.abstract if article.abstract else "Not provided"}
---

{f"ADDITIONAL CONTEXT:\n{criteria_context}\n" if criteria_context else ""}

EVALUATION INSTRUCTIONS:

1. Focus primarily on the abstract when determining relevance.
2. If the abstract is missing or insufficient, rely on title and metadata.
3. Be conservative in ambiguous cases.
4. The article must explicitly address Digital Twins AND at least one of:
   - Explainability / Explainable AI / Transparency
   - Human-in-the-loop / Human-centered decision support
5. If the article only mentions generic AI, ML, IoT, or cyber-physical systems without clear linkage to Digital Twins, it should NOT be included.
6. If the connection to explainability or human-centered aspects is weak or unclear, classify as "pode ser".
7. Do NOT assume relevance unless it is clearly supported by the text.

-----------------------------

RESPONSE INSTRUCTIONS:

You MUST respond exclusively in valid JSON.
Do NOT include explanations outside the JSON.
Do NOT include markdown code blocks (no ```).
Return only raw JSON.

Provide:

1. "decision": One of exactly three options:
   - "entra" (clearly satisfies inclusion criteria)
   - "não entra" (clearly does not satisfy criteria)
   - "pode ser" (uncertain / requires manual review)

2. "justification": A concise but precise explanation (minimum 20 characters) explicitly referencing which criteria were met or not met.

-----------------------------

VALID JSON RESPONSE FORMAT (NO BACKTICKS):

{
  "decision": "entra|não entra|pode ser",
  "justification": "Clear reasoning based on criteria."
}
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
