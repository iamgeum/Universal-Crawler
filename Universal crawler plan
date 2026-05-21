# Universal Crawler — 프로젝트 계획서

> 목표: 다양한 웹사이트의 텍스트 / 이미지 / 동영상을 가능한 범위 내에서 자동 수집하며,
> 사이트 구조 변화와 접근 제한에 적응할 수 있도록 설계된 범용 크롤링 프레임워크

---

## MD 작성 규칙 (필독 — 모든 LLM 공통)

> 이 문서를 받아 편집하는 모든 LLM은 아래 규칙을 반드시 준수할 것.
> 규칙을 어기면 다음 검토자가 이전 결정을 복구하는 데 시간을 낭비하게 된다.

### 절대 금지
- **이전 버전 내용 삭제 금지.** 변경이력, 결정 근거, 이전 섹션을 날리면 안 된다.
- **자기 의견 섹션만 남기고 나머지 날리는 것 금지.** (GPT v2.5에서 위반)
- **문서를 중간에서 자르는 것 금지.** 전체 내용을 보존하고 자기 섹션을 추가해야 한다. (Gemini v2.5.1에서 위반)
- **버전 번호 자의적 변경 금지.** 아래 버전 관리 규칙을 따를 것.
- **자기 차례가 아닌 버전 번호 사용 금지.** (GPT가 Gemini 차례인 v2.6.1 건너뛰고 v2.7 예측 작성한 사례)

### 편집 절차
1. 이전 버전 전체 내용을 그대로 유지한다.
2. `변경 이력` 테이블에 자기 버전 한 줄을 추가한다.
3. `버전별 결정 근거`에 이번 버전의 판단 이유를 추가한다.
4. `현재 버전` 표기를 업데이트한다.
5. 자기 검토 내용을 별도 섹션으로 추가한다. (기존 섹션 수정 금지)
6. `현재 해결된 판단` 테이블에 이번에 결정된 항목을 추가한다.
7. `Claude 제안` 섹션은 Claude만 수정한다. GPT/Gemini는 건드리지 않는다.

### 섹션 소유권
| 섹션 | 편집 가능 주체 |
|---|---|
| MD 작성 규칙 | Claude만 수정 가능 |
| 버전 관리 규칙 | Claude만 수정 가능 |
| 변경 이력 | 자기 버전 행만 추가 |
| 핵심 설계 원칙 | Claude만 수정 가능 (GPT/Gemini는 제안만) |
| Claude 제안 섹션 | Claude만 수정 가능 |
| GPT 검토 섹션 | GPT만 작성, 이전 GPT 섹션은 유지 |
| Gemini 검토 섹션 | Gemini만 작성, 이전 Gemini 섹션은 유지 |
| 현재 해결된 판단 | 자기 버전에서 결정된 항목만 추가 |

---

## 버전 관리 규칙

| 버전 형식 | 작성자 | 설명 |
|---|---|---|
| x.0 | Claude | 메이저 초안 |
| x.짝수 (x.2, x.4...) | Claude | 짝수 소수 첫째자리 — 이전 GPT/Gemini 검토 수용/보류 판단 |
| x.홀수 (x.1, x.3, x.5...) | GPT | 홀수 소수 첫째자리 — 검토 및 제안 추가 |
| x.x.홀수 (x.x.1, x.x.3...) | Gemini | 홀수 소수 둘째자리 — 검토 및 제안 추가 |

---

## 변경 이력

