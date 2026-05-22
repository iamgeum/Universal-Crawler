# Universal Crawler — 개발 컨텍스트

> 새 세션 시작 시 이 파일과 `universal_crawler_plan.md` 를 함께 첨부할 것.
> "두 파일 읽고 이어서 작업해줘" 한 마디로 컨텍스트 복구 가능.

---

## 현재 상태 (매 세션 종료 시 업데이트)

```
마지막 작업일: 2026-05-22
현재 Phase: 1c 완료 → 2a 시작 전
완료된 파일: engines/ytdlp_engine.py, engines/gallery_engine.py, core/browser_pool.py,
  core/runner.py (fallback/상태전이), tests/integration/test_fallback.py
다음 작업: Phase 2a — LLMBrain, planner, ollama, Dual-key Routing
```

---

## 프로젝트 핵심 결정사항 요약

> 상세 근거는 universal_crawler_plan.md 참고. 여기는 빠른 복기용.

| 항목 | 결정 |
|---|---|
| Python 버전 | 3.11+ |
| LLM 구조 | 대→소. 대형모델 전략 생성, 소형모델 실행 |
| 기본 뇌 | Ollama llama3.2 (무료 로컬). 클라우드는 에러 복구만 |
| 엔진 라우팅 | Phase 1: URL 패턴, Phase 2a: Dual-key (URL+Capability) |
| 출력 표준 | 모든 엔진 `execute()` → `CrawlResult` 반환 |
| partial_success | mandatory_fields 기반 전이. bool config 아님 |
| 보안 | CrawlEvent payload 재귀 마스킹 (중첩 dict + 쿼리스트링) |
| 브라우저 | MAX_CONTEXTS=5 Hard Limit, cleanup_zombies() 필수 |
| API 키 | .env 전용. config.py 하드코딩 절대 금지 |

---

## 폴더 구조 (목표)

```
universal-crawler/
├── .env                       ← API 키 (gitignore)
├── .gitignore
├── requirements.txt
├── crawler.py                 ← CLI 진입점
├── config.py                  ← 설정 (API 키는 .env에서 로드)
├── DEV_CONTEXT.md             ← 이 파일 (세션 컨텍스트 유지용)
├── universal_crawler_plan.md  ← 설계 문서 (LLM 공동 검토 이력)
├── core/
│   ├── brain.py               ← LLMBrain ABC
│   ├── brain_factory.py
│   ├── brains/
│   │   ├── claude.py
│   │   ├── openai.py
│   │   ├── gemini.py
│   │   ├── ollama.py
│   │   └── heuristic.py      ← AI 없는 URL 패턴 기반 (기본값)
│   ├── plugin.py              ← EnginePlugin ABC
│   ├── schema.py              ← 모든 Pydantic 모델
│   ├── persona.py
│   ├── policy.py
│   ├── planner.py
│   ├── classifier.py
│   ├── router.py
│   ├── browser_pool.py
│   ├── storage.py
│   ├── logger.py
│   └── telemetry.py
├── engines/
│   ├── scrapling_engine.py
│   ├── patchright_engine.py
│   ├── ytdlp_engine.py
│   └── gallery_engine.py
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── smoke/
│   └── regression/
├── output/                    ← (gitignore)
│   ├── text/
│   ├── images/
│   └── videos/
└── db/                        ← (gitignore)
    └── crawl_history.db
```

---

## 핵심 스키마 요약

> schema.py에 들어갈 것들. 상세 코드는 계획서 참고.

```python
# 전부 schema.py 한 파일에
CrawlEvent      # Event Log용. payload 재귀 마스킹 포함
CrawlStrategy   # Planner 출력. mandatory_fields 포함
CrawlResult     # 엔진 출력 표준. 모든 execute() 이걸 반환
JobState        # Enum: QUEUED/RUNNING/WAITING_RETRY/FALLBACK/
                #       PARTIAL_SUCCESS/MANUAL_REVIEW/COMPLETED/FAILED
RetryPolicy     # CrawlStrategy 내부
```

---

## Phase 체크리스트

### Phase 1a — 골격 ✅
- [x] 폴더 구조 생성
- [x] `config.py` (DEFAULT_FALLBACK_ENGINE, BRAIN_CONFIG 등)
- [x] `schema.py` (CrawlStrategy, CrawlJob, JobState, CrawlEvent, CrawlResult)
- [x] SQLite 초기화 (crawl_jobs, crawl_events, selector_memory, telemetry)
- [x] `crawler.py` CLI 기본 구조 (`init-db`, `status`, `enqueue`)
- [x] `requirements.txt`

