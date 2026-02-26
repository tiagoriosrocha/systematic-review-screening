# SLR LLM Reviewer

Ferramenta Python profissional para **triagem automática de artigos científicos (Systematic Literature Review)** usando Azure OpenAI com LLM.

## Características Principais

✅ **Automação Inteligente**: Avalia artigos automaticamente usando LLM  
✅ **Resposta Estruturada**: JSON validado com Pydantic  
✅ **Reprodutibilidade Científica**: Rastreia model, prompt_version e execution_date  
✅ **Tratamento Robusto**: Retry automático, timeout e validação forte  
✅ **Processamento Incremental**: Salva CSV a cada resultado, sem reprocessamento  
✅ **Logging Estruturado**: Rastreamento completo em arquivo e console  
✅ **Código Profissional**: Type hints, separação de responsabilidades, documentação completa  

## Estrutura do Projeto

```
slr_llm_reviewer/
│
├── src/
│   ├── __init__.py           # Package initialization
│   ├── config.py             # Configurações centralizadas
│   ├── models.py             # Modelos Pydantic (ArticleEvaluation)
│   ├── llm_client.py         # Cliente Azure OpenAI com retry
│   ├── prompt_builder.py     # Construtor de prompts
│   ├── evaluator.py          # Avaliador de artigos
│   ├── csv_handler.py        # I/O BibTeX/CSV
│   └── main.py               # Orquestração principal
│
├── input/
│   └── articles.bib          # Arquivo BibTeX com artigos
│
├── output/
│   └── artigos_avaliados.csv # Resultados (criado automaticamente)
│
├── logs/
│   └── slr_reviewer.log      # Log estruturado
│
├── .env.example              # Template de variáveis de ambiente
├── .env                      # Arquivo de configuração (não versionado)
├── requirements.txt          # Dependências Python
└── README.md                 # Este arquivo
```

## Requisitos

- **Python 3.11+**
- **Azure OpenAI API** (configurado)
- **Conta com acesso ao LLM** (gpt-4 recomendado)

## Instalação

### 1. Clonar o repositório

```bash
cd slr_llm_reviewer
```

### 2. Criar ambiente virtual Python

```bash
# Linux/Mac
python3 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
```

### 3. Instalar dependências

```bash
pip install -r requirements.txt
```

### 4. Configurar variáveis de ambiente

Copie o arquivo `.env.example` para `.env`:

```bash
cp .env.example .env
```

Edite `.env` com suas credenciais Azure OpenAI:

```env
LLM_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxx
LLM_ENDPOINT=https://your-resource-name.openai.azure.com/
LLM_API_VERSION=2024-02-15
LLM_MODEL=gpt-4
TEMPERATURE=0.3
```

### 5. Preparar arquivo BibTeX

Coloque seu arquivo `articles.bib` no diretório `input/`:

```bash
cp seu_arquivo.bib input/articles.bib
```

## Como Executar

### Execução básica

```bash
cd slr_llm_reviewer
python -m src.main
```

### Com variáveis de ambiente customizadas

```bash
# Usar temperatura diferente
TEMPERATURE=0.5 python -m src.main

# Usar modelo diferente
LLM_MODEL=gpt-4-turbo python -m src.main

# Aumentar verbosidade do log
LOG_LEVEL=DEBUG python -m src.main
```

### Exemplos de uso programático

```python
from src.csv_handler import BibTexHandler, CSVHandler
from src.evaluator import ArticleEvaluator
from src.prompt_builder import PromptBuilder

# Ler artigos
articles = BibTexHandler.read_articles("input/articles.bib")

# Criar avaliador
evaluator = ArticleEvaluator()

# Avaliar artigo
result = evaluator.evaluate(articles[0])
print(result.evaluation.decision)
print(result.evaluation.justification)

# Salvar resultado
CSVHandler.write_result("output/artigos_avaliados.csv", result)

# Obter estatísticas
stats = CSVHandler.get_statistics("output/artigos_avaliados.csv")
print(stats)
```

## Como Alterar Critérios do Prompt

Os critérios de inclusão/exclusão estão em [src/prompt_builder.py](src/prompt_builder.py).

### Editar critérios

```python
# Em src/prompt_builder.py

INCLUSION_CRITERIA = """
CRITÉRIOS DE INCLUSÃO:
- Seu critério 1
- Seu critério 2
...
"""

EXCLUSION_CRITERIA = """
CRITÉRIOS DE EXCLUSÃO:
- Seu critério 1
- Seu critério 2
...
"""
```

