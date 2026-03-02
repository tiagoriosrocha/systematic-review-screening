#!/usr/bin/env python3
"""
Script simples para atualizar o arquivo BibTeX com resultados da avaliação.

Uso:
    python atualizar_bibtex.py
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.config import Config
from src.csv_handler import CSVHandler
from src.bibtex_handler import BibTexHandler


def main():
    """Função principal."""
    
    print("\n" + "="*60)
    print("ATUALIZAR BIBTEX COM RESULTADOS DO CSV")
    print("="*60 + "\n")
    
    try:
        # Arquivos
        bib_file = Config.INPUT_BIB_FILE
        csv_file = Config.OUTPUT_CSV_FILE
        
        print(f"BibTeX: {bib_file}")
        print(f"CSV:    {csv_file}\n")
        
        # Validar arquivos
        if not os.path.exists(bib_file):
            print(f"Erro: BibTeX não encontrado: {bib_file}")
            return 1
        
        if not os.path.exists(csv_file):
            print(f"Erro: CSV não encontrado: {csv_file}")
            print("   Execute 'python run.py' primeiro\n")
            return 1
        
        # Ler CSV
        print("Lendo CSV...")
        csv_results = CSVHandler.read_results(csv_file)
        
        if not csv_results:
            print("Erro: CSV vazio\n")
            return 1
        
        print(f"{len(csv_results)} resultados encontrados\n")
        
        # Atualizar BibTeX
        print("Atualizando BibTeX...")
        BibTexHandler.update_evaluation_notes_from_csv(bib_file, csv_results)
        
        print(f"BibTeX atualizado com sucesso!\n")
        
        print("="*60)
        print("OPERAÇÃO CONCLUÍDA")
        print("="*60 + "\n")
        
        return 0
    
    except Exception as e:
        print(f"Erro: {e}\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
