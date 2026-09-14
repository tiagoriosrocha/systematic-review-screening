"""
Módulo principal da aplicação.

Orquestra todo o fluxo de processamento de artigos:
1. Carrega artigos do BibTeX
2. Filtra artigos já processados
3. Avalia cada artigo com LLM
4. Salva resultados incrementalmente
5. Exibe estatísticas finais
"""

import logging
import sys
from tqdm import tqdm
from datetime import datetime

from src.config import Config
from src.csv_handler import CSVHandler
from src.bibtex_handler import BibTexHandler
from src.evaluator import ArticleEvaluator
from src.prompt_builder import PromptBuilderPhase1, PromptBuilderPhase2, PromptBuilderPhase3


# Configurar logging
def setup_logging():
    """Configura o sistema de logging."""

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    
    # Create logger
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, Config.LOG_LEVEL))
    logger.handlers.clear()
    
    # File handler
    file_handler = logging.FileHandler(Config.LOG_FILE, encoding="utf-8")
    file_handler.setLevel(getattr(logging, Config.LOG_LEVEL))
    file_handler.setFormatter(logging.Formatter(Config.LOG_FORMAT))
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter(Config.LOG_FORMAT))
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    for logger_name in ("openai", "httpx", "httpcore"):
        logging.getLogger(logger_name).setLevel(logging.WARNING)
    
    return logger


