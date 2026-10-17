"""Pydantic 요청 검증 모델.

라우터로 들어오는 모든 입력의 형식·범위·길이를 여기서 1차로 걸러낸다.
검증 실패는 FastAPI가 422로 응답한다.
"""
import math
import re
from datetime import date as date_type

from pydantic import BaseModel, Field, field_validator, model_validator

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
MAX_MEMO_LEN = 200
MAX_MESSAGE_LEN = 2000
MAX_TITLE_LEN = 100
MAX_MESSAGES_PER_SAVE = 500


def _check_date(v: str) -> str:
    """YYYY-MM-DD 형식 + 실제 존재하는 날짜만 허용."""
    if not DATE_RE.match(v):
        raise ValueError("날짜는 YYYY-MM-DD 형식이어야 합니다")
    date_type.fromisoformat(v)  # 존재하지 않는 날짜(2/30 등)는 여기서 ValueError
    return v


def _check_finite_nonneg(v: float) -> float:
    if not math.isfinite(v):
        raise ValueError("유한한 숫자만 허용됩니다")
    # 도메인 정의: 전력수요(시간당 MWh)는 음수가 될 수 없다
    if v < 0:
        raise ValueError("전력수요 값은 0 이상이어야 합니다")
    return v


class Period(BaseModel):
    """차트·요약·AI 컨텍스트에 공통으로 쓰는 선택 기간 (inclusive)."""

    start: str | None = None
    end: str | None = None

    @field_validator("start", "end")
    @classmethod
    def valid(cls, v: str | None) -> str | None:
        return _check_date(v) if v else None

    @model_validator(mode="after")
    def ordered(self):
        if self.start and self.end and self.start > self.end:
            raise ValueError("시작일이 종료일보다 늦습니다")
        return self


class DataCreate(BaseModel):
    date: str = Field(..., description="YYYY-MM-DD")
    value: float
    memo: str = Field(default="", max_length=MAX_MEMO_LEN)

    @field_validator("date")
    @classmethod
    def valid_date(cls, v: str) -> str:
        return _check_date(v)

    @field_validator("value")
    @classmethod
    def valid_value(cls, v: float) -> float:
        return _check_finite_nonneg(v)

    @field_validator("memo")
    @classmethod
    def strip_memo(cls, v: str) -> str:
        return v.strip()


class DataUpdate(BaseModel):
    """부분 수정용. 세 필드 모두 None이면 라우터에서 400."""

    date: str | None = None
    value: float | None = None
    memo: str | None = Field(default=None, max_length=MAX_MEMO_LEN)

    @field_validator("date")
    @classmethod
    def valid_date(cls, v: str | None) -> str | None:
        return _check_date(v) if v is not None else v

    @field_validator("value")
    @classmethod
    def valid_value(cls, v: float | None) -> float | None:
        return _check_finite_nonneg(v) if v is not None else v

    @field_validator("memo")
    @classmethod
    def strip_memo(cls, v: str | None) -> str | None:
        return v.strip() if v is not None else v


class Message(BaseModel):
    role: str = Field(..., pattern="^(user|assistant)$")
    content: str = Field(..., min_length=1, max_length=MAX_MESSAGE_LEN * 10)


class ConversationCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=MAX_TITLE_LEN)
    messages: list[Message] = Field(..., max_length=MAX_MESSAGES_PER_SAVE)

    @field_validator("title")
    @classmethod
    def strip_title(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("제목이 비어 있습니다")
        return v


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=MAX_MESSAGE_LEN)
    conversation_id: str | None = Field(default=None, max_length=100)
    period: Period | None = None
    # 재시도 중복 저장 방지용 클라이언트 생성 ID (같은 ID면 같은 요청으로 간주)
    client_msg_id: str | None = Field(default=None, max_length=64)

    @field_validator("message")
    @classmethod
    def not_blank(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("질문이 비어 있습니다")
        return v
