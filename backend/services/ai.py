import os

from openai import OpenAI

SYSTEM_TEMPLATE = """당신은 전력수요 데이터 분석 비서입니다.

[사용자 데이터 요약]
- 데이터: 일별 전국 전력 최대수요(피크, MWh)
- 데이터 기간: {period}
- 총 레코드: {count}개
- 주요 지표: 평균 {average} MWh
  · 최대 {max} MWh ({max_date})
  · 최소 {min} MWh ({min_date})
- 최근 트렌드: {trend}

위 데이터를 기반으로 한국어로 간결하고 구체적인 맞춤형 답변을 제공하세요.
데이터에 없는 내용은 추측하지 말고 없다고 말하세요."""


def system_prompt(summary: dict) -> str:
    m = summary.get("metrics") or {}
    return SYSTEM_TEMPLATE.format(
        period=summary.get("period") or "없음",
        count=summary.get("count", 0),
        average=f"{m.get('average', 0):,}",
        max=f"{m.get('max', 0):,}",
        max_date=m.get("max_date", "날짜 미상"),
        min=f"{m.get('min', 0):,}",
        min_date=m.get("min_date", "날짜 미상"),
        trend=summary.get("trend", "알 수 없음"),
    )


def ask(summary: dict, history: list[dict], user_message: str) -> str:
    """요약을 시스템 프롬프트에 주입해 GPT 호출. history: [{role, content}]."""
    client = OpenAI()  # OPENAI_API_KEY 환경 변수 사용
    messages = [{"role": "system", "content": system_prompt(summary)}]
    messages += [{"role": m["role"], "content": m["content"]} for m in history[-10:]]
    messages.append({"role": "user", "content": user_message})
    resp = client.chat.completions.create(
        model=os.environ.get("OPENAI_MODEL", "gpt-4o-mini"),
        messages=messages,
        max_tokens=500,  # 과금 방지 상한
        temperature=0.7,
    )
    return resp.choices[0].message.content
