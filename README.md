# AI Business Intelligence Assistant

A small full-stack application for asking natural-language questions about sales transactions. The AI layer classifies a question into an allowed analytics intent; predefined SQLite queries calculate the answer. The model never generates SQL, which keeps database access constrained and results reproducible.

## Features

- Import and clean the supplied sales CSV with Pandas.
- SQLite database storage.
- Total revenue, highest-revenue product, highest-sales region, monthly trend, month comparison, category revenue, and sales-channel revenue.
- Optional OpenAI LLM intent classification with structured output.
- Rule-based fallback when no API key is configured or the LLM call fails.
- React UI with example questions, summary metrics, tables, and a monthly revenue bar chart.
- API validation, unsupported-question handling, and automated tests.

## Architecture

`CSV → Pandas validation/cleaning → SQLite → FastAPI → question interpreter → allowlisted analytics function → SQLite query → JSON response → React UI`

The LLM only returns an allowlisted intent and optional month values. All numerical results are calculated by parameterized, predefined SQL queries. No model-generated SQL is executed.

## Data and revenue assumptions

- Revenue is calculated as `quantity * unit_price - discount_amount`.
- The discount amount is treated as a transaction-level discount, not a per-unit discount.
- Only rows with `Status = Completed` are included in revenue calculations.
- Rows with missing required values, invalid dates, duplicate transaction IDs, nonpositive quantity, negative price/discount, or discount greater than gross line value are rejected by the importer.
- Returned transactions can remain in the database for traceability, but they are excluded from completed-sales revenue.
- The original `data/sales.csv` is preserved. Import output prints loaded and rejected row counts.

These are explicit implementation assumptions for this challenge; change them if the business defines discounts, returns, or invalid records differently.

## Requirements

- Python 3.10+
- Node.js 18+
- npm
- Optional OpenAI API key for LLM-based intent interpretation

## Setup on Windows (VS Code)

### 1. Backend

Open a terminal in the project root:

```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python import_data.py
```

If PowerShell blocks activation, use Command Prompt and run `venv\Scripts\activate.bat`, or invoke `venv\Scripts\python.exe` directly.

Optional LLM setup:

```powershell
Copy-Item .env.example .env
```

Edit `backend/.env` and set `OPENAI_API_KEY=your_key_here`. Keep `.env` private and do not commit it. Without a key, the app uses its deterministic rule-based question interpreter. The app remains functional, but this fallback is not a substitute for demonstrating actual LLM integration if the evaluator requires it.

Start the API:

```powershell
uvicorn main:app --reload
```

API docs: http://127.0.0.1:8000/docs
Health check: http://127.0.0.1:8000/health

The API automatically imports the supplied CSV on first startup if the database is empty. You can rerun `python import_data.py` to reload the source CSV.

### 2. Frontend

Open a second terminal from the project root:

```powershell
cd frontend
npm install
npm run dev
```

Open the URL printed by Vite, usually http://localhost:5173.

If the backend runs at a different URL, create `frontend/.env` with `VITE_API_URL=http://127.0.0.1:8000` and restart Vite.

### 3. Tests

In a backend terminal with dependencies installed:

```powershell
pytest -v
```

The test suite uses the challenge database and verifies the key API flows. For a production project, configure an isolated temporary database per test run.

## Example questions

- What is the total revenue?
- Which product generated the highest revenue?
- Show the monthly revenue trend.
- Which region generated the highest sales?
- Compare revenue between January 2026 and February 2026.
- Show revenue by category.
- Compare online and retail sales channels.

Month comparisons currently expect two named months with a year, or two `YYYY-MM` values.

## API example

`POST /ask`

```json
{
  "question": "Which product generated the highest revenue?"
}
```

The response includes `success`, `intent`, `interpretation_method`, `answer`, and `data` fields.

## AI usage and safety

- LLM purpose: map varied natural-language questions to a constrained intent schema.
- Safety: intent is validated against an allowlist; user text is never executed as SQL; query values are parameterized; all SQL operations are predefined read-only `SELECT` queries.
- Reliability: unsupported questions receive a clear message; if the LLM call fails, the system falls back to a rule-based interpreter and labels the method in the response.
- Limitations: the rule-based fallback understands only common phrasings; month parsing is intentionally limited; results depend on the stated data-cleaning and revenue assumptions.

## Debugging notes / improvements

Check `/health` first, then test the API in `/docs`, and finally test the React UI. If results look incorrect, verify the loaded row count, data-cleaning report, discount assumption, transaction status, and SQL result. Potential next improvements include isolated test databases, better month parsing, charts by category/region, pagination, authentication, logging, and broader natural-language tests.

## Repository submission checklist

- [ ] Verify the complete application runs locally.
- [ ] Add screenshots of the UI to the repository if useful.
- [ ] Keep `.env`, API keys, `venv`, `node_modules`, and generated database files out of Git.
- [ ] Confirm the actual LLM path works if claiming LLM integration.
- [ ] Be prepared to explain the data-cleaning rules and revenue formula.
