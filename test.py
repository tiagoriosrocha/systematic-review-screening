#!/usr/bin/env python3
"""
Script de teste de execução da aplicação SLR LLM Reviewer.

Este script é utilizado para validar a configuração do ambiente e testar o fluxo básico de avaliação de um artigo.
"""

from src.csv_handler import BibTexHandler, CSVHandler
from src.evaluator import ArticleEvaluator
from src.prompt_builder import PromptBuilder
from src.config import Config

import logging
import sys
import os

# Adicionar o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configurar logging
def setup_logging():
    """Configura o sistema de logging."""
    
    # Create logger
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, Config.LOG_LEVEL))
    
    # File handler
    file_handler = logging.FileHandler(Config.LOG_FILE)
    file_handler.setLevel(getattr(logging, Config.LOG_LEVEL))
    file_handler.setFormatter(logging.Formatter(Config.LOG_FORMAT))
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter(Config.LOG_FORMAT))
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger


# Validar configurações
Config.validate()

# Configurar logging
logger = setup_logging()

# Ler artigos (somente 1 artigo específico para teste)
articles = BibTexHandler.read_articles("input/articles_test.bib")

# Criar avaliador
evaluator = ArticleEvaluator()

# Avaliar artigo
result = evaluator.evaluate(articles[0])

# Exibir resultado
print(result.evaluation.decision)

# Justificativa detalhada
print(result.evaluation.justification)

# Salvar resultado
CSVHandler.write_result("output/artigos_avaliados_test.csv", result)

print("Teste concluído com sucesso!")