| 버전 | 날짜 | 작성자 | 주요 변경 내용 |
|---|---|---|---|
| v1.0 | 2026-05-21 | Claude | 최초 작성. 기본 아키텍처, 4단계 엔진 라우팅, Phase 1-4 설계 |
| v1.1 | 2026-05-21 | Claude | Claude API 하드코딩 문제 지적. 분류기 우선순위 구체화, fallback 전략 명세, config 항목 보완, Phase 순서 재조정 |
| v2.0 | 2026-05-21 | Claude | LLM-agnostic 구조 채택. LLMBrain 추상 인터페이스 도입. 대→소 캐스케이드 확정. Brain Persona 개념 추가. 모델명 config 중앙화 |
| v2.1 | 2026-05-21 | GPT | 적응형 프레임워크 방향 재정의. Telemetry / Selector Memory / API Detection / 3레이어 분리 제안 |
| v2.2 | 2026-05-21 | Claude | v2.1 수용/보류 판단. SQLite 스키마 명세. 페르소나 버전 관리. 엔진별 smoke test. Policy/Planning/Execution 3레이어 확정 |
| v2.3 | 2026-05-21 | GPT | 상태머신(CrawlJob), Job Queue, Plugin 구조, Browser Context Pool, JSON Schema 강제, 테스트 레벨 분리 제안 |
| v2.4 | 2026-05-21 | Claude | v2.3 수용/보류 판단. CrawlJob 상태머신, Pydantic Schema, Browser Context Pool, Plugin Architecture 채택. Router 분리/에이전트화 Phase 4 이후 보류 |
| v2.5 | 2026-05-21 | GPT | Recovery Planning, Event Log, Capability 기반 Plugin, Selector Telemetry 결합, Stealth Identity Layer 제안. 구현 우선순위 제안 |
| v2.5.1 | 2026-05-21 | Gemini | Event Log 보안 마스킹 필요성 지적. Capability 기반 Plugin 구체화. Browser Pool 우선순위 상향 제안 |
| v2.6 | 2026-05-21 | Claude | v2.5+v2.5.1 수용/보류 판단. Event Log+보안 마스킹, Capability Plugin, Browser Pool 우선순위 상향 채택. MD 작성 규칙 섹션 추가 |
| v2.6.1 | 2026-05-21 | Gemini | 재귀 마스킹(중첩 딕셔너리+쿼리스트링 케이스) 보완. Dual-key Routing 교착 상태 방지 제안. mandatory_fields 기반 partial_success 전이 제안 |
| v2.7 | 2026-05-21 | Claude | v2.6.1 Gemini 수용/보류 판단. 재귀 마스킹 채택. Dual-key Routing + Default Fallback 가드레일 채택. mandatory_fields 기반 partial_success 채택. CrawlResult 출력 표준화 채택 (GPT 비공식 제안 포함). schema.py 대폭 확장 |

### 버전별 결정 근거

**v1.0 → v1.1 (Claude)**
- Claude API 하드코딩 → provider 교체 불가 문제
- Phase 3에서야 AI 등장 → 분류기는 Phase 1부터 필요, 순서 앞당김

**v1.1 → v2.0 (Claude)**
- "뇌만 교체 가능한 구조로" 요청
- 소→대 vs 대→소: 소형모델이 방향 없이 수집하면 대형모델이 더 일함 → 대→소 채택
- 페르소나로 판단 로직 고정 → 대형모델 상시 호출 불필요

**v2.1 (GPT) → v2.2 (Claude)**
- 수용: 3레이어 분리, Telemetry, Selector Memory, API Detection
- Claude 추가: SQLite 스키마 명세, 페르소나 버전 관리, 테스트 전략

**v2.3 (GPT) → v2.4 (Claude)**
- 수용: CrawlJob 상태머신, Pydantic Schema, Browser Context Pool, Plugin Architecture
- 보류: Router 분리 (Phase 2 이전 오버엔지니어링), 에이전트화 (Phase 4 이후)
- Claude 추가: 상태 전이도, Plugin 인터페이스 명세, Pydantic 스키마 예시

**v2.5 (GPT) + v2.5.1 (Gemini) → v2.6 (Claude)**
- 수용: Event Log 분리, 보안 마스킹, Capability Plugin, Browser Pool 우선순위 상향
- 보류: Recovery Planner (Phase 4), Selector Telemetry 결합 (Phase 3), Stealth Identity (Phase 4)
- MD 규칙 섹션 추가: GPT v2.5 변경이력 삭제, Gemini v2.5.1 문서 절단 위반 방지

