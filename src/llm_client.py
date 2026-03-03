"""
Cliente para comunicação com Azure OpenAI.

Este módulo fornece funcionalidade de low-level para chamar o LLM
com tratamento de erros, retry automático e logging.
"""

import time
import json
import logging
from typing import Dict, Any, Optional
from openai import AzureOpenAI, APIError, APITimeoutError, RateLimitError

from src.config import Config


logger = logging.getLogger(__name__)


class LLMClient:
    """
    Cliente para Azure OpenAI com retry automático e tratamento de erros.
    """
    
    def __init__(self):
        """Inicializa o cliente Azure OpenAI."""
        self.client = AzureOpenAI(
            api_key=Config.LLM_API_KEY,
            api_version=Config.LLM_API_VERSION,
            base_url=Config.LLM_ENDPOINT,
        )
        self.model = Config.LLM_MODEL
        self.temperature = Config.TEMPERATURE
        self.max_retries = Config.MAX_RETRIES
        self.retry_delay = Config.RETRY_DELAY_SECONDS
        self.timeout = Config.TIMEOUT_SECONDS
        
        logger.info(f"LLM Client initialized with model: {self.model}")
    
    def call_llm(self, messages: list[dict]) -> str:
        """
        Chama o LLM com retry automático.
        
        Args:
            messages: Lista com mensagens no formato OpenAI.
        
        Returns:
            str: Resposta do LLM.
        
        Raises:
            APIError: Se o LLM falhar após todas as tentativas.
        """
        last_error = None
        
        for attempt in range(1, self.max_retries + 1):
            try:
                logger.debug(f"Calling LLM (attempt {attempt}/{self.max_retries})")
                
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    #temperature=self.temperature,
                    timeout=self.timeout,
                )
                
                # Extrai o conteúdo da resposta
                content = response.choices[0].message.content
                
                logger.debug(f"LLM response received (length: {len(content)})")
                return content
            
            except (RateLimitError, APITimeoutError) as e:
                # Erros recuperáveis
                last_error = e
                
                if attempt < self.max_retries:
                    wait_time = self.retry_delay * (2 ** (attempt - 1))  # Backoff exponencial
                    logger.warning(
                        f"LLM call failed (attempt {attempt}): {type(e).__name__}. "
                        f"Retrying in {wait_time}s..."
                    )
                    time.sleep(wait_time)
                else:
                    logger.error(f"LLM call failed after {self.max_retries} attempts")
            
            except APIError as e:
                # Erro fatal
                logger.error(f"LLM API error: {str(e)}")
                raise
        
        # Se chegou aqui, falhou após todas as tentativas
        raise APIError(
            f"Failed to call LLM after {self.max_retries} attempts. "
            f"Last error: {str(last_error)}"
        )
    
    def call_llm_for_json(self, messages: list[dict]) -> Dict[str, Any]:
        """
        Chama o LLM e espera uma resposta JSON.
        
        Trata erros de JSON e tenta extrair JSON inválido.
        
        Args:
            messages: Lista com mensagens no formato OpenAI.
        
        Returns:
            dict: Dicionário com a resposta parseada.
        
        Raises:
            ValueError: Se não conseguir extrair JSON válido da resposta.
        """
        response_text = self.call_llm(messages)
        
        try:
            # Tenta fazer parse direto
            return json.loads(response_text)
        
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse JSON from response: {str(e)}")
            
            # Tenta extrair JSON da resposta
            json_dict = self._extract_json_from_text(response_text)
            
            if json_dict is not None:
                logger.debug("Successfully extracted JSON from response text")
                return json_dict
            
            # Falha final
            logger.error(f"Invalid JSON response from LLM: {response_text[:200]}")
            raise ValueError(
                f"LLM returned invalid JSON. Response: {response_text[:500]}"
            )
    
    @staticmethod
    def _extract_json_from_text(text: str) -> Optional[Dict[str, Any]]:
        """
        Tenta extrair um dicionário JSON de um texto.
        
        Procura por padrões de dicionário Python e chaves JSON.
        
        Args:
            text: Texto para extrair JSON.
        
        Returns:
            dict ou None: Dicionário extraído ou None se não encontrado.
        """
        # Remove backticks de código Markdown se presentes
        text = text.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        
        # Tenta parse novamente
        try:
            return json.loads(text.strip())
        except json.JSONDecodeError:
            pass
        
        # Procura por um dicionário JSON entre chaves
        start_idx = text.find("{")
        end_idx = text.rfind("}")
        
        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            try:
                json_str = text[start_idx:end_idx + 1]
                return json.loads(json_str)
            except json.JSONDecodeError:
                pass
        
        return None
