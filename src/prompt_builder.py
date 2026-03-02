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






class PromptBuilderEnglish(PromptBuilder):
    """
    English version of the prompt builder for article evaluation.
    
    This class provides English prompts with inclusion and exclusion criteria
    for systematic literature review on Digital Twins.
    """
    
    # Inclusion criteria in English
    INCLUSION_CRITERIA = """
    INCLUSION CRITERIA:
    
    IC1. Articles where Digital Twin is a central concept of the proposed architecture, system, or framework.
    
    IC2. Articles that propose, implement, evaluate, or formally discuss explainability, 
         interpretability, transparency, or XAI (eXplainable AI) techniques in the context of Digital Twins.
    
    IC3. Articles that explicitly define human roles (e.g., operator, decision-maker) or 
         incorporate human-in-the-loop, human-on-the-loop, or human-centered interaction mechanisms 
         within the Digital Twin system.
    
    IC4. Articles that describe or evaluate the explanation process, architecture, or interaction 
         design within a Digital Twin system.
    """
    
    # Exclusion criteria in English
    EXCLUSION_CRITERIA = """
    EXCLUSION CRITERIA:
    
    EC1. Articles not related to Digital Twins.
    
    EC2. Articles that apply predictive models within Digital Twins without proposing, evaluating, 
         or discussing explainability or interpretability mechanisms.
    
    EC3. Short abstracts, posters, tutorials, non-peer-reviewed material, secondary studies, 
         or systematic reviews.
    
    EC4. Publications in languages other than English (articles in Portuguese or Spanish must have 
         an English version or abstract).
    """
    
    def __init__(self, version: str = "2.0"):
        """
        Initialize the English prompt builder.
        
        Args:
            version: Prompt version (for scientific traceability).
        """
        super().__init__(version=version)
    
    def build_evaluation_prompt(
        self, 
        article: Article,
        criteria_context: Optional[str] = None
    ) -> str:
        """
        Build a prompt for evaluating a scientific article.
        
        Args:
            article: Article to be evaluated.
            criteria_context: Additional context about criteria (optional).
        
        Returns:
            str: Structured prompt for the LLM.
        """
        prompt = f"""
        Evaluate whether a scientific article should be included in a Systematic Literature Review (SLR) focused on:
        Digital Twins + Explainable AI (XAI) + Human-centered approaches.


        {self.INCLUSION_CRITERIA}

        {self.EXCLUSION_CRITERIA}

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

        {f"ADDITIONAL CONTEXT:\\n{criteria_context}\\n" if criteria_context else ""}

        RESPONSE INSTRUCTION:
        You MUST respond EXCLUSIVELY in valid JSON format, with no additional text.
        Do not include code markers (```), only the raw JSON.

        Analyze the article based on the criteria above and provide:
        1. "decision": One of three options: "include", "exclude", or "maybe"
        - "include": The article clearly meets the inclusion criteria
        - "exclude": The article clearly does not meet the criteria
        - "maybe": There is doubt and the article requires additional review

        2. "justification": A clear and concise justification (minimum 20 characters)
        explaining the decision based on the criteria

        RESPONSE (VALID JSON WITHOUT BACKTICKS):
        {{
        "decision": "include|exclude|maybe",
        "justification": "your justification here"
        }}
        """

        return prompt.strip()
    
    @staticmethod
    def create_v2_0() -> "PromptBuilderEnglish":
        """Factory method to create an English PromptBuilder version 2.0."""
        return PromptBuilderEnglish(version="2.0")
