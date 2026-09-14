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

    SYSTEM_PROMPT: str
    
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
    You are a senior computer science researcher conducting PHASE 1 of a three-stage systematic literature review screening.
 
    DOMAIN: Graph Databases & Data Engineering (RDF and Property Graphs).
 
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
 
    IC1. The article addresses data conversion, schema mapping, interoperability, or query translation involving Graph Data Models.
 
    IC2. The article mentions, explores, or relates to Resource Description Framework (RDF) OR Property Graphs (PG) / Labeled Property Graphs (LPG) / Property Graph databases (e.g., Neo4j, Memgraph, GraphDB, AnzoGraph).
 
    RULE FOR PHASE 1:
    It is SUFFICIENT that:
        - Graph data conversion or schema mapping is mentioned AND
        - At least one model (RDF or PG) appears in the title or abstract
    DO NOT EXCLUDE if there is ANY potential relevance to converting between RDF and PG.
    """
 
    EXCLUSION_CRITERIA = """
    PHASE 1 EXCLUSION CRITERIA (Clear cases only):
 
    EC1. Out of Scope: The article is clearly and obviously unrelated to Graph Databases, RDF, or Property Graphs (e.g., purely relational database indexing, image processing, hardware design).
 
    EC2. Short Papers & Non-Peer-Reviewed: Extended abstracts, posters, keynotes, slides, tutorial summaries, editorials, or grey literature (theses, dissertations, technical reports, preprints without peer review).
 
    EC3. Publications without an English title or English abstract.
 
    EC4. Exact or obvious duplicate entries.
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
        Your goal is to identify ALL potentially relevant articles on RDF/PG conversion.
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
        Abstract: {article.abstract if article.abstract else "Not provided"}
        Journal: {article.journal if article.journal else "Not provided"}
 
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
    You are a senior computer science researcher conducting PHASE 2 of a three-stage systematic literature review screening.
 
    DOMAIN: Mapping, Interoperability, and Conversion between RDF and Property Graphs (PG).
 
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
 
    IC1. The article EXPLICITLY proposes, formalizes, implements, evaluates, or uses a method, algorithm, tool, schema mapping, or query transformation specifically BETWEEN RDF and Property Graphs (PG/LPG), in ANY direction (RDF -> PG, PG -> RDF, or Bidirectional).
 
    IC2. The work is a primary research paper (peer-reviewed journal or full conference/workshop paper).
 
    CRITICAL RULE FOR PHASE 2:
    The mapping MUST be DIRECTLY between RDF and PG.
    If the mapping is between Relational -> RDF (without PG) or Relational -> PG (without RDF), or if RDF/PG are mentioned only as passing background examples, the article should be marked "maybe" or "exclude".
    """
 
    EXCLUSION_CRITERIA = """
    PHASE 2 EXCLUSION CRITERIA (Clear violations):
 
    EC1. Out of Scope / Context Only: Articles where RDF or PG is mentioned merely as context, background, or motivation, without presenting or evaluating a mapping/conversion method between them.
 
    EC2. Other Models: Articles focusing exclusively on conversions involving other models (e.g., Relational to RDF, Property Graph to Relational, Property Graph to Document Store) without a direct translation layer between RDF and PG.
 
    EC3. Short Papers & Non-Peer-Reviewed: Short papers (< 4 pages), posters, workshop summaries, tutorials, survey papers/SLRs (secondary studies), theses, dissertations, preprints, or technical reports.
 
    EC4. Publications without an English title or English abstract, or duplicated studies.
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
        Abstract: {article.abstract if article.abstract else "Not provided"}
        Journal: {article.journal if article.journal else "Not provided"}
 
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
    You are a senior computer science researcher conducting PHASE 3 of a three-stage systematic literature review screening.
 
    DOMAIN: Mapping, Interoperability, and Conversion between RDF and Property Graphs (PG).
 
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
 
    IC1. The study EXPLICITLY presents, evaluates, or uses a concrete method, algorithm, tool, schema transformation, or query translation BETWEEN RDF AND PROPERTY GRAPHS (in any direction: RDF -> PG, PG -> RDF, or Bidirectional).
 
    IC2. The study is a primary research paper published in a peer-reviewed venue (full conference or journal paper).
 
    CRITICAL RULE FOR PHASE 3:
    All criteria must be clearly and explicitly supported by the abstract or metadata.
    If ANY criterion is missing, ambiguous, or only weakly supported, the article MUST be excluded.
    """
 
    EXCLUSION_GUIDANCE = """
    PHASE 3 EXCLUSION GUIDANCE:
 
    If ANY of the following are true, EXCLUDE the article:
    1. The mapping is between Relational DB and RDF/PG without a direct RDF <-> PG translation.
    2. RDF and PG are mentioned only as general background or future work.
    3. Evidence of RDF <-> PG conversion is insufficient, speculative, or weak.
    4. The article is a secondary study (survey/review), short paper (< 4 pages), thesis, dissertation, or technical report.
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
        Abstract: {article.abstract if article.abstract else "Not provided"}
        Journal: {article.journal if article.journal else "Not provided"}
 
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