from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from database import initialize_database, get_connection
from import_data import import_sales
from ai_interpreter import interpret_question
import analytics


@asynccontextmanager
async def lifespan(app: FastAPI):
    initialize_database()
    with get_connection() as conn:
        count = conn.execute("SELECT COUNT(*) FROM sales").fetchone()[0]
    if count == 0:
        import_sales()
    yield


app = FastAPI(
    title="AI Business Intelligence Assistant",
    description="Ask natural-language questions about sales data. AI classifies the request; SQLite computes the answer.",
    version="1.0.0",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


class QuestionRequest(BaseModel):
    question: str = Field(min_length=3, max_length=500)


@app.get("/")
def home():
    return {"message": "AI Business Intelligence Assistant is running", "docs": "/docs"}


@app.get("/health")
def health():
    with get_connection() as conn:
        count = conn.execute("SELECT COUNT(*) FROM sales").fetchone()[0]
    return {"status": "ok", "rows_loaded": count}


@app.get("/summary")
def summary():
    with get_connection() as conn:
        row_count = conn.execute("SELECT COUNT(*) FROM sales").fetchone()[0]
        valid_completed = conn.execute("SELECT COUNT(*) FROM sales WHERE UPPER(status)='COMPLETED'").fetchone()[0]
    return {"rows_loaded": row_count, "completed_transactions": valid_completed, "total_revenue": analytics.total_revenue()["data"][0]["revenue"]}


@app.post("/ask")
def ask_question(request: QuestionRequest):
    question = request.question.strip()
    if len(question) < 3:
        raise HTTPException(status_code=422, detail="Please enter a question with at least 3 characters.")
    interpretation = interpret_question(question)
    intent = interpretation.get("intent")
    operations = {
        "total_revenue": analytics.total_revenue,
        "highest_revenue_product": analytics.highest_revenue_product,
        "monthly_revenue": analytics.monthly_revenue,
        "highest_sales_region": analytics.highest_sales_region,
        "category_revenue": analytics.category_revenue,
        "channel_revenue": analytics.channel_revenue,
    }
    if intent == "compare_months":
        month_a, month_b = interpretation.get("month_a"), interpretation.get("month_b")
        if not month_a or not month_b:
            return {"success": False, "question": question, "answer": "Please name two months, for example: Compare revenue between January 2026 and February 2026.", "data": [], "intent": intent, "interpretation_method": interpretation.get("method")}
        result = analytics.compare_months(month_a, month_b)
    elif intent in operations:
        result = operations[intent]()
    else:
        return {
            "success": False,
            "question": question,
            "answer": "I can't answer that yet. Try asking about total revenue, the top product, the top region, monthly trends, category revenue, sales channels, or a comparison between two named months.",
            "data": [],
            "intent": "unsupported",
            "interpretation_method": interpretation.get("method"),
        }
    return {
        "success": True,
        "question": question,
        "intent": intent,
        "interpretation_method": interpretation.get("method"),
        "answer": result["answer"],
        "data": result["data"],
        "metric": result.get("metric", "revenue"),
    }
