"""
Construtor de prompts para o LLM.

Este módulo é responsável por construir prompts estruturados
e otimizados para a tarefa de triagem de artigos científicos.
"""

from abc import ABC, abstractmethod
from typing import Optional
from src.models import Article


class PromptBuilder(ABC):
    """
    Classe abstrata para construtor de prompts.
    
    Define a interface comum para diferentes implementações de construtores de prompts.
    """
    
    def get_system_message(self) -> str:
        """
        Retorna a mensagem do sistema para o LLM.
        
        Returns:
            str: Conteúdo do role "system".
        """
        return self.SYSTEM_PROMPT

    @abstractmethod
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
        pass
    
    def build_messages(
        self,
        article: Article,
        criteria_context: Optional[str] = None
    ) -> list[dict]:
        """
        Constrói a estrutura completa de mensagens com roles "system" e "user".
        
        Args:
            article: Artigo a ser avaliado.
            criteria_context: Contexto adicional sobre critérios (opcional).
        
        Returns:
            list[dict]: Lista com dicionários contendo "role" e "content".
        """
        return [
            {
                "role": "system",
                "content": self.get_system_message()
            },
            {
                "role": "user",
                "content": self.build_evaluation_prompt(article, criteria_context)
            }
        ]







class PromptBuilderPhase1(PromptBuilder):
    """
    Phase 1 - Broad Screening (High Recall)

    Goal: Maximize sensitivity and avoid excluding potentially relevant studies.
    """

    SYSTEM_PROMPT = """
    You are a senior researcher specialized in systematic literature reviews.

    You are performing the FIRST screening phase of a two-stage selection process.
    This phase prioritizes sensitivity (recall) over specificity.

    Your objective is to avoid prematurely excluding potentially relevant studies.
    When evidence is partial or unclear, prefer selecting "maybe" instead of "exclude".

    You must strictly follow the provided inclusion and exclusion criteria.
    Respond only with valid JSON.
    """

    INCLUSION_CRITERIA = """
    INCLUSION CRITERIA:

    IC1. The article discusses Digital Twins as a relevant or central concept 
         of the system, architecture, framework, or conceptual proposal.

    IC2. The article mentions, explores, or relates to explainability, interpretability,
         transparency, XAI, or human interaction aspects in the context of Digital Twins.

    NOTE:
    For Phase 1, it is sufficient that:
        - Digital Twin is relevant AND
        - At least one of the following appears:
            (a) explainability-related aspects OR
            (b) human-centered or interaction aspects
    """

    EXCLUSION_CRITERIA = """
    EXCLUSION CRITERIA:

    EC1. The article is clearly unrelated to Digital Twins.

    EC2. The article focuses exclusively on predictive or simulation models
         within Digital Twins without any reference to explainability,
         transparency, or human-related aspects.

    EC3. Short abstracts, posters, tutorials, non-peer-reviewed material,
         or secondary studies (e.g., systematic reviews or surveys).

    EC4. Publications without an English title or English abstract.
    """


    def build_evaluation_prompt(
        self,
        article: Article,
        criteria_context: Optional[str] = None
    ) -> str:

        prompt = f"""
        TASK:
        Perform Phase 1 screening of a scientific article.

        This is a BROAD screening phase.
        If relevance is plausible but not fully explicit, select "maybe".

        {self.INCLUSION_CRITERIA}

        {self.EXCLUSION_CRITERIA}

        ARTICLE:
        ---
        ID: {article.bibtex_id}
        Title: {article.title}
        Year: {article.year}
        Authors: {article.authors if article.authors else "Not provided"}
        Journal: {article.journal if article.journal else "Not provided"}
        DOI: {article.doi if article.doi else "Not provided"}
        Abstract: {article.abstract if article.abstract else "Not provided"}
        ---

        {f"ADDITIONAL CONTEXT:\n{criteria_context}\n" if criteria_context else ""}

        DECISION RULES:

        - "include" → Clearly satisfies Phase 1 inclusion logic.
        - "maybe"   → Partially satisfies criteria or insufficient clarity.
        - "exclude" → Clearly violates inclusion criteria.

        RESPONSE FORMAT (VALID JSON ONLY):
        {{
          "decision": "include|exclude|maybe",
          "justification": "Concise explanation grounded in the criteria"
        }}
        """

        return prompt.strip()






class PromptBuilderPhase2(PromptBuilder):
    """
    Phase 2 - Strict Screening (High Precision)

    Goal: Maximize specificity and ensure conceptual alignment.
    """

    SYSTEM_PROMPT = """
    You are a senior researcher specialized in systematic literature reviews.

    You are performing the SECOND screening phase of a two-stage selection process.
    This phase prioritizes specificity and conceptual precision.

    Only include articles that clearly and explicitly satisfy ALL required criteria.
    Do not infer missing elements.
    If key elements are not explicitly described, do not assume they exist.

    Respond only with valid JSON.
    """

    INCLUSION_CRITERIA = """
    INCLUSION CRITERIA (ALL must be satisfied):

    IC1. Digital Twin is a central concept of the proposed architecture, system, or framework.

    IC2. The article explicitly proposes, implements, evaluates, or formally discusses
         explainability, interpretability, transparency, or XAI mechanisms
         within the Digital Twin context.

    IC3. The article explicitly defines human roles (e.g., operator, decision-maker)
         OR incorporates human-in-the-loop, human-on-the-loop,
         or human-centered interaction mechanisms.

    NOTE:
    All criteria must be explicitly supported by the abstract or metadata.
    """

    EXCLUSION_CRITERIA = """
    EXCLUSION CRITERIA:

    EC1. The article is clearly unrelated to Digital Twins.

    EC2. The article focuses exclusively on predictive or simulation models
         within Digital Twins without any reference to explainability,
         transparency, or human-related aspects.

    EC3. Short abstracts, posters, tutorials, non-peer-reviewed material,
         or secondary studies (e.g., systematic reviews or surveys).

    EC4. Publications without an English title or English abstract.
    """

    def build_evaluation_prompt(
        self,
        article: Article,
        criteria_context: Optional[str] = None
    ) -> str:

        prompt = f"""
        TASK:
        Perform Phase 2 strict screening of a scientific article.

        This phase requires explicit evidence of ALL inclusion criteria.
        Do not rely on implicit assumptions.

        PHASE 1 ASSESSMENT (for reference only):
        {f"Previous justification: {criteria_context}" if criteria_context else "Not available"}

        {self.INCLUSION_CRITERIA}

        {self.EXCLUSION_CRITERIA}

        ARTICLE:
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

        DECISION RULES:

        - "include" → ALL inclusion criteria explicitly satisfied.
        - "maybe"   → Minor ambiguity but strong alignment.
        - "exclude" → Any required criterion missing.

        RESPONSE FORMAT (VALID JSON ONLY):
        {{
          "decision": "include|exclude|maybe",
          "justification": "Precise explanation referencing unmet or satisfied criteria"
        }}
        """

        return prompt.strip()