**v2.6.1 (Gemini) → v2.7 (Claude)**
- 수용: 재귀 마스킹 — 단층 validator는 중첩 딕셔너리·쿼리스트링에서 실제로 뚫림. 즉시 반영
- 수용: Dual-key Routing (URL 1차 → Capability 2차) + Default Fallback 가드레일 — Capability 오설정 시 교착 방지 논리 맞음
- 수용: mandatory_fields 기반 partial_success 전이 — 이분법 config보다 훨씬 현실적. PARTIAL_SUCCESS_AS config 폐기
- 수용 (GPT 비공식): CrawlResult 출력 표준화 — 엔진마다 반환 구조 다르면 router/storage 전부 엔진 종속됨. 반드시 필요
- 보류 (GPT 비공식): "크롤러 vs 에이전트 플랫폼" 예측 — Phase 4 이후 결정 유지
- 보류 (GPT 비공식): selector recovery 고도화 (DOM density, readability류) — Phase 3 이후 과제
- MD 규칙 추가: GPT가 Gemini 차례 건너뛰고 미래 버전 예측 작성한 케이스 금지 명시

---

## 현재 버전: v2.7

---

## Claude 제안 — 다음 검토 시 논의할 것

> Claude만 수정 가능한 섹션.

### 1. CrawlResult — 엔진별 반환 구조 통일 (v2.7 신규 채택)

GPT가 비공식으로 지적한 가장 중요한 포인트.
현재 `execute() -> dict`는 엔진마다 구조가 달라서 router/storage/planner가 전부 엔진 종속된다.
`CrawlResult`로 표준화하면 엔진 추가해도 상위 레이어를 건드릴 필요가 없다.

```python
class CrawlResult(BaseModel):
    success: bool
    partial: bool
    content_type: str                    # text | image | video | mixed
    text: Optional[str] = None
    images: list[str] = []              # 로컬 저장 경로 또는 URL
    videos: list[str] = []
    metadata: dict = {}                  # 제목, 작성자, 날짜 등
    extracted_fields: dict = {}          # mandatory_fields 수집 결과
    errors: list[str] = []
    telemetry: dict = {}                 # duration_ms, retry_count 등
```

모든 엔진의 `execute()`는 이 스키마를 반환해야 한다.

### 2. Dual-key Routing 구현 상세 (Phase 2a)

Gemini 제안 채택. 구현 흐름:

```
1차: URL/domain 패턴 매칭 → 후보 엔진 목록
2차: 후보 엔진 중 required_capabilities 교집합 확인
  → 매칭되면 해당 엔진 선택
  → 매칭 없으면 Default Fallback (PatchrightPlugin) 강제 선택
```

Phase 1까지는 1차만 동작. Phase 2a에서 2차 추가.
Default Fallback은 config에서 지정:
```python
DEFAULT_FALLBACK_ENGINE = "patchright"  # Capability 매칭 실패 시 최후 보루
```

### 3. mandatory_fields → CrawlStrategy에 포함

partial_success 판단 기준을 Planner가 전략 생성 시 함께 정의하도록:

```python
class CrawlStrategy(BaseModel):
    ...
    mandatory_fields: list[str] = []   # 비어있으면 partial_success 무조건 COMPLETED
    optional_fields: list[str] = []
```

### 4. 다음 GPT 검토 요청 항목 (v2.7.1 — 순서 주의)

- CrawlResult 스키마의 누락 필드 여부
- Dual-key Routing의 엣지 케이스 (같은 Capability를 여러 엔진이 가질 때 우선순위)
- Event Log 재귀 마스킹의 성능 오버헤드 허용 범위
- mandatory_fields가 비어있을 때 partial_success 처리 정책

---

## 핵심 설계 원칙

- 무료 / 오픈소스 우선 사용
- fallback 기반 설계
- 실패 복구 자동화
- Provider 독립 구조 (LLM, 브라우저 엔진 모두)
- 범용성 지속 확장
- 정책 / 계획 / 실행 분리
- Plugin + Capability 기반 엔진 확장
- 상태 기반 Job 관리
- 보안: 민감 정보 재귀 자동 마스킹
- 출력 표준화: 모든 엔진은 CrawlResult 반환

