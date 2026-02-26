#!/usr/bin/env python3
"""
Script de execução da aplicação SLR LLM Reviewer.

Este script é o ponto de entrada da aplicação.
Ele valida o ambiente, instala dependências se necessário e executa o processamento.
"""

import sys
import os

# Adicionar o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.main import main

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Execução interrompida pelo usuário.")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Erro fatal: {e}")
        sys.exit(1)