### Criar nova versão de prompt

```python
# Em src/prompt_builder.py

def create_v1_1() -> "PromptBuilder":
    """Factory method para criar PromptBuilder versão 1.1."""
    # Modifique os critérios aqui
    instance = PromptBuilder(version="1.1")
    # Customize conforme necessário
    return instance

# Em src/main.py ou seu script

prompt_builder = PromptBuilder.create_v1_1()
evaluator = ArticleEvaluator(prompt_builder=prompt_builder)
```

## Evoluir para Múltiplos Prompts (Experimentos Científicos)

Para comparar diferentes estratégias de avaliação:

### 1. Criar diferentes versões de prompt

```python
# src/prompt_builder.py

class PromptBuilder:
    @staticmethod
    def create_v1_0() -> "PromptBuilder":
        """Versão 1.0: Critérios estritos"""
        return PromptBuilder(version="1.0")
    
    @staticmethod
    def create_v1_1() -> "PromptBuilder":
        """Versão 1.1: Critérios moderados"""
        # Customize aqui
        return PromptBuilder(version="1.1")
    
    @staticmethod
    def create_v2_0() -> "PromptBuilder":
        """Versão 2.0: Critérios inclusivos"""
        # Customize aqui
        return PromptBuilder(version="2.0")
```

### 2. Executar experimento com múltiplas versões

```python
# experiment.py

from src.csv_handler import BibTexHandler, CSVHandler
from src.evaluator import ArticleEvaluator
from src.prompt_builder import PromptBuilder

articles = BibTexHandler.read_articles("input/articles.bib")

# Teste versão 1.0
evaluator_v1 = ArticleEvaluator(prompt_builder=PromptBuilder.create_v1_0())
results_v1 = [evaluator_v1.evaluate(a) for a in articles[:10]]

# Teste versão 1.1
evaluator_v2 = ArticleEvaluator(prompt_builder=PromptBuilder.create_v1_1())
results_v2 = [evaluator_v2.evaluate(a) for a in articles[:10]]

# Compare os resultados
# Os resultados terão prompt_version diferente para identificar qual versão
```

### 3. Analisar resultados

```python
# analysis.py

from src.csv_handler import CSVHandler

results = CSVHandler.read_results("output/artigos_avaliados.csv")

# Agrupar por prompt_version
v1_results = [r for r in results if r['prompt_version'] == '1.0']
v2_results = [r for r in results if r['prompt_version'] == '1.1']

# Comparar concordância, estatísticas, etc.
print(f"Versão 1.0 - Entra: {sum(1 for r in v1_results if r['decision'] == 'entra')}")
print(f"Versão 1.1 - Entra: {sum(1 for r in v2_results if r['decision'] == 'entra')}")
```

## Resultado Esperado

O script gera um arquivo CSV com estrutura:

| bibtex_id | title | decision | justification | model_name | prompt_version | execution_date | processing_time_seconds |
|-----------|-------|----------|---------------|------------|-----------------|------------------|-------------------------|
| rayyan-1 | Article Title | entra | Justificativa... | gpt-4 | 1.0 | 2024-02-26T14:30:00 | 2.45 |
| rayyan-2 | Another Title | não entra | Motivo... | gpt-4 | 1.0 | 2024-02-26T14:35:00 | 1.87 |

## Demonstração Rápida

```bash
# 1. Copiar template de ambiente
cp .env.example .env

# 2. Editar .env com suas credenciais

# 3. Executar (com 5 primeiros artigos para teste)
python -c "
from src.csv_handler import BibTexHandler
from src.evaluator import ArticleEvaluator
from src.config import Config

articles = BibTexHandler.read_articles(Config.INPUT_BIB_FILE)[:5]
evaluator = ArticleEvaluator()

for article in articles:
    result = evaluator.evaluate(article)
    print(f'{article.title[:50]}... -> {result.evaluation.decision}')
"
```

## Methodological Reproducibility Notes

### Por que rastrear `model_name`, `prompt_version` e `execution_date`?

A reprodutibilidade é **fundamental em pesquisa científica**. Este sistema foi projetado para garantir que qualquer pessoa possa reproduzir exatamente os mesmos resultados alterando apenas os critérios científicos, não a implementação técnica.

#### 1. **`model_name`** (ex: gpt-4)