---

## 기술 스택

| 역할 | 도구 | 이유 |
|---|---|---|
| 텍스트 / 일반 페이지 | `Scrapling` | HTTP + 브라우저 혼합, 셀렉터 자동 복구 |
| JS 렌더링 / Stealth | `Patchright` | 브라우저 자동화, Cloudflare 우회 |
| 동영상 수집 | `yt-dlp` | 1000+ 플랫폼 대응 |
| 이미지 수집 | `gallery-dl` | 이미지 특화 |
| 오케스트레이션 | `LLMBrain` (추상 인터페이스) | Provider 교체 가능 |
| Schema 검증 | `Pydantic` | planner 출력 검증 + 재귀 보안 마스킹 + CrawlResult 표준화 |
| 저장 | `SQLite` + 로컬 파일시스템 | 의존성 최소화 |

---

## LLM 오케스트레이션 설계

### 대 → 소 구조

```
[대형모델 / 페르소나]
사용자 의도 분석 → Pydantic CrawlStrategy 생성 (mandatory_fields 포함)
    ↓ CrawlJob 생성
[소형모델 / 실행기]
Job 상태 전이하며 단순 실행 → CrawlResult 반환
    ↓
[대형모델] — 실패 / 에러 복구 시에만
```

### 3레이어 분리

```
Policy Layer   → policy.py
  robots.txt 준수, rate limit, blacklist/whitelist

Planning Layer → planner.py
  LLM + Persona → Pydantic CrawlStrategy 생성
  mandatory_fields 포함. JSON Schema 강제로 hallucination 방지

Execution Layer → router.py
  Dual-key Routing (URL 1차 → Capability 2차 → Default Fallback)
  Job 상태머신 운영, CrawlResult 수집
```

### LLM Provider 추상화

```python
# core/brain.py
class LLMBrain(ABC):
    @abstractmethod
    def classify(self, url: str) -> dict: ...
    @abstractmethod
    def plan(self, url: str, context: dict) -> dict: ...
    @abstractmethod
    def recover(self, error: str, context: dict) -> dict: ...
```

```python
# config.py
BRAIN_CONFIG = {
    "primary":  {"provider": "anthropic", "model": "claude-sonnet-4-5"},
    "executor": {"provider": "ollama",    "model": "llama3.2"},
    "fallback": {"provider": "openai",    "model": "gpt-4o-mini"},
}
ACTIVE_BRAIN          = "executor"
USE_CASCADE           = True
ACTIVE_PERSONA        = "v1"
DEFAULT_FALLBACK_ENGINE = "patchright"   # Capability 매칭 실패 시 최후 보루
```

### 모델 캐스케이드 전략

```
1단계: 휴리스틱 (무료) — URL 패턴 매칭 ~90% 커버
2단계: 소형 로컬 모델 (무료) — Ollama + 페르소나
3단계: 클라우드 소형 모델 (저비용) — gpt-4o-mini, gemini-flash
4단계: 클라우드 대형 모델 (최후 수단) — 에러 복구, 셀렉터 자동 생성
```

---

## Pydantic 스키마 (schema.py)

