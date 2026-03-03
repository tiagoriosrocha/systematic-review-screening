"""
Configuração centralizada do projeto.

Este módulo carrega e valida todas as variáveis de ambiente
e configurações necessárias para o funcionamento do sistema.
"""

import os
from datetime import datetime
from dotenv import load_dotenv
from typing import Optional

# Carrega variáveis de ambiente do arquivo .env
load_dotenv()


class Config:
    """Configurações da aplicação."""
    
    # ====== CONFIGURAÇÕES AZURE OPENAI ======
    LLM_API_KEY: str = os.getenv("LLM_API_KEY", "")
    LLM_ENDPOINT: str = os.getenv("LLM_ENDPOINT", "")
    LLM_API_VERSION: str = os.getenv("LLM_API_VERSION", "2024-02-15")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "gpt-4")
    
    # ====== CONFIGURAÇÕES DE PROCESSAMENTO ======
    TEMPERATURE: float = float(os.getenv("TEMPERATURE", "0.7"))
    MAX_RETRIES: int = int(os.getenv("MAX_RETRIES", "3"))
    RETRY_DELAY_SECONDS: int = int(os.getenv("RETRY_DELAY_SECONDS", "2"))
    TIMEOUT_SECONDS: int = int(os.getenv("TIMEOUT_SECONDS", "30"))
    
    # ====== VERSÃO DO PROMPT ======
    PROMPT_VERSION: str = os.getenv("PROMPT_VERSION", "1.0")
    
    # ====== CAMINHOS ======
    BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    INPUT_DIR: str = os.path.join(BASE_DIR, "input")
    OUTPUT_DIR: str = os.path.join(BASE_DIR, "output")
    LOGS_DIR: str = os.path.join(BASE_DIR, "logs")
    
    INPUT_BIB_FILE: str = os.path.join(INPUT_DIR, "articles.bib")
    
    # Generate timestamp for unique filenames
    _TIMESTAMP: str = datetime.now().strftime("%d-%m-%Y-%H-%M-%S")
    
    # CSV files for two-stage screening with timestamp
    OUTPUT_CSV_PHASE1: str = os.path.join(OUTPUT_DIR, f"artigos_fase1_screening_{_TIMESTAMP}.csv")
    OUTPUT_CSV_PHASE2: str = os.path.join(OUTPUT_DIR, f"artigos_fase2_screening_{_TIMESTAMP}.csv")
    
    # Legacy (deprecated)
    OUTPUT_CSV_FILE: str = os.path.join(OUTPUT_DIR, "artigos_avaliados_v2.csv")
    
    LOG_FILE: str = os.path.join(LOGS_DIR, "slr_reviewer.log")
    
    # ====== LOGGING ======
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    @classmethod
    def validate(cls) -> None:
        """
        Valida se todas as configurações obrigatórias foram definidas.
        
        Raises:
            ValueError: Se alguma configuração obrigatória está faltando.
        """
        if not cls.LLM_API_KEY:
            raise ValueError("LLM_API_KEY não foi configurada no arquivo .env")
        
        if not cls.LLM_ENDPOINT:
            raise ValueError("LLM_ENDPOINT não foi configurada no arquivo .env")
        
        if not cls.LLM_MODEL:
            raise ValueError("LLM_MODEL não foi configurada no arquivo .env")
        
        # Valida temperatura
        if not 0.0 <= cls.TEMPERATURE <= 2.0:
            raise ValueError(
                f"TEMPERATURE deve estar entre 0.0 e 2.0, recebido: {cls.TEMPERATURE}"
            )
        
        # Cria diretórios se não existirem
        os.makedirs(cls.INPUT_DIR, exist_ok=True)
        os.makedirs(cls.OUTPUT_DIR, exist_ok=True)
        os.makedirs(cls.LOGS_DIR, exist_ok=True)
    
    @classmethod
    def to_dict(cls) -> dict:
        """
        Retorna as configurações como dicionário.
        
        Returns:
            dict: Dicionário com as configurações (sem API key por segurança).
        """
        return {
            "LLM_ENDPOINT": cls.LLM_ENDPOINT,
            "LLM_API_VERSION": cls.LLM_API_VERSION,
            "LLM_MODEL": cls.LLM_MODEL,
            "TEMPERATURE": cls.TEMPERATURE,
            "MAX_RETRIES": cls.MAX_RETRIES,
            "RETRY_DELAY_SECONDS": cls.RETRY_DELAY_SECONDS,
            "TIMEOUT_SECONDS": cls.TIMEOUT_SECONDS,
            "PROMPT_VERSION": cls.PROMPT_VERSION,
            "INPUT_BIB_FILE": cls.INPUT_BIB_FILE,
            "OUTPUT_CSV_PHASE1": cls.OUTPUT_CSV_PHASE1,
            "OUTPUT_CSV_PHASE2": cls.OUTPUT_CSV_PHASE2,
            "LOG_FILE": cls.LOG_FILE,
        }
