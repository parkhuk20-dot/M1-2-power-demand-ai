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
