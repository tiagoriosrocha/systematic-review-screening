"""
Gerenciador de entrada (BibTeX) e saída (CSV).

Este módulo fornece funcionalidades para:
- Ler artigos do arquivo BibTeX
- Escrever resultados em CSV
- Evitar reprocessamento de artigos já avaliados
- Fazer scraping de abstracts de URLs quando não disponível no BibTeX
"""

import csv
import logging
import os
import time
import shutil
import re
from typing import List, Set, Dict, Any, Optional
from bibtexparser import parse_file
import requests
from bs4 import BeautifulSoup

from src.models import Article, EvaluationResult
from src.config import Config


logger = logging.getLogger(__name__)


class BibTexHandler:
    """
    Lê e processa arquivos BibTeX.
    
    Pode fazer scraping de abstracts de URLs quando não disponível no arquivo.
    """
    
    # Timeout para requisições HTTP (segundos)
    REQUEST_TIMEOUT = 10
    # Delay entre requisições para respeitar servers (segundos)
    REQUEST_DELAY = 1
    
    @staticmethod
    def read_articles(bib_file: str) -> List[Article]:
        """
        Lê artigos de um arquivo BibTeX.
        
        Args:
            bib_file: Caminho do arquivo BibTeX.
        
        Returns:
            Lista de artigos parseados.
        
        Raises:
            FileNotFoundError: Se o arquivo não existir.
            ValueError: Se houver erro ao fazer parse do BibTeX.
        """
        if not os.path.exists(bib_file):
            raise FileNotFoundError(f"BibTeX file not found: {bib_file}")
        
        logger.info(f"Reading BibTeX file: {bib_file}")
        
        try:
            # Parse BibTeX
            bibtex_db = parse_file(bib_file)
            
            articles = []
            
            for entry in bibtex_db.entries:
                try:
                    article = Article(
                        bibtex_id=entry.key,
                        title=entry.fields_dict.get("title", {}).value if entry.fields_dict.get("title") else "",
                        year=int(entry.fields_dict.get("year", {}).value) if entry.fields_dict.get("year") else 0,
                        abstract=entry.fields_dict.get("abstract", {}).value if entry.fields_dict.get("abstract") else "",
                        authors=entry.fields_dict.get("author", {}).value if entry.fields_dict.get("author") else "",
                        journal=entry.fields_dict.get("journal", {}).value if entry.fields_dict.get("journal") else "",
                        doi=entry.fields_dict.get("doi", {}).value if entry.fields_dict.get("doi") else "",
                        url=entry.fields_dict.get("url", {}).value if entry.fields_dict.get("url") else "",
                    )
                    articles.append(article)
                
                except Exception as e:
                    logger.warning(f"Error parsing article entry {entry.key}: {str(e)}")
                    continue
            
            logger.info(f"Successfully read {len(articles)} articles from BibTeX")
            
            # Enriquecer abstracts a partir de URLs se necessário
            articles_with_abstracts = BibTexHandler._enrich_abstracts(articles, bib_file)
            
            return articles_with_abstracts
        
        except Exception as e:
            logger.error(f"Error reading BibTeX file: {str(e)}")
            raise ValueError(f"Failed to parse BibTeX file: {str(e)}")
    
    @staticmethod
    def _enrich_abstracts(articles: List[Article], bib_file: str = Config.INPUT_BIB_FILE) -> List[Article]:
        """
        Enriquece artigos com abstracts obtidos de URLs quando não disponível.
        
        Também atualiza o arquivo BibTeX original com os abstracts encontrados.
        
        Args:
            articles: Lista de artigos lidos do BibTeX.
            bib_file: Caminho do arquivo BibTeX original.
        
        Returns:
            Lista de artigos com abstracts preenchidos quando possível.
        """
        articles_without_abstract = [
            a for a in articles 
            if not a.abstract or a.abstract.strip() == ""
        ]
        
        if not articles_without_abstract:
            logger.debug("All articles have abstracts")
            return articles
        
        logger.info(
            f"Found {len(articles_without_abstract)} articles without abstract. "
            f"Attempting to fetch from URLs..."
        )
        
        # Dicionário para rastrear abstracts encontrados
        abstracts_found = {}
        
        for article in articles_without_abstract:
            if not article.url:
                logger.debug(f"Article {article.bibtex_id} has no URL, skipping")
                continue
            
            try:
                abstract = BibTexHandler._fetch_abstract_from_url(article.url)
                if abstract:
                    article.abstract = abstract
                    abstracts_found[article.bibtex_id] = abstract
                    logger.debug(f"Successfully fetched abstract for {article.bibtex_id}")
                else:
                    logger.debug(f"No abstract found at URL for {article.bibtex_id}")
                
                # Respeitar o servidor - delay entre requisições
                time.sleep(BibTexHandler.REQUEST_DELAY)
            
            except Exception as e:
                logger.warning(
                    f"Error fetching abstract for {article.bibtex_id}: {str(e)}"
                )
                # Continua com próximo artigo em caso de erro
                continue
        
        # Atualizar arquivo BibTeX com abstracts encontrados
        if abstracts_found:
            try:
                BibTexHandler._update_bibtex_file(bib_file, abstracts_found)
                logger.info(f"Updated {len(abstracts_found)} abstracts in {bib_file}")
            except Exception as e:
                logger.warning(f"Error updating BibTeX file with abstracts: {str(e)}")
        
        return articles
    
    @staticmethod
    def _update_bibtex_file(bib_file: str, abstracts: Dict[str, str]) -> None:
        """
        Atualiza o arquivo BibTeX original com abstracts encontrados.
        
        Faz backup antes de atualizar além de procurar-e-substituir de forma segura.
        
        Args:
            bib_file: Caminho do arquivo BibTeX.
            abstracts: Dicionário {bibtex_id: abstract_text}.
        
        Raises:
            Exception: Em caso de erro ao atualizar arquivo.
        """
        if not abstracts:
            return
        
        if not os.path.exists(bib_file):
            logger.warning(f"BibTeX file not found: {bib_file}")
            return
        
        try:
            # Criar backup do arquivo original
            backup_file = f"{bib_file}.backup"
            shutil.copy2(bib_file, backup_file)
            logger.info(f"Created backup of BibTeX file: {backup_file}")
            
            # Ler arquivo BibTeX original
            with open(bib_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Para cada abstract encontrado, adicionar ou atualizar no BibTeX
            for bibtex_id, abstract_text in abstracts.items():
                # Escapar caracteres especiais no abstract para BibTeX
                abstract_safe = abstract_text.replace('"', '\\"').replace('\n', ' ')
                
                # Procurar o entry do artigo
                # Buscar padrão: @article{bibtex_id, ... }
                # Pattern para encontrar o entry específico
                # Formato: @article{id, ... } ou @article{id,\n...}
                pattern = rf'(@\w+\{{\s*{re.escape(bibtex_id)}\s*,[^}}]*?)(\n\s*\}})'
                
                # Se o entry já tem abstract, substituir
                abstract_pattern = rf'(@\w+\{{{re.escape(bibtex_id)}[^}}]*abstract\s*=\s*[{{"]])[^}}"]+([}}"]][^}}]*}})'
                
                if re.search(abstract_pattern, content, re.DOTALL):
                    # Atualizar abstract existente
                    content = re.sub(
                        abstract_pattern,
                        rf'\1{{{abstract_safe}}}\2',
                        content,
                        flags=re.DOTALL
                    )
                    logger.debug(f"Updated existing abstract for {bibtex_id}")
                else:
                    # Adicionar abstract antes da chave de fechamento
                    content = re.sub(
                        pattern,
                        rf'\1,\n  abstract = {{\"{abstract_safe}\"}}\2',
                        content,
                        flags=re.DOTALL
                    )
                    logger.debug(f"Added new abstract for {bibtex_id}")
            
            # Escrever arquivo atualizado
            with open(bib_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.info(f"Successfully updated BibTeX file with {len(abstracts)} abstracts")
        
        except Exception as e:
            logger.error(f"Error updating BibTeX file: {str(e)}")
            # Tentar restaurar backup se algo deu errado
            if os.path.exists(backup_file):
                try:
                    shutil.copy2(backup_file, bib_file)
                    logger.warning(f"Restored backup due to error")
                except Exception as restore_error:
                    logger.error(f"Failed to restore backup: {str(restore_error)}")
            raise
    
    @staticmethod
    def _fetch_abstract_from_url(url: str) -> Optional[str]:
        """
        Faz scraping de abstract de uma URL de artigo.
        
        Suporta estrutura Springer e outras publishers similares.
        
        Args:
            url: URL do artigo.
        
        Returns:
            String com abstract encontrado ou None.
        
        Raises:
            Pode lançar exceções de requisição HTTP.
        """
        if not url or not url.strip():
            return None
        
        try:
            # Fazer requisição à URL
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                              'AppleWebKit/537.36 (KHTML, like Gecko)'
            }
            
            response = requests.get(
                url, 
                timeout=BibTexHandler.REQUEST_TIMEOUT,
                headers=headers,
                allow_redirects=True
            )
            response.raise_for_status()
            
            # Fazer parsing do HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Tentar encontrar abstract em estrutura Springer
            # <section aria-labelledby="Abs1" data-title="Abstract">
            abstract_section = soup.find(
                'section', 
                attrs={'data-title': 'Abstract'}
            )
            
            if abstract_section:
                # Procurar por <div class="c-article-section__content">
                content_div = abstract_section.find(
                    'div', 
                    class_='c-article-section__content'
                )
                
                if content_div:
                    # Extrair texto de todos os <p> dentro
                    paragraphs = content_div.find_all('p')
                    abstract_text = ' '.join([p.get_text() for p in paragraphs])
                    
                    if abstract_text.strip():
                        return abstract_text.strip()
            
            # Fallback: procurar por meta tags (og:description, description)
            og_description = soup.find('meta', property='og:description')
            if og_description:
                content = og_description.get('content', '')
                if content and len(content) > 20:
                    return content
            
            meta_description = soup.find('meta', attrs={'name': 'description'})
            if meta_description:
                content = meta_description.get('content', '')
                if content and len(content) > 20:
                    return content
            
            # Fallback: procurar por qualquer seção com "abstract" no nome
            for section in soup.find_all(['section', 'div'], {'id': lambda x: x and 'abs' in x.lower()}):
                text_content = section.get_text()
                if len(text_content) > 50:
                    return text_content.strip()[:500]  # Limitar a 500 caracteres
            
            return None
        
        except requests.RequestException as e:
            logger.debug(f"HTTP request failed for {url}: {str(e)}")
            return None
        
        except Exception as e:
            logger.debug(f"Error parsing abstract from {url}: {str(e)}")
            return None


class CSVHandler:
    """
    Gerencia leitura e escrita de arquivo CSV de resultados.
    """
    
    FIELDNAMES = [
        "bibtex_id",
        "title",
        "decision",
        "justification",
        "model_name",
        "prompt_version",
        "execution_date",
        "processing_time_seconds"
    ]
    
    @staticmethod
    def file_exists(csv_file: str) -> bool:
        """
        Verifica se o arquivo CSV existe.
        
        Args:
            csv_file: Caminho do arquivo CSV.
        
        Returns:
            bool: True se existe, False caso contrário.
        """
        return os.path.exists(csv_file)
    
    @staticmethod
    def get_processed_ids(csv_file: str) -> Set[str]:
        """
        Lê os IDs de artigos já processados do CSV.
        
        Args:
            csv_file: Caminho do arquivo CSV.
        
        Returns:
            Set com IDs já processados (vazio se arquivo não existe).
        """
        if not CSVHandler.file_exists(csv_file):
            return set()
        
        processed_ids = set()
        
        try:
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row and 'bibtex_id' in row:
                        processed_ids.add(row['bibtex_id'])
            
            logger.debug(f"Found {len(processed_ids)} already processed articles")
            return processed_ids
        
        except Exception as e:
            logger.warning(f"Error reading processed IDs from CSV: {str(e)}")
            return set()
    
    @staticmethod
    def write_result(csv_file: str, result: EvaluationResult) -> None:
        """
        Escreve um resultado de avaliação no CSV (incremental).
        
        Escreve cabeçalho se o arquivo não existir.
        
        Args:
            csv_file: Caminho do arquivo CSV.
            result: Resultado da avaliação.
        """
        file_exists = CSVHandler.file_exists(csv_file)
        
        try:
            with open(csv_file, 'a', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=CSVHandler.FIELDNAMES)
                
                # Escreve cabeçalho se arquivo é novo
                if not file_exists:
                    writer.writeheader()
                    logger.info(f"Created new CSV file: {csv_file}")
                
                # Escreve resultado
                row = {
                    "bibtex_id": result.bibtex_id,
                    "title": result.title,
                    "decision": result.evaluation.decision,
                    "justification": result.evaluation.justification,
                    "model_name": result.model_name,
                    "prompt_version": result.prompt_version,
                    "execution_date": result.execution_date.isoformat(),
                    "processing_time_seconds": result.processing_time_seconds,
                }
                
                writer.writerow(row)
                logger.debug(f"Wrote result for article {result.bibtex_id} to CSV")
        
        except Exception as e:
            logger.error(f"Error writing result to CSV: {str(e)}")
            raise
    
    @staticmethod
    def read_results(csv_file: str) -> List[Dict[str, Any]]:
        """
        Lê todos os resultados do arquivo CSV.
        
        Args:
            csv_file: Caminho do arquivo CSV.
        
        Returns:
            Lista de dicionários com resultados.
        """
        if not CSVHandler.file_exists(csv_file):
            logger.warning(f"CSV file does not exist: {csv_file}")
            return []
        
        results = []
        
        try:
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                results = list(reader)
            
            logger.info(f"Read {len(results)} results from CSV")
            return results
        
        except Exception as e:
            logger.error(f"Error reading CSV file: {str(e)}")
            raise
    
    @staticmethod
    def get_statistics(csv_file: str) -> Dict[str, Any]:
        """
        Calcula estatísticas dos resultados no CSV.
        
        Args:
            csv_file: Caminho do arquivo CSV.
        
        Returns:
            Dicionário com estatísticas.
        """
        results = CSVHandler.read_results(csv_file)
        
        if not results:
            return {
                "total": 0,
                "entra": 0,
                "nao_entra": 0,
                "pode_ser": 0,
                "percentual_entra": 0.0,
                "percentual_nao_entra": 0.0,
                "percentual_pode_ser": 0.0,
            }
        
        total = len(results)
        entra = sum(1 for r in results if r.get('decision') == 'entra')
        nao_entra = sum(1 for r in results if r.get('decision') == 'não entra')
        pode_ser = sum(1 for r in results if r.get('decision') == 'pode ser')
        
        return {
            "total": total,
            "entra": entra,
            "nao_entra": nao_entra,
            "pode_ser": pode_ser,
            "percentual_entra": (entra / total * 100) if total > 0 else 0.0,
            "percentual_nao_entra": (nao_entra / total * 100) if total > 0 else 0.0,
            "percentual_pode_ser": (pode_ser / total * 100) if total > 0 else 0.0,
        }
