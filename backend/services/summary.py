"""데이터 요약 계산 — 시스템 프롬프트 주입용."""


def _group_stats(rows: list[dict], key_len: int) -> list[dict]:
    """date 앞 key_len글자(4=연, 7=월)로 묶어 평균·최대·최소와 그 날짜를 낸다.

    rows는 날짜순 정렬돼 있어야 한다.
    """
    groups: dict[str, list[dict]] = {}
    for r in rows:
        groups.setdefault(r["date"][:key_len], []).append(r)
    out = []
    for key, rs in groups.items():
        vals = [float(r["value"]) for r in rs]
        hi = max(rs, key=lambda r: float(r["value"]))
        lo = min(rs, key=lambda r: float(r["value"]))
        out.append(
            {
                "key": key,
                "count": len(rs),
                "average": round(sum(vals) / len(vals)),
                "max": round(float(hi["value"])),
                "max_date": hi["date"],
                "min": round(float(lo["value"])),
                "min_date": lo["date"],
            }
        )
    return out


def build_summary(rows: list[dict]) -> dict:
    """rows: [{date: 'YYYY-MM-DD', value: float, ...}] → 요약 dict."""
    if not rows:
        return {
            "period": None, "count": 0, "metrics": None, "trend": "데이터 없음",
            "yearly": [], "monthly": [],
        }

    rows = sorted(rows, key=lambda r: r["date"])
    values = [float(r["value"]) for r in rows]
    count = len(values)

    # 최대/최소는 날짜까지 넘겨야 한다. 값만 주면 모델이 "언제 최고였냐"는
    # 질문에 기간 끝 날짜를 지어내 답한다.
    max_row = max(rows, key=lambda r: float(r["value"]))
    min_row = min(rows, key=lambda r: float(r["value"]))

    metrics = {
        "total": round(sum(values)),
        "average": round(sum(values) / count),
        "max": round(max(values)),
        "max_date": max_row["date"],
        "min": round(min(values)),
        "min_date": min_row["date"],
    }

    # 최근 30개 평균 vs 그 이전 30개 평균으로 추세 판정 (±3% 이내는 유지)
    if count >= 60:
        recent = sum(values[-30:]) / 30
        prev = sum(values[-60:-30]) / 30
        pct = (recent - prev) / prev * 100
        if pct > 3:
            trend = f"상승 (최근 30일 평균이 직전 30일 대비 +{pct:.1f}%)"
        elif pct < -3:
            trend = f"하락 (최근 30일 평균이 직전 30일 대비 {pct:.1f}%)"
        else:
            trend = f"유지 (최근 30일 평균 변화 {pct:+.1f}%)"
    else:
        trend = "데이터 부족 (추세 판정에 60개 이상 필요)"

    return {
        "period": f"{rows[0]['date']} ~ {rows[-1]['date']}",
        "count": count,
        "metrics": metrics,
        "trend": trend,
        "yearly": _group_stats(rows, 4),
        "monthly": _group_stats(rows, 7),
    }
