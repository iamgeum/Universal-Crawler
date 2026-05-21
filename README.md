# Universal-Crawler

범용 웹 크롤링 프레임워크 (LLM co-work 설계)

## 빠른 시작

```bash
pip install -r requirements.txt
cp .env.example .env   # API 키 입력 (Phase 2 이후)

python crawler.py init-db
python crawler.py enqueue "https://example.com"
python crawler.py status

python -m pytest tests/unit/
```

## 문서

- `DEV_CONTEXT.md` — 진척도, Phase 체크리스트
- `universal_crawler_plan.md` — 설계 상세

## 현재 Phase

**1a 완료** — 골격, schema, SQLite, CLI  
**다음: 1b** — policy, heuristic 라우터, scrapling 엔진
