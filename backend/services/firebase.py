import json
import os

import firebase_admin
from firebase_admin import credentials, firestore

_db = None


def get_db():
    """Firestore 클라이언트 (lazy init).

    FIREBASE_SERVICE_ACCOUNT_JSON 환경 변수에 서비스 계정 키의
    JSON 문자열 또는 키 파일 경로를 넣는다.
    """
    global _db
    if _db is None:
        raw = os.environ["FIREBASE_SERVICE_ACCOUNT_JSON"]
        if raw.strip().startswith("{"):
            info = json.loads(raw)
        else:
            with open(raw) as f:
                info = json.load(f)
        if not firebase_admin._apps:
            firebase_admin.initialize_app(credentials.Certificate(info))
        _db = firestore.client()
    return _db


def fetch_data(start: str | None = None, end: str | None = None) -> list[dict]:
    """data 컬렉션 조회. 기간은 양 끝 포함.

    날짜가 YYYY-MM-DD 문자열이라 사전순 비교가 곧 날짜순 비교다.
    기간을 Firestore 쿼리에서 거르므로 좁힐수록 읽기 횟수도 준다.
    """
    q = get_db().collection("data")
    if start:
        q = q.where(filter=firestore.FieldFilter("date", ">=", start))
    if end:
        q = q.where(filter=firestore.FieldFilter("date", "<=", end))
    return [{"id": d.id, **d.to_dict()} for d in q.stream()]
