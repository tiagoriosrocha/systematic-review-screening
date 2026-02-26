"""
Avaliador de artigos científicos.

Este módulo coordena a avaliação de artigos, chamando o LLM
e validando as respostas com Pydantic.
"""

import logging
import time
from datetime import datetime
from typing import Optional

from src.models import Article, ArticleEvaluation, EvaluationResult
from src.llm_client import LLMClient
from src.prompt_builder import PromptBuilder
from src.config import Config


logger = logging.getLogger(__name__)


class ArticleEvaluator:
    """
    Avaliador de artigos científicos usando LLM.
    """
    
    def __init__(
        self, 
        prompt_builder: Optional[PromptBuilder] = None,
        llm_client: Optional[LLMClient] = None
    ):
        """
        Inicializa o avaliador.
        
        Args:
            prompt_builder: PromptBuilder customizado (opcional).
            llm_client: LLMClient customizado (opcional).
        """
        self.prompt_builder = prompt_builder or PromptBuilder.create_v1_0()
        self.llm_client = llm_client or LLMClient()
    
    def evaluate(
        self, 
        article: Article,
        additional_context: Optional[str] = None
    ) -> EvaluationResult:
        """
        Avalia um artigo científico.
        
        Args:
            article: Artigo a avaliar.
            additional_context: Contexto adicional para o prompt (opcional).
        
        Returns:
            EvaluationResult: Resultado completo da avaliação.
        
        Raises:
            ValueError: Se a resposta do LLM for inválida.
        """
        start_time = time.time()
        
        logger.info(f"Starting evaluation of article: {article.bibtex_id}")
        logger.debug(f"Article title: {article.title}")
        
        # Construir prompt
        prompt = self.prompt_builder.build_evaluation_prompt(
            article=article,
            criteria_context=additional_context
        )
        
        logger.debug(f"Prompt built (length: {len(prompt)})")
        
        try:
            # Chamar LLM
            response_dict = self.llm_client.call_llm_for_json(prompt)
            
            logger.debug(f"LLM response: {response_dict}")
            
            # Validar resposta com Pydantic
            evaluation = ArticleEvaluation(**response_dict)
            
            logger.info(
                f"Article {article.bibtex_id} evaluated as '{evaluation.decision}'"
            )
            
            # Calcular tempo de processamento
            processing_time = time.time() - start_time
            
            # Criar resultado completo
            result = EvaluationResult(
                bibtex_id=article.bibtex_id,
                title=article.title,
                evaluation=evaluation,
                model_name=Config.LLM_MODEL,
                prompt_version=self.prompt_builder.get_version(),
                execution_date=datetime.now(),
                processing_time_seconds=processing_time
            )
            
            logger.debug(f"Evaluation result created: processing_time={processing_time:.2f}s")
            
            return result
        
        except ValueError as e:
            logger.error(
                f"Validation error for article {article.bibtex_id}: {str(e)}"
            )
            raise
        
        except Exception as e:
            logger.error(
                f"Unexpected error evaluating article {article.bibtex_id}: {str(e)}"
            )
            raise
    
    def get_model_info(self) -> dict:
        """
        Retorna informações sobre o modelo e configuração atual.
        
        Returns:
            dict: Dicionário com informações do modelo.
        """
        return {
            "model_name": Config.LLM_MODEL,
            "prompt_version": self.prompt_builder.get_version(),
            "temperature": Config.TEMPERATURE,
            "max_retries": Config.MAX_RETRIES,
        }
