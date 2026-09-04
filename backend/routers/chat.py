from firebase_admin import firestore
from fastapi import APIRouter, HTTPException

from schemas import ChatRequest
from services import ai
from services.firebase import get_db
from services.summary import build_summary

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("")
def chat(body: ChatRequest):
    """흐름: 데이터 요약 → 시스템 프롬프트 주입 → GPT 호출 → 대화 자동 저장."""
    db = get_db()

    rows = [d.to_dict() for d in db.collection("data").stream()]
    summary = build_summary(rows)

    history = []
    conv_ref = None
    if body.conversation_id:
        conv_ref = db.collection("conversations").document(body.conversation_id)
        snap = conv_ref.get()
        if not snap.exists:
            raise HTTPException(404, "대화가 없습니다")
        history = snap.to_dict().get("messages", [])

    try:
        reply = ai.ask(summary, history, body.message)
    except Exception as e:
        raise HTTPException(502, f"AI 호출 실패: {e}")

    new_messages = history + [
        {"role": "user", "content": body.message},
        {"role": "assistant", "content": reply},
    ]
    if conv_ref is None:
        conv_ref = db.collection("conversations").document()
        conv_ref.set(
            {
                "title": body.message[:30],
                "messages": new_messages,
                "updated_at": firestore.SERVER_TIMESTAMP,
            }
        )
    else:
        conv_ref.update(
            {"messages": new_messages, "updated_at": firestore.SERVER_TIMESTAMP}
        )

    return {"reply": reply, "conversation_id": conv_ref.id, "summary": summary}
