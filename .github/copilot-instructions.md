# AI Coding Agent Instructions for Expense-agent

## Project Overview
Expense-agent is an AI-powered personal finance analysis system that ingests transaction CSVs, classifies expenses, and provides insights via a Streamlit dashboard. The system uses a dual-classification strategy (rule-based + LLM fallback) to categorize transactions and DuckDB for analytics.

## Architecture & Data Flow

### Core Pipeline (run_pipeline.py)
Sequential ETL pipeline with strict dependency order:
1. **Ingest** (`src/ingest/revolut_csv.py`): CSV → DuckDB `transactions_raw` table
2. **Transform** (`src/transform/clean_transactions.py`): Normalizes, deduplicates → `transactions_clean`
3. **Classify** (`src/classify/run_classification.py`): Uses orchestrator → `transactions_final` with categories
4. **Analytics** (`src/analytics/metrics.py`): Generates aggregated views (`metrics_monthly`, `metrics_by_category`, `metrics_trends`, `metrics_anomalies`)

**Key pattern**: Each step reads a specific table and writes a new one; failures in earlier steps break downstream processing.

### Agent Architecture (src/agent/)
- **Base class** (`base.py`): All agents inherit `Agent` ABC with `run(input: Dict) -> Dict` interface. Input/output must be JSON-serializable.
- **Classification strategy** (`orchestrator.py`):
  - 1️⃣ Always try rule-based first (`RuleClassificationAgent`)
  - 2️⃣ If confidence < 0.5, fallback to LLM (`LLMClassificationAgent`)
  - 3️⃣ LLM failures gracefully degrade (silently skip)
- **Rule engine** (`classification_rule_agent.py`): Keyword-based matching with hardcoded `RULES` dict. High confidence (0.9) if match, else "Other" with 0.1.
- **LLM integration** (`classification_llm_agent.py`): Uses OpenAI GPT-4o-mini with prompt injection. Gracefully skips if `OPENAI_API_KEY` missing.
- **Chat interface** (`chat_agent.py`): System-prompted LLM that ONLY interprets pre-computed insights JSON—no DB access, no calculations. Prevents hallucination.
- **Insights agent** (`insight_agent.py`): Generates structured spending insights for dashboard consumption.
- **Feedback agent** (`feedback_agent.py`): Captures user corrections to improve future classifications.

**Integration point**: `src/classify/run_classification.py` instantiates orchestrator and runs batch classification per row.

### Data Storage (DuckDB)
All persistence via `data/expenses.duckdb`. Tables follow naming: `transactions_*` (raw/clean/final) and `metrics_*` (aggregates).
- **Never** delete `expenses.duckdb`; pipeline appends/overwrites tables
- **Dashboard** (`app/dashboard.py`) reads `transactions_final` and `metrics_*` tables via `@st.cache_data`

## Project Conventions

### LLM Prompting
- **Classification prompt** (`classification_llm_agent.py`): Explicit category list + JSON return format
- **Chat prompt** (`chat_agent.py`): System prompt forbids inventing data; constraints are critical to prevent false advice
- **Temperature settings**: 0 for classification (deterministic), 0.3 for chat (slight flexibility)

### Data Normalization
`clean_transactions.py` applies transformations in order:
- Datetime parsing with error coercion
- String lowercasing/stripping (esp. description, merchant)
- Drop NA in key columns (date, amount, description)
- Deduplication on (date, amount, description) triple
- Add temporal features: month, weekday, year
- Stable transaction IDs based on row index

### Error Handling
- **Pipeline steps**: Fail loudly with `sys.exit(1)` if subprocess returns non-zero
- **LLM calls**: Silently degrade (try/except with `pass`) rather than crash dashboard
- **Agent initialization**: Check for `OPENAI_API_KEY` before creating client; `self.client = None` if missing

## Critical Developer Workflows

### Running the Pipeline
```bash
python run_pipeline.py
```
Executes all 4 steps in sequence. Use this to process raw data after adding CSV to `data/revolut.csv`.

### Starting the Dashboard
```bash
streamlit run app/dashboard.py
```
Interactive Streamlit app. Requires `data/expenses.duckdb` to exist from prior pipeline run.

### Adding New Classification Rules
Edit `RULES` dict in `src/agent/classification_rule_agent.py`. Keywords are case-insensitive, matched via substring. Example:
```python
RULES = {
    "Subscriptions": ["spotify", "netflix", "prime", "icloud"],
    "Transport": ["uber", "bolt", "tram", "metro", "bus", "taxi"],
}
```

### Debugging Classification
- Check `confidence` field in `transactions_final` table to see which method was used (0.9 = rule, 0.X-LLM)
- Use `category_source` column: "rule" vs "llm"
- LLM responses parsed via `eval()` in `classification_llm_agent.py`—dangerous but workable for controlled prompts

## Dependencies & Setup
- **Python**: Streamlit, Pandas, DuckDB, OpenAI, Plotly
- **Environment**: `OPENAI_API_KEY` required for LLM classification (optional if only using rules)
- **Data**: CSV input at `data/revolut.csv`; database created on first ingestion

## Key Files to Reference
- `src/agent/orchestrator.py`: Classification strategy and fallback logic
- `src/classify/run_classification.py`: Batch classification orchestration
- `app/dashboard.py`: Frontend and Streamlit caching patterns
- `src/transform/clean_transactions.py`: Data normalization pipeline
