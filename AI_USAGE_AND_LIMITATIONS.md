# AI usage, challenges, and limitations

## AI tools used

This project can use an OpenAI-compatible chat completion for structured intent classification when `OPENAI_API_KEY` is configured. During development, a coding assistant may be used to explain code, draft tests, and troubleshoot errors; document the tools actually used by the developer before submission.

## How AI is used at runtime

The model receives the user question and returns one intent from a fixed allowlist, with optional month values for month comparisons. It does not generate SQL or calculate revenue. SQLite performs the calculations, and the UI shows the supporting rows.

## Reliability and safety

- Only known intents are accepted.
- The backend maps intents to predefined analytics functions.
- No arbitrary or destructive SQL is executed.
- SQL parameters are bound separately.
- Unsupported questions receive a clear message.
- If the LLM is unavailable, the application uses a rule-based fallback and reports that method.

## Data quality choices

Rows with invalid required fields, duplicate transaction IDs, quantity <= 0, negative price/discount, or discount exceeding gross value are rejected. Revenue includes only completed transactions and uses quantity × unit price − discount amount. These assumptions should be confirmed against the business's intended accounting rules.

## Known limitations

- Without an API key, intent interpretation uses keyword rules rather than an LLM.
- Month comparison needs recognizable month names and years or `YYYY-MM` values.
- The application supports a predefined set of analytical questions, not unrestricted chat.
- The dataset is small and the application is a challenge prototype, not a production deployment.

## What I would improve with another day

- Isolated test database and stronger integration tests.
- More robust date and intent extraction.
- Additional charts and filtering by category, product, region, and channel.
- Logging, observability, authentication, and deployment configuration.
- More explicit handling for returns/refunds and financial rounding.