- **Motivo**: Diferentes modelos têm comportamentos diferentes
- **Impacto**: Um LLM novo/atualizado pode gerar resultados diferentes
- **Reproducibilidade**: 
  - Documentar qual modelo foi usado permite que outros usem o *mesmo* modelo
  - Diferentes versões (gpt-4, gpt-4-turbo, gpt-35-turbo) têm capacidades e treinamentos diferentes
  - Em uma revisão sistemática, você quer que seus dados sejam comparáveis
  
**Exemplo científico**: 
```
"Resultados obtidos com gpt-4 (release Feb 2024) vs gpt-35-turbo podem divergir"
```

#### 2. **`prompt_version`** (ex: 1.0, 1.1, 2.0)

- **Motivo**: O prompt é o algoritmo de decisão do LLM
- **Impacto**: Pequenas mudanças no prompt podem resultar em decisões diferentes
- **Reproducibilidade**:
  - Versionar prompts permite rastrear qual regra de decisão foi usada
  - Permite comparação entre versões (v1.0 vs v2.0) de forma controlada
  - Facilita revisão: "qual critério mudou entre v1.0 e v1.1?"
  
**Exemplo científico**:
```
v1.0: Critério = "Digital Twin explicitamente mencionado"
v1.1: Critério = "Digital Twin ou Cyber-Physical System mencionado"

Comparar resultados identifica artigos sensíveis à definição de escopo
```

#### 3. **`execution_date`** (timestamp completo)

- **Motivo**: O comportamento do LLM pode mudar ao longo do tempo
- **Impacto**: Atualizações do modelo, mudanças de dataset de treinamento
- **Reproducibilidade**:
  - Timestamps permitem rastrear quando cada avaliação foi feita
  - Identifica se atualizações do modelo (Azure OpenAI) mudaram resultados
  - Importante para auditar: "foi feito com qual versão do serviço?"
  
**Exemplo científico**:
```
Resultados de fevereiro 2024 vs fevereiro 2025 podem diferir se:
- Modelo foi atualizado
- Versão API mudou
- Serviço teve manutenção
```

### Implicações Práticas

#### ✅ Controlado (Boas práticas)

```csv
bibtex_id,decision,model_name,prompt_version,execution_date
id1,entra,gpt-4,1.0,2024-02-26T14:30:00Z
id1,entra,gpt-4,1.1,2024-02-26T15:00:00Z
```
→ **Permite comparar exatamente o que mudou**: só a versão do prompt

#### ❌ Não controlado (Problema)

```csv
bibtex_id,decision
id1,entra
id1,não entra
```
→ **Impossível saber por quê mudou**: modelo? prompt? implementação?

### Cenários de Uso

**Cenário 1: Repetibilidade Interna**
```
Seu orientador pede: "Como você chegou a essa decisão?"
Resposta: "Artigo id1 foi avaliado em 2024-02-26 com gpt-4 
usando prompt_version 1.0. Veja na coluna decision."
```

**Cenário 2: Comparação de Estratégias**
```
Você quer comparar dois prompts:
SELECT COUNT(*) FROM results WHERE prompt_version='1.0' AND decision='entra'
SELECT COUNT(*) FROM results WHERE prompt_version='1.1' AND decision='entra'
```

**Cenário 3: Auditoría e Governança**
```
"Todos os artigos processados com gpt-4 entre 2024-02-20 e 2024-02-25
terão valores comparáveis. Os processados depois podem diferir (novo modelo)."
```

**Cenário 4: Publicação Científica**
```
Métodos: "Utilizamos Azure OpenAI (gpt-4, Feb 2024) com prompt versão 1.0.
Os critérios estão no apêndice. Código e dados estão disponíveis em [URL]."
```

### Boas Práticas Implementadas

1. **Automatização**: Campos preenchidos automaticamente (sem entrada manual)
2. **Imutabilidade**: Uma vez salvo, não pode mudar (CSV append-only)
3. **Rastreabilidade**: Cada decisão tem identificadores únicos
4. **Versionamento**: Prompts seguem semantic versioning
5. **Documentação**: Critérios salvos junto com resultados

### Recomendações para Pesquisa

1. **Versione explicitamente qualquer mudança no prompt**:
   - Mudança de critérios → novo PROMPT_VERSION
   - Use git para versionar `src/prompt_builder.py`

2. **Mantenha histórico completo**:
   - Nunca sobrescreva CSV, sempre faça append
   - Implemente backup antes de mudanças

3. **Documente decisões**:
   - Por que mudou de v1.0 para v1.1?
   - Quais resultados foram afetados?

