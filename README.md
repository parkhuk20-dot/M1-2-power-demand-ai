# ⚡ 전력수요 AI 비서 — 내 데이터를 아는 AI 챗봇

일반 챗봇은 "요즘 전력수요 어때?"라고 물으면 일반론만 답한다.
이 서비스는 **일별 전국 전력 최대수요(피크) 데이터 2년치(731일)**를 Firestore에 저장하고,
그 요약을 시스템 프롬프트에 주입(컨텍스트 주입)해 **내 데이터 기반의 맞춤형 답변**을 제공한다.

데이터는 [M1-1 전력수요 시계열 분석](../M1-1)에서 정제한
한국전력거래소 일별 최대수요(2024-01-01 ~ 2025-12-31, 731개)를 사용했다.

## 기술 스택

| 구분 | 기술 |
|---|---|
| 백엔드 | Python 3.10+, FastAPI, Pydantic, Uvicorn |
| DB | Firebase Firestore (`data`, `conversations` 컬렉션) |
| AI | GPT (`gpt-5-mini`, 코디세이 OpenAI 호환 API 경유, 시스템 프롬프트 컨텍스트 주입) |
| 프론트엔드 | HTML / CSS / Vanilla JavaScript |
| 배포 | 백엔드 Render, 프론트엔드 Vercel |

## 배포 URL

- 프론트엔드: https://m1-2-power-demand-ai.vercel.app
- 백엔드 API: https://m1-2-power-demand-api.onrender.com
- Swagger UI: https://m1-2-power-demand-api.onrender.com/docs

⏱ 백엔드가 Render 무료 티어라 15분 미사용 시 슬립된다. **첫 요청은 최대 1분가량 걸릴 수 있다**
(프론트 상단에 동일 안내 문구 표시).

## API 목록

| 메서드 | 경로 | 설명 |
|---|---|---|
| POST | /api/data | 데이터 추가 (date, value, memo) |
| GET | /api/data | 데이터 목록 조회 |
| PUT | /api/data/{id} | 데이터 수정 |
| DELETE | /api/data/{id} | 데이터 삭제 |
| GET | /api/data/summary | 요약(기간·개수·평균·최대·최소·추세) — 프롬프트 주입용 |
| POST | /api/chat | AI 대화 (요약 주입 → GPT 호출 → 대화 자동 저장) |
| POST | /api/conversations | 대화 저장 |
| GET | /api/conversations | 대화 목록 (메타데이터만) |
| GET | /api/conversations/{id} | 특정 대화 전체 messages 조회 (불러오기용) |
| DELETE | /api/conversations/{id} | 대화 삭제 |

## 로컬 실행

```bash
# 1. 백엔드
cd backend
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

cp ../.env.example .env        # 값 채우기 (아래 환경 변수 참고)
python seed.py                 # 시드 데이터 731개 업로드 (최초 1회)
python test_summary.py         # 요약 로직 자가 검증
uvicorn main:app --reload      # http://localhost:8000/docs

# 2. 프론트엔드 (다른 터미널)
cd frontend
python3 -m http.server 3000    # http://localhost:3000
```

## 환경 변수

| 변수 | 설명 |
|---|---|
| `OPENAI_API_KEY` | OpenAI 호환 API 키 (코디세이 API 콘솔에서 발급) |
| `OPENAI_BASE_URL` | OpenAI 호환 서버 주소. 공식 OpenAI면 생략, 코디세이는 `https://copa.codyssey.kr/v1` |
| `FIREBASE_SERVICE_ACCOUNT_JSON` | 서비스 계정 키 **JSON 문자열 전체** 또는 키 파일 경로 |
| `ALLOWED_ORIGINS` | CORS 허용 도메인, 콤마 구분 (예: `https://xxx.vercel.app`) |
| `OPENAI_MODEL` | 사용할 모델 ID. 배포는 `gpt-5-mini` (미지정 시 `gpt-4o-mini`) |
| `API_BASE_URL` | (Vercel 전용) 프론트가 호출할 백엔드 주소 |

키는 모두 환경 변수로만 관리하며 코드/저장소에 넣지 않는다 (`.gitignore` 처리).

## 배포 방법

### 백엔드 — Render

1. GitHub에 푸시 후 Render에서 **New → Web Service**, 저장소 연결
2. Root Directory `backend`, Build `pip install -r requirements.txt`,
   Start `uvicorn main:app --host 0.0.0.0 --port $PORT`
3. 비밀 값 2개 입력: `OPENAI_API_KEY`, `FIREBASE_SERVICE_ACCOUNT_JSON`(키 파일 내용 통째로 붙여넣기).
   `OPENAI_BASE_URL`·`OPENAI_MODEL`·`ALLOWED_ORIGINS`는 `render.yaml`에 이미 들어 있다
4. 배포 후 `/docs` 접속 확인

### 프론트엔드 — Vercel

1. Vercel에서 저장소 연결, Root Directory `frontend`
2. 환경 변수 `API_BASE_URL` = Render 백엔드 주소 등록
   (`vercel.json`의 buildCommand가 빌드 시 `config.js`에 주입한다)

## 컨텍스트 주입 동작 흐름

```
사용자 질문 → GET data 컬렉션 → build_summary() (기간/개수/통계/추세)
  → 요약을 시스템 프롬프트 템플릿에 삽입 → GPT 호출
  → 질문+답변을 conversations에 자동 저장 → 답변 반환
```

## 제출 스크린샷

> 배포 후 캡처해서 채운다.

1. 데이터 요약이 보이는 채팅 화면 (질문+답변 포함)
2. 데이터 관리 화면 (추가/삭제 동작)
3. 대화 기록 화면 (불러오기 동작)

## 폴더 구조

```
M1-2/
├── backend/
│   ├── main.py               앱 초기화 · CORS · 라우터 등록
│   ├── schemas.py            Pydantic 요청 검증 모델
│   ├── routers/              엔드포인트 (data / conversations / chat)
│   ├── services/             비즈니스 로직 (firebase / summary / ai)
│   ├── seed.py               시드 데이터 업로드 스크립트
│   ├── seed_data.csv         M1-1에서 추출한 2년치(731일) 데이터
│   ├── test_summary.py       요약 로직 자가 검증
│   └── requirements.txt
├── frontend/
│   ├── index.html / style.css / app.js
│   ├── config.js             API 주소 (Vercel 빌드 시 env로 덮어씀)
│   └── vercel.json
├── .env.example
└── README.md
```
