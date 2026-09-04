from firebase_admin import firestore
from fastapi import APIRouter, HTTPException

from schemas import ConversationCreate
from services.firebase import get_db

router = APIRouter(prefix="/api/conversations", tags=["conversations"])


@router.post("", status_code=201)
def create_conversation(body: ConversationCreate):
    ref = get_db().collection("conversations").document()
    ref.set(
        {
            "title": body.title,
            "messages": [m.model_dump() for m in body.messages],
            "updated_at": firestore.SERVER_TIMESTAMP,
        }
    )
    return {"id": ref.id}


@router.get("")
def list_conversations():
    """목록 조회 — messages는 제외하고 메타데이터만 반환한다."""
    docs = (
        get_db()
        .collection("conversations")
        .order_by("updated_at", direction=firestore.Query.DESCENDING)
        .stream()
    )
    items = []
    for d in docs:
        data = d.to_dict()
        items.append(
            {
                "id": d.id,
                "title": data.get("title", "(제목 없음)"),
                "message_count": len(data.get("messages", [])),
                "updated_at": str(data.get("updated_at", "")),
            }
        )
    return {"count": len(items), "items": items}


@router.get("/{doc_id}")
def get_conversation(doc_id: str):
    """대화 불러오기 — 전체 messages 포함."""
    snap = get_db().collection("conversations").document(doc_id).get()
    if not snap.exists:
        raise HTTPException(404, "대화가 없습니다")
    data = snap.to_dict()
    data["updated_at"] = str(data.get("updated_at", ""))
    return {"id": snap.id, **data}


@router.delete("/{doc_id}")
def delete_conversation(doc_id: str):
    ref = get_db().collection("conversations").document(doc_id)
    if not ref.get().exists:
        raise HTTPException(404, "대화가 없습니다")
    ref.delete()
    return {"id": doc_id, "deleted": True}
