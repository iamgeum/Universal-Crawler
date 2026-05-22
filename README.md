# Universal-Crawler

범용 웹 크롤링 프레임워크 (LLM co-work 설계)

## 빠른 시작

```bash
pip install -r requirements.txt
cp .env.example .env   # API 키 입력 (Phase 2 이후)

python crawler.py init-db
python crawler.py plan "https://example.com" --planner heuristic
python crawler.py plan "https://example.com" -c static_html --planner auto
python crawler.py enqueue "https://example.com" --planner auto
python crawler.py crawl "https://example.com" --planner heuristic
python crawler.py run 1
python crawler.py status

python -m pytest tests/unit/
python -m pytest tests/smoke/   # 네트워크 필요
```

## 문서

- `DEV_CONTEXT.md` — 진척도, Phase 체크리스트
- `universal_crawler_plan.md` — 설계 상세

## 현재 Phase

**2b 완료** — patchright, browser pool, Claude/OpenAI/Gemini, 대→소 cascade  
**다음: 3** — API Detection, Selector Memory

```bash
pip install patchright && patchright install chromium  # patchright 엔진
# .env: ANTHROPIC_API_KEY, OPENAI_API_KEY, GEMINI_API_KEY (클라우드 cascade)
python crawler.py plan URL --planner cascade
```