```python
import re
from pydantic import BaseModel, validator
from typing import Literal, Optional
from enum import Enum

# ── 보안 마스킹 ────────────────────────────────────────────────
SENSITIVE_KEYS = {'api_key', 'token', 'password', 'session', 'cookie', 'secret', 'authorization'}
SENSITIVE_RE   = re.compile(r'(token|key|passwd|auth)=([^&\s"\']+)', re.IGNORECASE)

# ── CrawlEvent (Event Log) ─────────────────────────────────────
class CrawlEvent(BaseModel):
    job_id: int
    event_type: str   # job_created | engine_started | captcha_detected
                      # fallback_triggered | selector_recovered | job_completed
    payload: dict

    @validator('payload')
    def mask_sensitive_recursive(cls, v):
        def _mask(obj):
            if isinstance(obj, dict):
                return {k: '***' if k.lower() in SENSITIVE_KEYS else _mask(val)
                        for k, val in obj.items()}
            elif isinstance(obj, list):
                return [_mask(item) for item in obj]
            elif isinstance(obj, str):
                return SENSITIVE_RE.sub(r'\1=***', obj)
            return obj
        return _mask(v)

# ── CrawlStrategy (Planner 출력) ───────────────────────────────
class RetryPolicy(BaseModel):
    max_retries: int = 3
    backoff: Literal["linear", "exponential"] = "exponential"

class CrawlStrategy(BaseModel):
    engine: Literal["scrapling", "gallery-dl", "yt-dlp", "patchright"]
    priority: int = 1
    timeout: int = 30
    retry_policy: RetryPolicy = RetryPolicy()
    fallback_chain: list[str] = ["patchright"]
    telemetry_tags: list[str] = []
    selectors: dict = {}
    mandatory_fields: list[str] = []   # 비어있으면 partial_success → COMPLETED
    optional_fields: list[str] = []
    reason: str = ""

# ── CrawlResult (엔진 출력 표준화) ─────────────────────────────
class CrawlResult(BaseModel):
    success: bool
    partial: bool
    content_type: str                  # text | image | video | mixed
    text: Optional[str] = None
    images: list[str] = []
    videos: list[str] = []
    metadata: dict = {}                # 제목, 작성자, 날짜 등
    extracted_fields: dict = {}        # mandatory_fields 수집 결과
    errors: list[str] = []
    telemetry: dict = {}               # duration_ms, retry_count 등

# ── JobState (상태머신) ────────────────────────────────────────
class JobState(Enum):
    QUEUED          = "queued"
    RUNNING         = "running"
    WAITING_RETRY   = "waiting_retry"
    FALLBACK        = "fallback_running"
    PARTIAL_SUCCESS = "partial_success"
    MANUAL_REVIEW   = "manual_review"
    COMPLETED       = "completed"
    FAILED          = "failed"
```

---

## CrawlJob 상태머신

상태 전이:
```
QUEUED → RUNNING → COMPLETED
                 → FAILED → WAITING_RETRY → RUNNING
                                          → FALLBACK → COMPLETED
                                                     → MANUAL_REVIEW
         RUNNING → PARTIAL_SUCCESS
                     → mandatory_fields 전부 충족 → COMPLETED
                     → mandatory_fields 하나라도 누락 → FAILED
                     → mandatory_fields 비어있음 → COMPLETED (무조건)
```

```python
# execution_layer의 partial_success 전이 판단
if job.state == JobState.PARTIAL_SUCCESS:
    mandatory = job.strategy.mandatory_fields
    if not mandatory:                                          # 필수 필드 미지정
        job.transition_to(JobState.COMPLETED)
    elif all(f in result.extracted_fields for f in mandatory): # 전부 수집
        job.transition_to(JobState.COMPLETED)
    else:                                                      # 누락
        job.transition_to(JobState.FAILED)
```

---

## Plugin Architecture

```python
class EnginePlugin(ABC):
    capabilities: list[str] = []   # Capability 선언

    @abstractmethod
    def can_handle(self, url: str) -> bool: ...   # Phase 1: URL 기반

    @abstractmethod
    def execute(self, job: CrawlJob) -> CrawlResult: ...  # 반환 타입 표준화

    @property
    @abstractmethod
    def name(self) -> str: ...

# Capability 예시
class PatchrightPlugin(EnginePlugin):
    capabilities = ["spa_rendering", "infinite_scroll", "login_session", "captcha_bypass"]

class ScraplingPlugin(EnginePlugin):
    capabilities = ["static_html", "basic_js"]
```

### Dual-key Routing (Phase 2a 이후)

```
1차: URL/domain 패턴 → 후보 엔진 목록
2차: 후보 중 required_capabilities 교집합 확인
  → 매칭 있음: 해당 엔진 선택
  → 매칭 없음: DEFAULT_FALLBACK_ENGINE 강제 선택 (교착 방지)
```

