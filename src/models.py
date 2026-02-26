"""
Modelos Pydantic para validação de dados.

Este módulo define os modelos de dados utilizados para validar
as respostas do LLM, garantindo integridade e tipagem forte.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Literal
from datetime import datetime


class ArticleEvaluation(BaseModel):
    """
    Modelo para representar a avaliação de um artigo.
    
    Valida a resposta do LLM conforme esperado.
    """
    
    decision: Literal["entra", "não entra", "pode ser"] = Field(
        ..., 
        description="Decisão de inclusão do artigo"
    )
    justification: str = Field(
        ..., 
        min_length=10,
        description="Justificativa textual da decisão"
    )
    
    @field_validator('decision')
    @classmethod
    def validate_decision(cls, v: str) -> str:
        """Valida que a decisão é uma das opções permitidas."""
        valid_decisions = ["entra", "não entra", "pode ser"]
        if v not in valid_decisions:
            raise ValueError(
                f"Decision must be one of {valid_decisions}, got: {v}"
            )
        return v
    
    @field_validator('justification')
    @classmethod
    def validate_justification(cls, v: str) -> str:
        """Valida que a justificativa não está vazia."""
        if not v.strip():
            raise ValueError("Justification cannot be empty or whitespace only")
        return v
    
    class Config:
        """Configuração do modelo."""
        str_strip_whitespace = True
        json_schema_extra = {
            "example": {
                "decision": "entra",
                "justification": "O artigo aborda digital twins em manufatura, alinhado com o escopo da revisão sistemática."
            }
        }


class Article(BaseModel):
    """
    Modelo para representar um artigo científico do arquivo BibTeX.
    """
    
    bibtex_id: str = Field(..., description="ID único do artigo (chave BibTeX)")
    title: str = Field(..., description="Título do artigo")
    year: int = Field(..., description="Ano de publicação")
    abstract: str = Field(default="", description="Resumo do artigo")
    authors: str = Field(default="", description="Autores do artigo")
    journal: str = Field(default="", description="Periódico de publicação")
    doi: str = Field(default="", description="DOI do artigo")
    url: str = Field(default="", description="URL do artigo")
    
    class Config:
        """Configuração do modelo."""
        str_strip_whitespace = True


class EvaluationResult(BaseModel):
    """
    Modelo para representar o resultado completo da avaliação de um artigo.
    """
    
    bibtex_id: str = Field(..., description="ID único do artigo")
    title: str = Field(..., description="Título do artigo")
    evaluation: ArticleEvaluation = Field(..., description="Avaliação do artigo")
    model_name: str = Field(..., description="Nome do modelo LLM utilizado")
    prompt_version: str = Field(..., description="Versão do prompt utilizado")
    execution_date: datetime = Field(..., description="Data/hora da execução")
    processing_time_seconds: float = Field(..., description="Tempo de processamento em segundos")
    
    class Config:
        """Configuração do modelo."""
        str_strip_whitespace = True
