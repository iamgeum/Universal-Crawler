# Universal-Crawler

범용 웹 크롤링 프레임워크 (LLM co-work 설계)

## 빠른 시작

```bash
pip install -r requirements.txt
cp .env.example .env   # API 키 입력 (Phase 2 이후)

python crawler.py init-db
python crawler.py enqueue "https://example.com"   # heuristic 라우팅
python crawler.py run 1                           # queued Job 실행
python crawler.py crawl "https://example.com"     # 등록+실행 (scrapling)
python crawler.py status

python -m pytest tests/unit/
python -m pytest tests/smoke/   # 네트워크 필요
```

## 문서

- `DEV_CONTEXT.md` — 진척도, Phase 체크리스트
- `universal_crawler_plan.md` — 설계 상세

## 현재 Phase

**1c 완료** — yt-dlp, gallery-dl, fallback, browser_pool 인터페이스  
**다음: 2a** — LLMBrain, planner, Dual-key Routing