def main():
    """
    Função principal que orquestra todo o processamento em três fases.
    
    Fluxo:
    1. FASE 1: Broad Screening (High Recall) → phase1_broad_screening.csv
    2. FASE 2: Strict Screening (High Precision) → phase2_strict_screening.csv
    3. FASE 3: Adjudication (Binary Decision) → phase3_adjudication.csv
    """
    # Configurar logging
    logger = setup_logging()
    
    logger.info("=" * 80)
    logger.info("Starting Two-Stage SLR LLM Screening")
    logger.info("=" * 80)
    
    try:
        # Validar configurações
        Config.validate()
        logger.info("Configuration validated successfully")
        
        # Ler artigos do BibTeX
        logger.info(f"Reading articles from: {Config.INPUT_BIB_FILE}")
        articles = BibTexHandler.read_articles(Config.INPUT_BIB_FILE)
        logger.info(f"Total articles in BibTeX: {len(articles)}")
        
        # ====== FASE 1: Broad Screening ======
        logger.info("=" * 80)
        logger.info("PHASE 1: Broad Screening (High Recall)")
        logger.info("=" * 80)
        
        already_processed_phase1 = CSVHandler.get_processed_ids(Config.OUTPUT_CSV_PHASE1)
        articles_to_process_phase1 = [
            a for a in articles 
            if a.bibtex_id not in already_processed_phase1
        ]
        
        logger.info(f"Articles already processed in Phase 1: {len(already_processed_phase1)}")
        logger.info(f"Articles to process in Phase 1: {len(articles_to_process_phase1)}")
        
        if articles_to_process_phase1:
            prompt_builder_phase1 = PromptBuilderPhase1()
            evaluator_phase1 = ArticleEvaluator(prompt_builder=prompt_builder_phase1)
            
            logger.info(f"Prompt builder: {prompt_builder_phase1.__class__.__name__}")
            
            try:
                for article in tqdm(
                    articles_to_process_phase1,
                    desc="Phase 1: Evaluating articles",
                    unit="article"
                ):
                    try:
                        result = evaluator_phase1.evaluate(article)
                        CSVHandler.write_result(Config.OUTPUT_CSV_PHASE1, result)
                    except Exception as e:
                        logger.error(f"Error evaluating article {article.bibtex_id} (Phase 1): {str(e)}")
                        continue
                
                logger.info("Phase 1 screening completed successfully")
            
            except KeyboardInterrupt:
                logger.warning("Phase 1 interrupted by user")
                sys.exit(130)
        else:
            logger.info("All articles already processed in Phase 1")
        
        # ====== FASE 2: Strict Screening ======
        logger.info("=" * 80)
        logger.info("PHASE 2: Strict Screening (High Precision)")
        logger.info("=" * 80)
        
        # Ler resultados da Phase 1 (apenas os "include" e "maybe")
        phase1_results = CSVHandler.read_results(Config.OUTPUT_CSV_PHASE1)
        
        # Criar mapa de justificativas da Phase 1: bibtex_id → justification
        justifications_map = {}
        for result in phase1_results:
            bibtex_id = result.get("bibtex_id")
            justification = result.get("justification", "")
            decision = result.get("decision")
            
            if decision in ["include", "maybe"]:
                justifications_map[bibtex_id] = justification
        
        logger.info(f"Phase 1 justifications loaded: {len(justifications_map)}")
        articles_for_phase2 = [
            r for r in phase1_results 
            if r.get("decision") in ["include", "maybe"]
        ]
        
        logger.info(f"Articles from Phase 1 for Phase 2: {len(articles_for_phase2)}")
        
        already_processed_phase2 = CSVHandler.get_processed_ids(Config.OUTPUT_CSV_PHASE2)
        articles_to_process_phase2 = [
            a for a in articles 
            if a.bibtex_id in [r.get("bibtex_id") for r in articles_for_phase2]
            and a.bibtex_id not in already_processed_phase2
        ]
        
        logger.info(f"Articles already processed in Phase 2: {len(already_processed_phase2)}")
        logger.info(f"Articles to process in Phase 2: {len(articles_to_process_phase2)}")
        
        if articles_to_process_phase2:
            prompt_builder_phase2 = PromptBuilderPhase2()
            evaluator_phase2 = ArticleEvaluator(prompt_builder=prompt_builder_phase2)
            
            logger.info(f"Prompt builder: {prompt_builder_phase2.__class__.__name__}")
            
            try:
                for article in tqdm(
                    articles_to_process_phase2,
                    desc="Phase 2: Evaluating articles",
                    unit="article"
                ):
                    try:
                        # Recuperar justificativa da Phase 1 como contexto
                        phase1_justification = justifications_map.get(article.bibtex_id, "")
                        
                        result = evaluator_phase2.evaluate(
                            article,
                            additional_context=phase1_justification
                        )
                        CSVHandler.write_result(Config.OUTPUT_CSV_PHASE2, result)
                    except Exception as e:
                        logger.error(f"Error evaluating article {article.bibtex_id} (Phase 2): {str(e)}")
                        continue
                
                logger.info("Phase 2 screening completed successfully")
            
            except KeyboardInterrupt:
                logger.warning("Phase 2 interrupted by user")
                sys.exit(130)
        else:
            logger.info("No articles to process in Phase 2")
        
        # ====== FASE 3: Adjudication (Binary Decision) ======
        logger.info("=" * 80)
        logger.info("PHASE 3: Adjudication (Binary Decision)")
        logger.info("=" * 80)
        
        # Ler resultados da Phase 2 (apenas os "maybe")
        phase2_results = CSVHandler.read_results(Config.OUTPUT_CSV_PHASE2)
        
        # Criar mapa de justificativas da Phase 2: bibtex_id → justification
        phase2_justifications_map = {}
        for result in phase2_results:
            bibtex_id = result.get("bibtex_id")
            justification = result.get("justification", "")
            decision = result.get("decision")
            
            if decision == "maybe":
                phase2_justifications_map[bibtex_id] = justification
        
        logger.info(f"Phase 2 maybe decisions to adjudicate: {len(phase2_justifications_map)}")
        
        articles_for_phase3 = [
            r for r in phase2_results 
            if r.get("decision") == "maybe"
        ]
        
        already_processed_phase3 = CSVHandler.get_processed_ids(Config.OUTPUT_CSV_PHASE3)
        articles_to_process_phase3 = [
            a for a in articles 
            if a.bibtex_id in [r.get("bibtex_id") for r in articles_for_phase3]
            and a.bibtex_id not in already_processed_phase3
        ]
        
        logger.info(f"Articles already processed in Phase 3: {len(already_processed_phase3)}")
        logger.info(f"Articles to process in Phase 3: {len(articles_to_process_phase3)}")
        
        if articles_to_process_phase3:
            prompt_builder_phase3 = PromptBuilderPhase3()
            evaluator_phase3 = ArticleEvaluator(prompt_builder=prompt_builder_phase3)
            
            logger.info(f"Prompt builder: {prompt_builder_phase3.__class__.__name__}")
            
            try:
                for article in tqdm(
                    articles_to_process_phase3,
                    desc="Phase 3: Adjudicating articles",
                    unit="article"
                ):
                    try:
                        # Recuperar justificativa da Phase 2 como contexto
                        phase2_justification = phase2_justifications_map.get(article.bibtex_id, "")
                        
                        result = evaluator_phase3.evaluate(
                            article,
                            additional_context=phase2_justification
                        )
                        CSVHandler.write_result(Config.OUTPUT_CSV_PHASE3, result)
                    except Exception as e:
                        logger.error(f"Error adjudicating article {article.bibtex_id} (Phase 3): {str(e)}")
                        continue
                
                logger.info("Phase 3 adjudication completed successfully")
            
            except KeyboardInterrupt:
                logger.warning("Phase 3 interrupted by user")
                sys.exit(130)
        else:
            logger.info("No articles to process in Phase 3")
        
        # ====== RESUMO FINAL ======
        logger.info("=" * 80)
        logger.info("Three-Stage Screening Finished Successfully")
        logger.info("=" * 80)
        logger.info(f"Phase 1 (Broad Screening) results saved to: {Config.OUTPUT_CSV_PHASE1}")
        logger.info(f"Phase 2 (Strict Screening) results saved to: {Config.OUTPUT_CSV_PHASE2}")
        logger.info(f"Phase 3 (Adjudication) results saved to: {Config.OUTPUT_CSV_PHASE3}")
    
    except ValueError as e:
        logger.error(f"Configuration error: {str(e)}")
        sys.exit(1)
    
    except FileNotFoundError as e:
        logger.error(f"File not found: {str(e)}")
        sys.exit(1)
    
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        sys.exit(1)


def _print_statistics(stats: dict) -> None:
    """
    Imprime estatísticas de avaliação.
    
    Args:
        stats: Dicionário com estatísticas.
    """
    logger = logging.getLogger()
    
    logger.info("")
    logger.info("EVALUATION STATISTICS:")
    logger.info(f"  Total articles: {stats['total']}")
    logger.info(f"  Included (entra): {stats['entra']} ({stats['percentual_entra']:.1f}%)")
    logger.info(f"  Excluded (não entra): {stats['nao_entra']} ({stats['percentual_nao_entra']:.1f}%)")
    logger.info(f"  Uncertain (pode ser): {stats['pode_ser']} ({stats['percentual_pode_ser']:.1f}%)")
    logger.info("")


if __name__ == "__main__":
    main()
