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
    You are a senior researcher conducting PHASE 1 of a three-stage systematic literature review screening.

    PHASE 1 OBJECTIVE: BROAD SCREENING
    - Maximize SENSITIVITY (recall) - catch as many relevant articles as possible
    - Minimize false negatives - avoid prematurely excluding potentially relevant studies
    - When evidence is partial or unclear, PREFER "maybe" over "exclude"
    - This is a HIGH RECALL phase designed to cast a wide net

    Your role: Initial triage to identify potentially relevant studies.
    Your constraint: Follow the inclusion and exclusion criteria strictly.
    Your output: Valid JSON with decision (include|exclude|maybe) and justification.
    """

    INCLUSION_CRITERIA = """
    PHASE 1 INCLUSION CRITERIA (Broad):

    IC1. The article discusses Digital Twins as a relevant or central concept 
         of the system, architecture, framework, or conceptual proposal.

    IC2. The article mentions, explores, or relates to explainability, interpretability,
         transparency, XAI, or human interaction aspects in the context of Digital Twins.

    RULE FOR PHASE 1:
    It is SUFFICIENT that:
        - Digital Twin is relevant AND
        - At least one of the following appears:
            (a) explainability-related aspects OR
            (b) human-centered or interaction aspects
    
    DO NOT EXCLUDE if there is ANY potential relevance.
    """

    EXCLUSION_CRITERIA = """
    PHASE 1 EXCLUSION CRITERIA (Clear cases only):

    EC1. The article is clearly and obviously unrelated to Digital Twins.

    EC2. The article focuses exclusively on predictive or simulation models
         within Digital Twins WITHOUT ANY reference to explainability,
         transparency, or human-related aspects.

    EC3. Short abstracts, posters, tutorials, non-peer-reviewed material,
         or secondary studies (e.g., systematic reviews or surveys).

    EC4. Publications without an English title or English abstract.
    
    IMPORTANT: Only exclude if the article clearly violates these criteria.
    """

    def build_evaluation_prompt(
        self,
        article: Article,
        criteria_context: Optional[str] = None
    ) -> str:

        prompt = f"""
        ============================================================
        PHASE 1: BROAD SCREENING (HIGH RECALL)
        ============================================================
        
        TASK:
        You are screening a scientific article in PHASE 1 of a three-stage SLR process.
        
        This is a BROAD SCREENING phase with HIGH RECALL emphasis.
        Your goal is to identify ALL potentially relevant articles.
        When in doubt, prefer "maybe" instead of excluding.
        
        You will see stricter criteria in later phases (Phase 2, Phase 3).
        For now, cast a wide net.

        {self.INCLUSION_CRITERIA}

        {self.EXCLUSION_CRITERIA}

        ============================================================
        ARTICLE TO EVALUATE:
        ============================================================
        
        ID: {article.bibtex_id}
        Title: {article.title}
        Year: {article.year}
        Authors: {article.authors if article.authors else "Not provided"}
        Journal: {article.journal if article.journal else "Not provided"}
        DOI: {article.doi if article.doi else "Not provided"}
        Abstract: {article.abstract if article.abstract else "Not provided"}

        {f"ADDITIONAL CONTEXT:\n{criteria_context}\n" if criteria_context else ""}

        ============================================================
        DECISION RULES FOR PHASE 1:
        ============================================================

        - "include" → Clearly satisfies Phase 1 inclusion criteria. Article is relevant.
        - "maybe"   → Partially satisfies criteria OR evidence is unclear. Article has potential.
        - "exclude" → Clearly violates Phase 1 criteria. Article is not relevant.

        ============================================================
        RESPONSE FORMAT (VALID JSON ONLY):
        ============================================================
        {{
          "decision": "include|exclude|maybe",
          "justification": "Concise explanation grounded in the criteria above"
        }}
        """

        return prompt.strip()






class PromptBuilderPhase2(PromptBuilder):
    """
    Phase 2 - Strict Screening (High Precision)

    Goal: Maximize specificity and ensure conceptual alignment.
    """

    SYSTEM_PROMPT = """
    You are a senior researcher conducting PHASE 2 of a three-stage systematic literature review screening.

    PHASE 2 OBJECTIVE: STRICT SCREENING
    - Maximize SPECIFICITY (precision) - only keep articles that clearly meet all criteria
    - Minimize false positives - rigorously evaluate against stricter criteria
    - Do NOT infer or assume missing elements
    - Only include if evidence is EXPLICIT in the abstract/metadata
    - This is a HIGH PRECISION phase designed to refine the selection

    Your role: Rigorous evaluation of articles that passed Phase 1.
    Your constraint: All criteria must be explicitly satisfied - no assumptions.
    Your output: Valid JSON with decision (include|exclude|maybe) and justification.
    
    NOTE: Articles marked as "maybe" here will proceed to Phase 3 for final adjudication.
    """

    INCLUSION_CRITERIA = """
    PHASE 2 INCLUSION CRITERIA (Strict - ALL must be satisfied):

    IC1. Digital Twin is a CENTRAL CONCEPT of the proposed architecture, system, or framework.
         (Not just mentioned in passing)

    IC2. The article EXPLICITLY proposes, implements, evaluates, or formally discusses
         explainability, interpretability, transparency, or XAI mechanisms
         within the Digital Twin context.
         (Not just implied or tangentially related)

    IC3. The article EXPLICITLY defines human roles (e.g., operator, decision-maker)
         OR explicitly incorporates human-in-the-loop, human-on-the-loop,
         or human-centered interaction mechanisms as part of the system.
         (Not just mentioned in acknowledgments or future work)

    CRITICAL RULE FOR PHASE 2:
    All criteria MUST BE EXPLICITLY SUPPORTED by the abstract or metadata.
    If any criterion is missing or only implied, the article should be marked "maybe" or "exclude".
    """

    EXCLUSION_CRITERIA = """
    PHASE 2 EXCLUSION CRITERIA (Clear violations):

    EC1. The article is clearly unrelated to Digital Twins.

    EC2. The article focuses exclusively on predictive or simulation models
         within Digital Twins WITHOUT ANY reference to explainability,
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
        ============================================================
        PHASE 2: STRICT SCREENING (HIGH PRECISION)
        ============================================================
        
        TASK:
        You are screening a scientific article in PHASE 2 of a three-stage SLR process.
        
        This is a STRICT SCREENING phase with HIGH PRECISION emphasis.
        Your goal is to rigorously evaluate articles against stricter criteria.
        
        PHASE 1 ASSESSMENT (for reference only - re-evaluate independently):
        {f"Previous Phase 1 justification: {criteria_context}" if criteria_context else "Not available"}
        
        Do NOT be influenced by Phase 1 assessment.
        Re-evaluate based strictly on Phase 2 criteria.

        {self.INCLUSION_CRITERIA}

        {self.EXCLUSION_CRITERIA}

        ============================================================
        ARTICLE TO EVALUATE:
        ============================================================
        
        ID: {article.bibtex_id}
        Title: {article.title}
        Year: {article.year}
        Authors: {article.authors if article.authors else "Not provided"}
        Journal: {article.journal if article.journal else "Not provided"}
        DOI: {article.doi if article.doi else "Not provided"}
        URL: {article.url if article.url else "Not provided"}
        Abstract: {article.abstract if article.abstract else "Not provided"}

        {f"ADDITIONAL CONTEXT:\n{criteria_context}\n" if criteria_context else ""}

        ============================================================
        DECISION RULES FOR PHASE 2:
        ============================================================

        - "include" → ALL inclusion criteria are EXPLICITLY satisfied in the abstract/metadata.
        - "maybe"   → Minor ambiguity exists but there is strong alignment with criteria.
                       Article will be sent to Phase 3 for final adjudication.
        - "exclude" → Any required criterion is missing or not explicitly stated.

        ============================================================
        RESPONSE FORMAT (VALID JSON ONLY):
        ============================================================
        {{
          "decision": "include|exclude|maybe",
          "justification": "Precise explanation referencing which criteria are satisfied or missing"
        }}
        """

        return prompt.strip()



class PromptBuilderPhase3(PromptBuilder):
    """
    Phase 3 - Adjudication Phase (Forced Binary Decision)

    Goal:
    Resolve ambiguity from Phase 2 and produce a final binary decision.
    No "maybe" option allowed - must choose include or exclude.
    """

    SYSTEM_PROMPT = """
    You are a senior researcher conducting PHASE 3 of a three-stage systematic literature review screening.

    PHASE 3 OBJECTIVE: ADJUDICATION (FINAL DECISION)
    - Resolve ambiguity from Phase 2 screening
    - Make a DEFINITIVE BINARY decision (include or exclude)
    - NO "maybe" option - a decision must be made
    - Apply rigorous inclusion criteria
    - Explicitly identify which criteria are satisfied or not
    - Avoid ambiguity in the final decision

    Your role: Final arbiter to resolve Phase 2 "maybe" cases.
    Your constraint: Must output either "include" or "exclude", not "maybe".
    Your output: Valid JSON with binary decision (include|exclude) and detailed justification.
    
    NOTE: This is the final filtering stage. Only articles that clearly and explicitly
    meet ALL criteria should be included.
    """

    INCLUSION_CRITERIA = """
    PHASE 3 FINAL INCLUSION CRITERIA (ALL must be explicitly supported):

    IC1. Digital Twin is a CENTRAL AND DEFINING CONCEPT of the proposed system.
         (Not peripheral or incidental)

    IC2. The article EXPLICITLY proposes, implements, evaluates, or formally analyzes
         explainability, interpretability, transparency, or XAI mechanisms
         WITHIN THE DIGITAL TWIN CONTEXT.
         (Clear, unambiguous discussion - not vague or implied)

    IC3. The article EXPLICITLY defines human roles (e.g., operator, decision-maker, analyst)
         OR explicitly incorporates human-in-the-loop, human-on-the-loop, or human-centered interaction
         as part of the system architecture or evaluation.
         (Concrete evidence - not mentioned in passing)

    CRITICAL RULE FOR PHASE 3:
    All criteria must be clearly and explicitly supported by the abstract or metadata.
    If ANY criterion is missing, ambiguous, or only weakly supported, the article MUST be excluded.
    """

    EXCLUSION_GUIDANCE = """
    PHASE 3 EXCLUSION GUIDANCE:

    If ANY of the following are true, EXCLUDE the article:
    
    1. Digital Twin is not clearly central to the work
    2. Explainability/XAI aspects are vague, implied, or absent
    3. Human roles or interaction mechanisms are not explicitly described
    4. Evidence is insufficient, weak, or only in acknowledgments/future work
    5. The article is a secondary study, tutorial, or non-peer-reviewed work
    
    Do NOT assume implicit evidence.
    Do NOT extrapolate beyond what is stated in the abstract.
    When in doubt, EXCLUDE.
    """

    def build_evaluation_prompt(
        self,
        article: Article,
        criteria_context: Optional[str] = None
    ) -> str:

        prompt = f"""
        ============================================================
        PHASE 3: ADJUDICATION (FINAL BINARY DECISION)
        ============================================================
        
        TASK:
        You are making a FINAL DECISION for a scientific article in PHASE 3.
        
        This article was previously marked as "maybe" in Phase 2.
        You must now issue a DEFINITIVE BINARY DECISION.
        
        NO "maybe" option is allowed.
        You MUST choose either "include" or "exclude".

        PHASE 2 ASSESSMENT (for context only - re-evaluate independently):
        {f"Previous Phase 2 justification: {criteria_context}" if criteria_context else "Not available"}
        
        Do NOT be bound by Phase 2 assessment.
        Re-evaluate independently based on Phase 3 criteria.

        {self.INCLUSION_CRITERIA}

        {self.EXCLUSION_GUIDANCE}

        ============================================================
        ARTICLE TO EVALUATE:
        ============================================================
        
        ID: {article.bibtex_id}
        Title: {article.title}
        Year: {article.year}
        Authors: {article.authors if article.authors else "Not provided"}
        Journal: {article.journal if article.journal else "Not provided"}
        DOI: {article.doi if article.doi else "Not provided"}
        Abstract: {article.abstract if article.abstract else "Not provided"}

        ============================================================
        DECISION RULES FOR PHASE 3:
        ============================================================

        - "include" → ALL inclusion criteria are EXPLICITLY and CLEARLY satisfied.
                      Strong evidence of all required elements.
                      
        - "exclude" → ANY required criterion is missing, ambiguous, or weakly supported.
                      When in doubt, exclude.

        NO OTHER OPTIONS ARE ALLOWED.

        ============================================================
        RESPONSE FORMAT (VALID JSON ONLY):
        ============================================================
        {{
          "decision": "include|exclude",
          "justification": "Explicitly reference which criteria are satisfied or missing. Explain the final decision."
        }}
        """

        return prompt.strip()