# SLR LLM Reviewer

Ferramenta Python para **triagem automática de artigos em três fases** (Systematic Literature Review) usando Azure OpenAI.

## Instalação

```bash
# Criar ambiente virtual
python3 -m venv venv
source venv/bin/activate

# Instalar dependências
pip install -r requirements.txt

# Configurar ambiente
cp .env.example .env
# Editar .env com suas credenciais Azure OpenAI
```

## Execução

```bash
python src/main.py
```

## Fluxo de Triagem (3 Fases)

1. **Fase 1: Broad Screening** (Alta Sensibilidade/Recall)
   - Critérios amplos para maximizar inclusos
   - Opções: include, exclude, maybe
   - Saída: `phase1_broad_screening_[timestamp].csv`

2. **Fase 2: Strict Screening** (Alta Especificidade/Precisão)
   - Critérios rigorosos, reavalia independentemente
   - Recebe justificativa da Fase 1 como contexto
   - Opções: include, exclude, maybe
   - Saída: `phase2_strict_screening_[timestamp].csv`

3. **Fase 3: Adjudication** (Decisão Final)
   - Resolve ambiguidades da Fase 2
   - Sem opção "maybe" - decisão binária
   - Recebe justificativa da Fase 2 como contexto
   - Saída: `phase3_adjudication_[timestamp].csv`

## Estrutura

```
src/
├── config.py          # Configurações (caminhos, timestamps)
├── models.py          # Modelos Pydantic
├── llm_client.py      # Cliente Azure OpenAI
├── prompt_builder.py  # Prompts das 3 fases (abstrato + concreto)
├── evaluator.py       # Orquestrador LLM
├── csv_handler.py     # I/O BibTeX/CSV
└── main.py           # Execução das 3 fases
```

## Configuração (.env)

```env
LLM_API_KEY=your-key
LLM_ENDPOINT=https://your-resource.openai.azure.com/
LLM_API_VERSION=2024-02-15
LLM_MODEL=gpt-4
TEMPERATURE=0.3
```

## Customização de Critérios

Editar em `src/prompt_builder.py`:
- `PromptBuilderPhase1.INCLUSION_CRITERIA` - Fase 1
- `PromptBuilderPhase2.INCLUSION_CRITERIA` - Fase 2
- `PromptBuilderPhase3.INCLUSION_CRITERIA` - Fase 3

## Resultado

CSVs com colunas:
- `bibtex_id`, `title`, `decision`, `justification`, `prompt_identifier`, `execution_date`

---

**Versão**: 3.0.0 | **Ultima atualização**: Março 2026