4. **Valide independentemente**:
   - Peça a outro revisor avaliar uma amostra
   - Compare com prompt_version diferente
   - Analise concordância (inter-rater reliability)

5. **Para publicação**:
   - Inclua PROMPT_VERSION no paper
   - Forneça arquivo `.env.example` no apêndice
   - Cite data de execução e modelo específico

## Logging e Debugging

O sistema cria um arquivo `logs/slr_reviewer.log` com rastreamento completo.

### Exemplo de log

```
2024-02-26 14:30:00,000 - __main__ - INFO - Starting SLR LLM Reviewer
2024-02-26 14:30:00,150 - src.config - INFO - Configuration validated successfully
2024-02-26 14:30:01,200 - src.csv_handler - INFO - Reading BibTeX file: input/articles.bib
2024-02-26 14:30:05,450 - src.csv_handler - INFO - Successfully read 100 articles from BibTeX
2024-02-26 14:30:05,500 - src.evaluator - INFO - Starting evaluation of article: rayyan-471934058
2024-02-26 14:30:07,800 - src.evaluator - INFO - Article rayyan-471934058 evaluated as 'entra'
```

### Aumentar verbosidade

```bash
LOG_LEVEL=DEBUG python -m src.main
```

## Tratamento de Erros

O sistema é resiliente:

- ✅ **Retry automático**: Falha temporária? Tenta novamente
- ✅ **Continua processamento**: Um artigo falho não interrompe os outros
- ✅ **Incremental**: Pode pausar e retomar depois
- ✅ **Validação forte**: Resposta inválida é rejeitada com motivo claro

## Performance

- **Tempo médio por artigo**: 2-5 segundos (depende da IA/internet)
- **Com 1000 artigos**: ~1-2 horas
- **Costs**: ~$0.01-0.05 por artigo (depende do modelo)

## Troubleshooting

### Erro: `LLM_API_KEY não configurada`

```bash
# Solução: Editar .env
echo "LLM_API_KEY=sua_chave_aqui" >> .env
```

### Erro: `Failed to parse JSON from response`

O LLM retornou resposta inválida. Solução:

1. Verificar se o prompt é claro (talvez customizou mal)
2. Reduzir TEMPERATURE para 0.3-0.5
3. Usar modelo mais recente/potente
4. Adicionar exemplos no prompt

### Erro: `Timeout`

O LLM está lento ou não responde:

```bash
# Aumentar timeout
TIMEOUT_SECONDS=60 python -m src.main
```

## API Reference

### ArticleEvaluation (Pydantic Model)

```python
class ArticleEvaluation(BaseModel):
    decision: Literal["entra", "não entra", "pode ser"]
    justification: str  # min_length=10
```

### EvaluationResult

```python
class EvaluationResult(BaseModel):
    bibtex_id: str
    title: str
    evaluation: ArticleEvaluation
    model_name: str        # ex: "gpt-4"
    prompt_version: str    # ex: "1.0"
    execution_date: datetime
    processing_time_seconds: float
```

### Funções principais

```python
# Ler artigos
articles = BibTexHandler.read_articles(filepath)

# Avaliar artigo
result = evaluator.evaluate(article)

# Salvar resultado (incremental)
CSVHandler.write_result(csv_path, result)

# Estatísticas
stats = CSVHandler.get_statistics(csv_path)
```

## Limitações Conhecidas

1. **Qualidade LLM**: Resultado depende do LLM (mesmo com prompt perfeito)
2. **Alucinações**: LLM pode inventar informações
3. **Idiomas**: Prompt em português, LLM pode não entender tão bem
4. **Contexto**: Título + metadados podem não ser suficientes (não lê PDF)

## Próximos Passos

- [ ] Interface web/GUI
- [ ] Suporte a múltiplas LLMs (Anthropic, OpenAI, local)
- [ ] Leitura de PDF completo
- [ ] Machine Learning local para fine-tuning
- [ ] Análise de concordância inter-rater
- [ ] Dashboard de estatísticas

## Contribuindo

Melhorias são bem-vindas! Ideias:

- Novos prompts/critérios
- Otimizações de performance
- Suporte a mais formatos de entrada
- Visualizações dos resultados

## Referências

- [Azure OpenAI API Docs](https://learn.microsoft.com/en-us/azure/ai-services/openai/reference)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [Systematic Literature Review Guide](https://www.elsevier.com/en-gb/connect/systematic-review-methodology)

## Licença

MIT License

## Autor

Seu Nome

---

**Última atualização**: Fevereiro 2024  
**Versão**: 1.0.0
