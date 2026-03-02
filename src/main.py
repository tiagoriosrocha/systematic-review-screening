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
from src.prompt_builder import PromptBuilder, PromptBuilderEnglish


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


def main():
    """
    Função principal que orquestra todo o processamento.
    """
    # Configurar logging
    logger = setup_logging()
    
    logger.info("=" * 80)
    logger.info("Starting SLR LLM Reviewer")
    logger.info("=" * 80)
    
    try:
        # Validar configurações
        Config.validate()
        logger.info("Configuration validated successfully")
        logger.info(f"Configuration: {Config.to_dict()}")
        
        # Ler artigos do BibTeX
        logger.info(f"Reading articles from: {Config.INPUT_BIB_FILE}")
        articles = BibTexHandler.read_articles(Config.INPUT_BIB_FILE)
        logger.info(f"Total articles in BibTeX: {len(articles)}")
        
        # Obter IDs já processados
        already_processed = CSVHandler.get_processed_ids(Config.OUTPUT_CSV_FILE)
        articles_to_process = [
            a for a in articles 
            if a.bibtex_id not in already_processed
        ]
        
        logger.info(f"Articles already processed: {len(already_processed)}")
        logger.info(f"Articles to process: {len(articles_to_process)}")
        
        if not articles_to_process:
            logger.info("All articles have already been processed!")
            stats = CSVHandler.get_statistics(Config.OUTPUT_CSV_FILE)
            _print_statistics(stats)
            return
        
        # Criar avaliador
        # Use PromptBuilder.create_v1_0() para português
        # Use PromptBuilderEnglish.create_v2_0() para inglês
        prompt_builder = PromptBuilderEnglish.create_v2_0()
        evaluator = ArticleEvaluator(prompt_builder=prompt_builder)
        
        logger.info("Article Evaluator initialized")
        logger.info(f"Model: {evaluator.llm_client.model}")
        logger.info(f"Prompt version: {prompt_builder.get_version()}")
        
        # Processar artigos com barra de progresso
        logger.info("Starting article evaluation...")
        
        try:
            for article in tqdm(
                articles_to_process, 
                desc="Evaluating articles",
                unit="article"
            ):
                try:
                    # Avaliar artigo
                    result = evaluator.evaluate(article)
                    
                    # Salvar resultado incrementalmente no CSV
                    CSVHandler.write_result(Config.OUTPUT_CSV_FILE, result)
                
                except Exception as e:
                    logger.error(f"Error evaluating article {article.bibtex_id}: {str(e)}")
                    # Continua com próximo artigo
                    continue
            
            logger.info("Article evaluation completed successfully")
            
            # Ler resultados do CSV completo
            #logger.info("Reading evaluation results from CSV...")
            #csv_results = CSVHandler.read_results(Config.OUTPUT_CSV_FILE)
            #
            # Atualizar arquivo BibTeX com resultados da avaliação lidos do CSV
            #if csv_results:
            #    logger.info(f"Updating BibTeX file with {len(csv_results)} evaluation results...")
            #    BibTexHandler.update_evaluation_notes_from_csv(
            #        Config.INPUT_BIB_FILE,
            #        csv_results
            #    )
            #    logger.info(f"BibTeX file updated: {Config.INPUT_BIB_FILE}")
            
            logger.info("=" * 80)
            logger.info("SLR LLM Reviewer finished successfully")
            logger.info("=" * 80)
            logger.info(f"Results saved to: {Config.OUTPUT_CSV_FILE}")
            logger.info(f"BibTeX file updated: {Config.INPUT_BIB_FILE}")
        
        except KeyboardInterrupt:
            logger.warning("Processing interrupted by user")
            logger.warning("Partial results have been saved")
            sys.exit(130)
    
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
