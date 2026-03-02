"""
Gerenciador de BibTeX
Compatível com bibtexparser==1.4.4
"""
import logging
import os
import time
from typing import List, Set, Dict, Any, Optional

import requests
from bs4 import BeautifulSoup
import bibtexparser

from src.models import Article, EvaluationResult
from src.config import Config


logger = logging.getLogger(__name__)


class BibTexHandler:
    """
    Lê e processa arquivos BibTeX usando bibtexparser 1.4.4.
    """

    REQUEST_TIMEOUT = 10
    REQUEST_DELAY = 1

    @staticmethod
    def read_articles(bib_file: str) -> List[Article]:

        if not os.path.exists(bib_file):
            raise FileNotFoundError(f"BibTeX file not found: {bib_file}")

        logger.info(f"Reading BibTeX file: {bib_file}")

        try:
            with open(bib_file, encoding="utf-8") as bibtex_file:
                bib_database = bibtexparser.load(bibtex_file)

            articles: List[Article] = []

            for entry in bib_database.entries:
                try:
                    article = Article(
                        bibtex_id=entry.get("ID", ""),
                        title=entry.get("title", ""),
                        year=int(entry.get("year", 0)) if entry.get("year") else 0,
                        abstract=entry.get("abstract", ""),
                        authors=entry.get("author", ""),
                        journal=entry.get("journal", ""),
                        doi=entry.get("doi", ""),
                        url=entry.get("url", ""),
                    )

                    articles.append(article)

                except Exception as e:
                    logger.warning(f"Error parsing entry {entry.get('ID', '')}: {e}")
                    continue

            logger.info(f"Successfully read {len(articles)} articles")

            articles = BibTexHandler._enrich_abstracts(articles, bib_file)

            return articles

        except Exception as e:
            logger.error(f"Error parsing BibTeX: {e}")
            raise ValueError(f"Failed to parse BibTeX file: {e}")

    @staticmethod
    def _enrich_abstracts(
        articles: List[Article],
        bib_file: str = Config.INPUT_BIB_FILE
    ) -> List[Article]:

        articles_without_abstract = [
            a for a in articles if not a.abstract or not a.abstract.strip()
        ]

        if not articles_without_abstract:
            return articles

        logger.info(
            f"Fetching abstracts for {len(articles_without_abstract)} articles..."
        )

        abstracts_found: Dict[str, str] = {}

        for article in articles_without_abstract:

            if not article.url:
                continue

            try:
                abstract = BibTexHandler._fetch_abstract_from_url(article.url)
                logger.info(f"Abstract fetched for article {article.bibtex_id}")

                if abstract:
                    article.abstract = abstract
                    abstracts_found[article.bibtex_id] = abstract

                time.sleep(BibTexHandler.REQUEST_DELAY)

            except Exception as e:
                logger.warning(f"Error fetching abstract for {article.bibtex_id}: {e}")
                continue

        if abstracts_found:
            BibTexHandler._update_bibtex_file(bib_file, abstracts_found)

        return articles

    @staticmethod
    def _update_bibtex_file(
        bib_file: str,
        abstracts: Dict[str, str]
    ) -> None:

        if not abstracts:
            return

        logger.info("Updating BibTeX file with new abstracts")

        with open(bib_file, encoding="utf-8") as bibtex_file:
            bib_database = bibtexparser.load(bibtex_file)

        updated_count = 0

        for entry in bib_database.entries:
            entry_id = entry.get("ID", "")
            if entry_id in abstracts:
                entry["abstract"] = abstracts[entry_id]
                updated_count += 1

        with open(bib_file, "w", encoding="utf-8") as bibtex_file:
            bibtexparser.dump(bib_database, bibtex_file)

        logger.info(f"Updated {updated_count} abstracts in BibTeX")

    @staticmethod
    def update_evaluation_notes_from_csv(
        bib_file: str,
        csv_results: List[Dict[str, Any]]
    ) -> None:
        """
        Atualiza o campo 'note' do BibTeX com os resultados do CSV.
        
        Args:
            bib_file: Caminho do arquivo BibTeX
            csv_results: Lista de dicionários com resultados lidos do CSV
        """
        
        if not csv_results:
            logger.warning("No CSV results to update")
            return

        if not os.path.exists(bib_file):
            raise FileNotFoundError(f"BibTeX file not found: {bib_file}")

        logger.info(f"Updating BibTeX file with CSV results: {bib_file}")

        try:
            with open(bib_file, encoding="utf-8") as bibtex_file:
                bib_database = bibtexparser.load(bibtex_file)

            # Criar mapping de resultados por bibtex_id a partir do CSV
            results_map = {
                result["bibtex_id"]: result 
                for result in csv_results
            }

            updated_count = 0

            for entry in bib_database.entries:
                entry_id = entry.get("ID", "")
                
                if entry_id not in results_map:
                    continue

                result = results_map[entry_id]
                
                # Determinar decision em inglês para o note
                decision_map = {
                    "entra": "Included",
                    "não entra": "Excluded",
                    "pode ser": "Maybe"
                }
                decision = result.get("decision", "")
                decision_en = decision_map.get(decision, decision)
                
                # Obter justificativa
                justification = result.get("justification", "")
                
                # Construir note com o novo formato
                new_note = (
                    f'RAYYAN-INCLUSION: {{"LLM-Evaluator"=>"{decision_en}"}} | '
                    f'RAYYAN-EXCLUSION-REASONS: {justification}'
                )
                
                entry["note"] = new_note
                updated_count += 1
                
                logger.debug(f"Updated note for article {entry_id}: {decision_en}")

            # Salvar arquivo atualizado
            with open(bib_file, "w", encoding="utf-8") as bibtex_file:
                bibtexparser.dump(bib_database, bibtex_file)

            logger.info(f"Successfully updated {updated_count} evaluation notes in BibTeX from CSV")

        except Exception as e:
            logger.error(f"Error updating BibTeX with CSV results: {e}")
            raise ValueError(f"Failed to update BibTeX file: {e}")

    @staticmethod
    def update_evaluation_notes(
        bib_file: str,
        evaluation_results: List[EvaluationResult]
    ) -> None:
        """
        Atualiza o campo 'note' do BibTeX com os resultados da avaliação do LLM.
        DEPRECATED: Use update_evaluation_notes_from_csv() instead.
        
        Args:
            bib_file: Caminho do arquivo BibTeX
            evaluation_results: Lista de resultados de avaliação
        """
        
        if not evaluation_results:
            logger.warning("No evaluation results to update")
            return

        if not os.path.exists(bib_file):
            raise FileNotFoundError(f"BibTeX file not found: {bib_file}")

        logger.info(f"Updating BibTeX file with evaluation results: {bib_file}")

        try:
            with open(bib_file, encoding="utf-8") as bibtex_file:
                bib_database = bibtexparser.load(bibtex_file)

            # Criar mapping de resultados por bibtex_id
            results_map = {
                result.bibtex_id: result 
                for result in evaluation_results
            }

            updated_count = 0

            for entry in bib_database.entries:
                entry_id = entry.get("ID", "")
                
                if entry_id not in results_map:
                    continue

                result = results_map[entry_id]
                
                # Determinar decision em inglês para o note
                decision_map = {
                    "entra": "Included",
                    "não entra": "Excluded",
                    "pode ser": "Maybe"
                }
                decision_en = decision_map.get(result.evaluation.decision, result.evaluation.decision)
                
                # Construir note com o novo formato
                new_note = (
                    f'RAYYAN-INCLUSION: {{"LLM-Evaluator"=>"{decision_en}"}} | '
                    f'RAYYAN-EXCLUSION-REASONS: {result.evaluation.justification}'
                )
                
                entry["note"] = new_note
                updated_count += 1
                
                logger.debug(f"Updated note for article {entry_id}")

            # Salvar arquivo atualizado
            with open(bib_file, "w", encoding="utf-8") as bibtex_file:
                bibtexparser.dump(bib_database, bibtex_file)

            logger.info(f"Successfully updated {updated_count} evaluation notes in BibTeX")

        except Exception as e:
            logger.error(f"Error updating BibTeX with evaluation results: {e}")
            raise ValueError(f"Failed to update BibTeX file: {e}")

    @staticmethod
    def _fetch_abstract_from_url(url: str) -> Optional[str]:

        if not url:
            return None

        try:
            headers = {"User-Agent": "Mozilla/5.0"}

            response = requests.get(
                url,
                timeout=BibTexHandler.REQUEST_TIMEOUT,
                headers=headers,
                allow_redirects=True
            )

            response.raise_for_status()

            soup = BeautifulSoup(response.content, "html.parser")

            # Springer structure
            abstract_section = soup.find("section", attrs={"data-title": "Abstract"})
            if abstract_section:
                text = abstract_section.get_text(strip=True)
                if text:
                    return text

            # og:description
            og = soup.find("meta", property="og:description")
            if og and og.get("content"):
                return og["content"]

            # meta description
            meta = soup.find("meta", attrs={"name": "description"})
            if meta and meta.get("content"):
                return meta["content"]

            return None

        except Exception as e:
            logger.debug(f"Error fetching abstract from {url}: {e}")
            return None