Phase 1까지는 1차(URL 기반)만 동작.

---

## Browser Context Pool

```python
class BrowserContextPool:
    MAX_CONTEXTS = 5      # Hard Limit — 좀비 프로세스 방지
    MAX_BROWSERS = 2

    def acquire(self, domain: str) -> BrowserContext: ...
    def release(self, domain: str, context: BrowserContext): ...
    def invalidate(self, domain: str): ...     # 탐지 시 컨텍스트 폐기
    def cleanup_zombies(self): ...             # 주기적 좀비 프로세스 정리

# 장기 방향: fingerprint rotation, viewport/timezone spoofing
# → Phase 4 이후 stealth_profile.py 분리 검토
```

---

## SQLite 스키마

```sql
CREATE TABLE crawl_jobs (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    url             TEXT NOT NULL,
    engine          TEXT NOT NULL,
    content_type    TEXT,
    state           TEXT NOT NULL,
    retry_count     INTEGER DEFAULT 0,
    error_msg       TEXT,
    brain_used      TEXT,
    strategy_json   TEXT,
    result_json     TEXT,                    -- CrawlResult JSON
    partial         INTEGER DEFAULT 0,
    duration_ms     INTEGER,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Event Log (append-only 행동 이력 — 블랙박스 recorder)
CREATE TABLE crawl_events (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id      INTEGER,
    event_type  TEXT,
    payload     TEXT,     -- JSON (재귀 마스킹 후 저장)
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Selector Memory
CREATE TABLE selector_memory (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    domain      TEXT NOT NULL,
    selector    TEXT NOT NULL,
    status      TEXT NOT NULL,
    hit_count   INTEGER DEFAULT 1,
    last_seen   DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Telemetry 집계 (통계 — Event Log와 역할 다름)
CREATE TABLE telemetry (
    domain              TEXT PRIMARY KEY,
    total_attempts      INTEGER DEFAULT 0,
    success_count       INTEGER DEFAULT 0,
    partial_count       INTEGER DEFAULT 0,
    fallback_count      INTEGER DEFAULT 0,
    captcha_count       INTEGER DEFAULT 0,
    avg_duration_ms     REAL,
    last_updated        DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

---

## 페르소나 버전 관리

```python
# core/persona.py
PERSONAS = {
    "v1": """
너는 웹 크롤러 오케스트레이터다.
사용자의 수집 요청을 분석하고 최적의 실행 계획을 JSON으로만 반환한다.

판단 규칙:
  도메인별 즉시 결정:
    youtube.com, youtu.be     → engine: yt-dlp
    pixiv.net                 → engine: gallery-dl
    twitter.com, x.com        → engine: gallery-dl (이미지) or scrapling (텍스트)
    instagram.com             → engine: gallery-dl
    일반 HTML                 → engine: scrapling, fallback: patchright

  JS 필요 신호:
    React/Vue SPA, 로그인 필요, 무한 스크롤 → engine: patchright

  에러 대응:
    403 → User-Agent 교체 후 재시도
    429 → 딜레이 2배 후 재시도
    CAPTCHA → patchright 전환
    3회 실패 → 에스컬레이션 요청

출력: CrawlStrategy JSON Schema만. 설명 없음.
""",
}
```

---

## 폴더 구조

```
universal-crawler/
├── crawler.py
├── config.py
├── core/
│   ├── brain.py
│   ├── brain_factory.py
│   ├── brains/
│   │   ├── claude.py
│   │   ├── openai.py
│   │   ├── gemini.py
│   │   ├── ollama.py
│   │   └── heuristic.py
│   ├── plugin.py              ← EnginePlugin ABC + Capability 선언
│   ├── schema.py              ← CrawlStrategy, CrawlJob, JobState, CrawlEvent, CrawlResult
│   ├── persona.py
│   ├── policy.py
│   ├── planner.py
│   ├── classifier.py
│   ├── router.py              ← Dual-key Routing + Default Fallback 가드레일
│   ├── browser_pool.py        ← MAX_CONTEXTS Hard Limit + cleanup_zombies
│   ├── storage.py
│   ├── logger.py
│   └── telemetry.py
├── engines/
│   ├── scrapling_engine.py    ← execute() → CrawlResult
│   ├── patchright_engine.py   ← execute() → CrawlResult
│   ├── ytdlp_engine.py        ← execute() → CrawlResult
│   └── gallery_engine.py      ← execute() → CrawlResult
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── smoke/
│   └── regression/
├── output/
│   ├── text/
│   ├── images/
│   └── videos/
└── db/
    └── crawl_history.db