### Phase 1b — 단일 엔진 ✅
- [x] `policy.py` — robots.txt, blacklist/whitelist
- [x] `engines/scrapling_engine.py` — execute() → CrawlResult (scrapling + urllib fallback)
- [x] `brains/heuristic.py` — 도메인 → 엔진 매핑, enqueue 라우팅
- [x] `logger.py` + `telemetry.py` 기본
- [x] `core/runner.py` — run_job, storage try/except
- [x] CLI: `enqueue`, `run`, `crawl` (engine 하드코딩 제거)
- [x] tests: unit (policy/heuristic/scrapling/runner) + smoke/test_scrapling.py

### Phase 1c — 멀티 엔진 ✅
- [x] `engines/ytdlp_engine.py` — 메타 추출 (skip_download)
- [x] `engines/gallery_engine.py` — gallery-dl -g URL 수집
- [x] fallback + CrawlJob 상태 전이 (FAILED→WAITING_RETRY→FALLBACK)
- [x] `browser_pool.py` 인터페이스 (MAX_CONTEXTS=5, cleanup_zombies)
- [x] `tests/integration/test_fallback.py` + unit 테스트

### Phase 2a — LLM + Planner ← 현재 여기
- [ ] `core/brain.py` ABC
- [ ] `brain_factory.py`
- [ ] `persona.py` 버전 관리
- [ ] `planner.py`
- [ ] `brains/ollama.py`
- [ ] router → Dual-key Routing 전환

### Phase 2b — Stealth + 클라우드
- [ ] `engines/patchright_engine.py` + Browser Pool 구현
- [ ] `brains/claude.py`, `openai.py`, `gemini.py`
- [ ] 대→소 캐스케이드
- [ ] `tests/regression/`

### Phase 3 — AI 고도화
- [ ] API Detection (XHR/GraphQL)
- [ ] Selector Memory 활성화
- [ ] 페르소나 v2 A/B 비교

### Phase 4 — 스케일
- [ ] Job Queue, 병렬 처리
- [ ] 스케줄링
- [ ] 대시보드 UI
- [ ] Tor/VPN 로테이션
- [ ] "크롤러 vs 에이전트" 방향 결정

---

## 세션 시작 프롬프트 템플릿

```
universal_crawler_plan.md, DEV_CONTEXT.md 두 파일 첨부

DEV_CONTEXT.md의 현재 상태 확인하고
[여기에 작업 내용 입력]
```

### 예시
```
# Phase 1a 시작할 때
"두 파일 읽고 Phase 1a 구현 시작해줘"

# 이어서 할 때
"두 파일 읽고 Phase 1b 이어서 해줘. scrapling_engine.py부터"

# 막혔을 때
"두 파일 읽고 [에러 내용] 해결해줘"

# 계획 수정할 때
"두 파일 읽고 [변경사항] 반영해서 계획서 업데이트해줘"
```

---

## Git 커밋 컨벤션

```bash
feat: Phase 1a — 골격, schema, SQLite 초기화
feat: Phase 1b — scrapling 엔진, policy, heuristic 라우터
feat: Phase 1c — yt-dlp/gallery-dl, fallback, 상태머신
feat: Phase 2a — LLMBrain, planner, ollama 어댑터
feat: Phase 2b — patchright, browser pool, 클라우드 LLM
fix: [버그 설명]
refactor: [리팩터링 내용]
docs: 계획서/컨텍스트 문서 업데이트
```

---

## 환경 설정

```bash
# 의존성 설치
pip install -r requirements.txt

# .env 파일 (직접 작성, gitignore)
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
GEMINI_API_KEY=...
OLLAMA_HOST=http://localhost:11434

# Ollama 로컬 모델 설치
ollama pull llama3.2
```

---

## .gitignore 필수 항목

```
# Python
__pycache__/
*.pyc
*.pyo
.venv/
venv/

# 프로젝트 전용
.env
config.local.py
output/
db/*.db

# OS
.DS_Store
Thumbs.db
```

---

*이 파일은 세션 종료 시 "현재 상태" 섹션을 업데이트하고 커밋할 것*
*`docs: DEV_CONTEXT 업데이트 — Phase XX 완료`*
