"""seed_data.csv(M1-1 일별 전력수요 최근 180일)를 Firestore data 컬렉션에 업로드.

사용법: .env 설정 후  python seed.py
이미 데이터가 있으면 중복 방지를 위해 중단한다. (--force 로 전체 삭제 후 재시드)
"""
import csv
import sys

from dotenv import load_dotenv

load_dotenv()

from services.firebase import get_db  # noqa: E402


def main():
    db = get_db()
    col = db.collection("data")

    existing = list(col.limit(1).stream())
    if existing and "--force" not in sys.argv:
        print("data 컬렉션에 이미 데이터가 있습니다. 재시드하려면: python seed.py --force")
        return
    if existing:
        for d in col.stream():
            d.reference.delete()
        print("기존 데이터 삭제 완료")

    with open("seed_data.csv") as f:
        rows = list(csv.DictReader(f))

    # Firestore batch는 한 번에 최대 500건까지만 커밋할 수 있다
    for i in range(0, len(rows), 500):
        batch = db.batch()
        for r in rows[i : i + 500]:
            batch.set(col.document(), {"date": r["date"], "value": float(r["value"]), "memo": r["memo"]})
        batch.commit()
    print(f"{len(rows)}개 업로드 완료 ({rows[0]['date']} ~ {rows[-1]['date']})")


if __name__ == "__main__":
    main()