```

---

## 개발 단계

### Phase 1a — 프로젝트 골격
- [ ] 폴더 구조 생성
- [ ] `config.py` 작성 (DEFAULT_FALLBACK_ENGINE 포함)
- [ ] `schema.py` — CrawlStrategy, CrawlJob, JobState, CrawlEvent (재귀 마스킹), CrawlResult
- [ ] SQLite 스키마 생성
- [ ] CLI 진입점 기본 구조

### Phase 1b — Policy + 휴리스틱 + 단일 엔진
- [ ] `policy.py` — robots.txt, blacklist
- [ ] `heuristic.py` — 도메인 → 엔진 매핑 (URL 기반, 1차 라우팅)
- [ ] Scrapling Plugin (`execute() → CrawlResult`)
- [ ] `logger.py` + `telemetry.py` 기본
- [ ] `tests/smoke/` 기본

### Phase 1c — 멀티 엔진 + Browser Pool 인터페이스
- [ ] yt-dlp Plugin, gallery-dl Plugin (`execute() → CrawlResult`)
- [ ] fallback, CrawlJob 상태 전이 (partial_success → mandatory_fields 판단)
- [ ] `browser_pool.py` 인터페이스 정의 (Hard Limit, cleanup_zombies)
- [ ] `tests/integration/` 기본

### Phase 2a — LLM 추상화 + Planner + Dual-key Routing
- [ ] `LLMBrain` ABC, `brain_factory.py`
- [ ] `persona.py` 버전 관리
- [ ] `planner.py` — Persona 주입 + Pydantic 검증 + mandatory_fields 생성
- [ ] `ollama.py` 어댑터
- [ ] router → Dual-key Routing (URL 1차 + Capability 2차 + Default Fallback)

### Phase 2b — Stealth + 클라우드 LLM
- [ ] Patchright Plugin + Browser Pool 구현
- [ ] 딜레이 랜덤화, UA 로테이션
- [ ] `claude.py`, `openai.py`, `gemini.py` 어댑터
- [ ] 대→소 캐스케이드 구현
- [ ] `tests/regression/` anti-bot 기본

### Phase 3 — AI 고도화
- [ ] API Detection Layer (XHR/GraphQL 감지)
- [ ] Selector Memory 활성화
- [ ] Telemetry 기반 페르소나 튜닝
- [ ] 에러 → 대형LLM 복구 전략
- [ ] 페르소나 v2 A/B 비교

### Phase 4 — 스케일
- [ ] Job Queue (대량 URL 병렬 처리)
- [ ] 스케줄링
- [ ] 대시보드 UI (Telemetry + Event Log 시각화)
- [ ] Tor / 무료 VPN 로테이션
- [ ] Router → executor.py / recovery_planner.py 분리 검토
- [ ] stealth_profile.py (fingerprint rotation 등) 분리 검토
- [ ] "크롤러 vs 에이전트 플랫폼" 방향 결정

---

## 현재 해결된 판단

| 이슈 | 결론 |
|---|---|
| LLM 구조 | 대→소 채택 |
| 모델 종속성 | LLMBrain 인터페이스. config만 수정 |
| 버전업 대응 | 모델명 config 중앙화 |
| 비용 절감 | 소형 로컬 모델 기본. 대형모델은 에러 복구만 |
| 레이어 분리 | Policy / Planning / Execution 3레이어 확정 |
| planner 오류 방지 | Pydantic CrawlStrategy 검증 확정 |
| Event Log 보안 | CrawlEvent 재귀 마스킹 (중첩 dict + 쿼리스트링 대응) |
| Job 관리 | CrawlJob 상태머신 채택 |
| partial_success | mandatory_fields 기반 전이. PARTIAL_SUCCESS_AS config 폐기 |
| 엔진 출력 표준화 | CrawlResult Pydantic 모델. 모든 execute() 동일 반환 |
| 엔진 확장 | Plugin Architecture. 명시적 레지스트리 |
| Plugin 라우팅 | Dual-key (URL 1차 → Capability 2차) + Default Fallback 가드레일 |
| 브라우저 재사용 | Browser Context Pool. 도메인별 격리. MAX_CONTEXTS Hard Limit |
| 좀비 프로세스 | cleanup_zombies() 포함. Phase 1c 인터페이스 선행 |
| Telemetry vs Event Log | Telemetry=통계, Event Log=행동 이력(블랙박스 recorder). 분리 |
| Selector Memory | Phase 3에서 DB 기반 구현 |
| 페르소나 관리 | 버전 태그 + config active 지정 |
| 테스트 전략 | unit / integration / smoke / regression 4단계 |
| Recovery Planner | Phase 4 이후 복잡도 보면서 결정 |
| Stealth Identity | Phase 4 이후 stealth_profile.py 분리 검토 |
| 에이전트화 여부 | Phase 4 이후 결정 |
| MD 작성 규칙 | 명시적 규칙 섹션. 차례 외 버전 작성 금지 추가 |

---

## GPT 검토 섹션 (v2.5)

> GPT 작성. 수정 금지.

### 구현 우선순위 제안
```
1. 단일 엔진 정상 동작
2. CrawlJob 상태머신
3. Telemetry
4. Fallback
5. Planner
6. LLM 연동
7. Selector Memory
8. API Detection
9. Browser Pool
10. Stealth 고도화
```
초기부터 stealth/LLM 고도화에 집중하면 디버깅 난이도 급상승.
"단순 구조가 안정적으로 동작하는가" 검증이 먼저.

### 현재 프로젝트 단계 평가 (GPT)
아이디어 수준 → 단순 기획 수준 → **실제 구현 가능한 설계 초안** 단계.
초기 기능 추가 중심에서 실패 처리 / 상태 관리 / 비용 절감 / 유지보수성 관점으로 이동한 점이 긍정적.

---

## Gemini 검토 섹션 (v2.5.1)

> Gemini 작성. 수정 금지.

- 장점: LLMBrain 추상화, 대→소 캐스케이드, Pydantic Schema 등 유연성 확보 훌륭
- 보완: 실패가 일상인 크롤링 환경에 대한 방어적 코드 부족 → Phase별로 보완 예정
- 보안 결함 지적: Event Log payload 평문 덤프 시 API 토큰 노출 위험 → v2.6에서 반영

---

## Gemini 검토 섹션 (v2.6.1)

> Gemini 작성. 수정 금지.

### 1. Event Log 재귀 마스킹 제안
단층 validator는 중첩 딕셔너리({"headers": {"Authorization": "Bearer token"}})와
쿼리스트링(url="https://api.com?token=abcde") 케이스에서 평문 노출.
재귀 탐색 + 정규식 결합으로 해결. → v2.7에서 채택.

### 2. Dual-key Routing 교착 방지
Capability 오설정 시 무한루프 또는 즉시 실패 위험.
URL 1차 → Capability 2차 + Default Fallback 가드레일 구조 제안. → v2.7에서 채택.

### 3. mandatory_fields 기반 partial_success 전이
이분법 config(PARTIAL_SUCCESS_AS)는 데이터 무결성 파괴 위험.
Planner가 mandatory_fields 지정 → 수집 결과와 대조 → COMPLETED/FAILED 결정. → v2.7에서 채택.

---

*최종 수정: v2.7 — 2026-05-21*
*다음 검토: GPT → v2.7.1*
*다음 세션에 이 파일 첨부 후 원하는 Phase + "구현 시작" 이면 바로 진행 가능*
