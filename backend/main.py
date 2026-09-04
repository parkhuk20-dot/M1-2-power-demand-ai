import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

from routers import chat, conversations, data  # noqa: E402

app = FastAPI(
    title="전력수요 AI 비서 API",
    description="일별 전국 전력 최대수요 데이터를 이해하고 답하는 AI 챗봇 백엔드",
    version="1.0.0",
)

origins = [o.strip() for o in os.environ.get("ALLOWED_ORIGINS", "*").split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(data.router)
app.include_router(conversations.router)
app.include_router(chat.router)


@app.get("/")
def root():
    return {"status": "ok", "docs": "/docs"}
