"""python test_summary.py — build_summary 로직 자가 검증."""
from services.summary import build_summary


def run():
    assert build_summary([])["count"] == 0

    # 60개: 앞 30개 평균 100, 뒤 30개 평균 120 → 상승
    rows = [{"date": f"2025-01-{i+1:02d}", "value": 100} for i in range(30)]
    rows += [{"date": f"2025-02-{i+1:02d}", "value": 120} for i in range(28)]
    rows += [{"date": f"2025-03-{i+1:02d}", "value": 120} for i in range(2)]
    s = build_summary(rows)
    assert s["count"] == 60
    assert s["period"] == "2025-01-01 ~ 2025-03-02"
    assert s["metrics"]["max"] == 120 and s["metrics"]["min"] == 100
    assert s["trend"].startswith("상승"), s["trend"]

    # 최대/최소 날짜: 기간 끝이 아니라 실제 발생일이어야 한다
    spike = [
        {"date": "2025-01-01", "value": 50},
        {"date": "2025-01-02", "value": 900},  # 최대는 중간에
        {"date": "2025-01-03", "value": 70},
    ]
    sm = build_summary(spike)["metrics"]
    assert sm["max_date"] == "2025-01-02", sm
    assert sm["min_date"] == "2025-01-01", sm

    # 정렬 무관해야 함
    assert build_summary(list(reversed(rows)))["trend"] == s["trend"]

    # 60개 미만 → 추세 판정 불가
    assert "부족" in build_summary(rows[:10])["trend"]

    # 연도별·월별 집계: 입력 순서와 무관하게 그룹·날짜순으로 나와야 한다
    mixed = [
        {"date": "2025-02-01", "value": 30},
        {"date": "2024-12-31", "value": 10},
        {"date": "2025-01-15", "value": 50},
        {"date": "2025-01-02", "value": 20},
    ]
    agg = build_summary(mixed)
    assert [y["key"] for y in agg["yearly"]] == ["2024", "2025"]
    y25 = agg["yearly"][1]
    assert y25["count"] == 3 and y25["average"] == 33, y25
    assert y25["max_date"] == "2025-01-15" and y25["min_date"] == "2025-01-02"
    assert [m["key"] for m in agg["monthly"]] == ["2024-12", "2025-01", "2025-02"]
    jan = agg["monthly"][1]
    assert jan["count"] == 2 and jan["average"] == 35 and jan["max"] == 50, jan
    assert build_summary([])["monthly"] == []

    print("test_summary: OK")


if __name__ == "__main__":
    run()
