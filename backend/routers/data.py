from fastapi import APIRouter, HTTPException

from schemas import DataCreate, DataUpdate
from services.firebase import get_db
from services.summary import build_summary

router = APIRouter(prefix="/api/data", tags=["data"])


def _fetch_all() -> list[dict]:
    docs = get_db().collection("data").stream()
    return [{"id": d.id, **d.to_dict()} for d in docs]


@router.get("/summary")
def data_summary():
    return build_summary(_fetch_all())


@router.get("")
def list_data():
    rows = sorted(_fetch_all(), key=lambda r: r["date"], reverse=True)
    return {"count": len(rows), "items": rows}


@router.post("", status_code=201)
def create_data(body: DataCreate):
    ref = get_db().collection("data").document()
    ref.set(body.model_dump())
    return {"id": ref.id, **body.model_dump()}


@router.put("/{doc_id}")
def update_data(doc_id: str, body: DataUpdate):
    ref = get_db().collection("data").document(doc_id)
    if not ref.get().exists:
        raise HTTPException(404, "데이터가 없습니다")
    changes = {k: v for k, v in body.model_dump().items() if v is not None}
    if not changes:
        raise HTTPException(400, "수정할 필드가 없습니다")
    ref.update(changes)
    return {"id": doc_id, **ref.get().to_dict()}


@router.delete("/{doc_id}")
def delete_data(doc_id: str):
    ref = get_db().collection("data").document(doc_id)
    if not ref.get().exists:
        raise HTTPException(404, "데이터가 없습니다")
    ref.delete()
    return {"id": doc_id, "deleted": True}
