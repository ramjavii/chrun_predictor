import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api import events, explain, models, predict, train
from src.core.errors import IDSException, ids_exception_handler, unhandled_exception_handler
from src.core.logging import configure_logging

configure_logging()
logger = logging.getLogger(__name__)

app = FastAPI(
    title="IDS — Churn Predictor",
    description="From prediction to retention: a customer churn intelligence API",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_exception_handler(IDSException, ids_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)

app.include_router(events.router)
app.include_router(predict.router)
app.include_router(explain.router)
app.include_router(models.router)
app.include_router(train.router)


@app.get("/health")
async def health():
    return {"status": "ok"}
