---
name: daily-trend-briefing
description: |
  매일 GitHub TrendShift + Product Hunt + X(트위터) + Reddit 4개 소스를 병렬 수집하여
  AI/개발 트렌드 브리핑 마크다운을 자동 생성하는 스킬.
  파트별 개별 파일(part1~4) + 종합 정리 합본을 한 번에 만든다.

  반드시 사용해야 하는 트리거:
  - "트렌드 브리핑", "오늘 트렌드", "트렌딩 정리해줘", "AI 트렌드 분석"
  - "GitHub 트렌딩 + Product Hunt", "4-in-1 브리핑", "4소스 분석"
  - "오늘 뭐가 떴어", "요즘 AI 뭐가 핫해", "트렌드 리포트 만들어줘"
  - "TrendShift 분석", "PH 분석", "트윗 분석", "레딧 분석" (개별 소스도 이 스킬 사용)
  - "GitHub에서 뜨는 거", "Product Hunt 오늘", "X에서 AI 화제", "Reddit AI 커뮤니티"
  - "트렌딩 레포", "신제품 분석", "타임라인 분석", "서브레딧 동향"
  - 사용자가 AI/개발 트렌드를 파악하고 싶어하는 모든 요청
  - 사용자가 "트렌드", "트렌딩", "핫한", "뜨는", "최신" 등의 키워드와 AI/개발을 조합하는 경우
  이 스킬은 ai-tool-learner와 tweet-trend-analyzer를 통합 교체한다.
  개별 소스만 요청해도 이 스킬을 사용하되, 해당 파트만 실행하면 된다.
---

# Daily Trend Briefing — 5-in-1 AI/개발 트렌드 브리핑

6개 소스(TrendShift, Product Hunt, X, Reddit, Hacker News, Polymarket)에서 AI/개발 트렌드를 **병렬 수집**하고,
파트별 개별 파일 + 종합 합본을 생성하는 스킬.

## 왜 6개 소스인가

각 소스는 서로 다른 시각을 제공한다:
- **GitHub TrendShift**: 개발자가 실제로 쓰고 만드는 도구 (공급 측)
- **Product Hunt**: 새로 출시된 제품과 시장 반응 (시장 측)
- **X(트위터)**: 실시간 여론과 바이럴 트렌드 (여론 측)
- **Reddit**: 커뮤니티 깊이 있는 토론과 실전 후기 (실전 측)
- **Hacker News**: 기술적 깊이와 회의적 시각 (비평 측)
- **Polymarket**: 돈이 걸린 집단지성 예측 (시장 예측 측)

하나만 보면 편향되고, 6개를 교차하면 **진짜 트렌드**가 보인다.
3개 이상 소스에서 동시에 등장하면 신뢰도가 높고, 1개 소스에서만 보이면 "숨은 트렌드"다.
Polymarket 데이터로 다른 소스의 주장을 **돈으로 검증**할 수 있다.

## 실행 흐름

```
사용자 요청
    ↓
날짜 확인 (bash: date)
    ↓
Chrome 디버그 프로필 확인 (curl localhost:9222/json/version)
    ├── 안 떠있으면 → Chrome 실행 (--remote-debugging-port=9222)
    └── 떠있으면 → 바로 진행
    ↓
dev-browser 경로 확인 (which dev-browser 또는 npm config get prefix)
    ↓
6개 파트 수집
    ├── Part 1: GitHub (WebFetch → TrendShift 5개 URL) ← 에이전트 위임 가능
    ├── Part 2: Product Hunt (WebFetch) ← 에이전트 위임 가능
    ├── Part 3: X/Twitter (dev-browser DOM 스크롤) ← 직접 수집 필수
    ├── Part 4: Reddit (dev-browser DOM 9개 서브레딧) ← 직접 수집 필수
    ├── Part 5: Hacker News (dev-browser DOM 또는 WebFetch)
    └── Part 6: Polymarket (dev-browser DOM 또는 WebFetch)
    ↓
파트별 파일 저장 (trending-YYYY-MM-DD/part1~6.md)
    ↓
종합 합본 작성 (trending-YYYY-MM-DD.md)
    ├── 각 파트 핵심 테이블
    ├── 크로스 소스 인사이트 (4/3/2/1개 소스 교차)
    ├── 메가 트렌드 5가지
    └── 오늘 바로 해볼 수 있는 액션 4가지
```

## 핵심 규칙 (절대 지키기)

이 규칙들은 실전에서 반복된 실수를 바탕으로 정립됐다. 어기면 사용자가 교정할 것이다.

1. **모든 소스 동등하게 다루기** — 한쪽만 상세하고 나머지를 축약하면 안 됨
2. **테이블 축약 금지** — 25개 레포면 25개 전부 같은 형식. "TOP 5만 상세, 나머지 테이블" 절대 금지
3. **기술적 어려움 미리 걱정 금지** — 일단 시도하고, 안 되면 [수집 실패]로 표시
4. **날짜는 bash로 먼저 확인** — 추측 없이 `date +%Y-%m-%d` 실행
5. **Part 3~4는 반드시 dev-browser DOM 수집** — WebSearch 대체 금지. 실제 DOM 데이터와 WebSearch 결과는 완전히 다름
6. **Chrome DevTools MCP 대신 dev-browser CLI 사용** — MCP는 브라우저 창을 직접 조작하여 사용자 화면 방해
7. **Chrome 디버그 프로필 먼저 확인** — 수집 시작 전 `curl localhost:9222/json/version`으로 Chrome 연결 확인. 안 떠있으면 실행
8. **에이전트 위임은 Part 1~2만** — Part 3~6은 dev-browser가 필요하므로 직접 수집하거나 에이전트에 dev-browser 사용을 명시적으로 지시

## 출력 구조

```
📁 trending-YYYY-MM-DD/       (파트별 상세)
├── part1-github.md           (GitHub 25개 레포, 각각 동일 형식)
├── part2-producthunt.md      (PH 전제품, 오늘+어제)
├── part3-twitter.md          (X 토픽 분석 + 통계)
├── part4-reddit.md           (9개 서브레딧 트렌드)
├── part5-hackernews.md       (HN AI 포스트 + 핵심 토론)
└── part6-polymarket.md       (예측 시장 AI + 세계 동향)

📄 trending-YYYY-MM-DD.md     (종합 합본 — 핵심만 정리)
```

## Part 1: GitHub 트렌딩 (TrendShift)

**수집:** WebFetch로 5개 URL 병렬 접근 → 중복 제거 후 통합

```
1. https://trendshift.io/repositories?d=today     (전체 트렌딩)
2. https://trendshift.io/topics/ai-workflow        (AI 워크플로우)
3. https://trendshift.io/topics/ai-skills          (AI 스킬)
4. https://trendshift.io/topics/ai-coding          (AI 코딩)
5. https://trendshift.io/topics/ai-agent           (AI 에이전트)
```

**중복 제거:** 같은 레포가 여러 URL에서 등장하면 1개만 유지. 레포명(owner/repo) 기준으로 dedup.
토픽 페이지에서만 나타나는 레포는 `[토픽 전용]`으로 표시하여 전체 트렌딩과 구분.

**출력 스타일: 내러티브 + 링크 (테이블 아님)**

토픽별로 그룹핑하여 내러티브 형식으로 작성. 각 레포에 왜 뜨고 있는지 맥락과 시사점 포함.

```markdown
# Part 1: GitHub Trending (TrendShift) — YYYY-MM-DD

> **데이터:** 25개 레포 분석 | **주요 키워드:** Claude Code(N개), Agent(N개), ...

오늘 GitHub 트렌딩의 가장 눈에 띄는 흐름은 **[핵심 트렌드 1문단]**이다.

---

## 1. 에이전트 프레임워크 — "에이전트가 팀을 이루다"

오늘 에이전트 관련 레포가 N개로 전체의 N%를 차지했다. obra/superpowers(119K ⭐)가 ...

주요 레포들:
- **obra/superpowers** (119K ⭐, Shell) — 에이전틱 개발 사실상 표준. [🔗](URL) "방법론"으로의 진화를 보여줌
- **paperclipai/paperclip** (36.9K ⭐, TS) — "제로 휴먼 컴퍼니" 오케스트레이션. [🔗](URL)

> **시사점:** 에이전트가 단일에서 팀으로 진화하며 "에이전트 조직 관리"가 새 카테고리로 형성
> `#에이전트팀오케스트레이션` `#제로휴먼컴퍼니`

---

## 2. Claude Code 생태계 — "..."
...
```

**핵심 규칙:**
- 토픽별 그룹핑 (관련 레포끼리 묶기)
- 각 토픽에 내러티브 도입부 + 레포 목록 + 시사점 + 해시태그
- engagement 데이터(스타, 포크) 포함
- 링크 [🔗](URL) 형식

## Part 2: Product Hunt 신제품

**수집:** Chrome MCP `read_page`로 `https://www.producthunt.com/` 오늘 + 어제

Chrome MCP가 없으면 WebFetch로 대체.

**출력 스타일: 내러티브 + 투표 수 + 링크**

트렌드별로 그룹핑하여 시장 맥락과 함께 서술.

```markdown
# Part 2: Product Hunt — YYYY-MM-DD

> **데이터:** N개 제품 (오늘 N개 + 어제 N개) | **핵심 트렌드:** 에이전트 수익화, 음성 AI, ...

오늘 PH의 가장 눈에 띄는 흐름은 **[핵심 트렌드 1문단]**이다.

---

## 1. AI 에이전트 가치사슬 — "만들기에서 팔기까지"

Crossnode(364🔺)가 AI 에이전트를 노코드로 만들고 **결제벽 뒤에 배포**하는 플랫폼을 내놓았다. ...

주요 제품들:
- **Crossnode** (364🔺) — 노코드 에이전트 + 결제벽 수익화. [🔗](URL)
- **Agentation** (422🔺) — 에이전트 비주얼 피드백/디버깅. [🔗](URL)

> **시사점:** 에이전트 가치사슬이 완성되고 있다 — 만들기(Crossnode) → 관찰(Agentation) → 수익화
> `#에이전트수익화플랫폼` `#노코드에이전트빌더`
```

## Part 3: X(트위터) AI 트렌드

**수집 우선순위:**
1. **dev-browser DOM 스크롤** (추천) — 기존 Chrome 연결, 필터 정확도 최고
2. **dev-browser GraphQL** — ct0 토큰으로 API 직접 호출
3. **Chrome MCP GraphQL** — Cowork 전용
4. **WebSearch 대체** — 위 3개 모두 불가 시

### dev-browser DOM 스크롤 수집 (터미널 기본 방식)

**전제:** Chrome이 디버그 프로필로 실행 중 + X 로그인 완료
```bash
# 최초 1회: 디버그 프로필 Chrome 실행 후 X 수동 로그인
chrome.exe --remote-debugging-port=9222 --user-data-dir="~/.chrome-debug-profile"
# 이후 헤드리스도 가능 (로그인 세션 유지됨)
chrome.exe --headless=new --remote-debugging-port=9222 --user-data-dir="~/.chrome-debug-profile"
```

**수집 절차:**
1. `dev-browser --connect http://localhost:9222` 로 기존 Chrome 연결
2. x.com/home 이동 → 추천 피드 DOM 스크롤 수집 (300개 목표)
3. "팔로잉" 탭 전환 → 팔로잉 피드 DOM 스크롤 수집 (300개 목표)
4. 중복 제거 후 합치기 → AI 키워드 필터링 → 14개 토픽 클러스터링

**스크롤 파라미터 (autoresearch 최적화 완료):**
- 딜레이: 500ms (2배속)
- 스크롤 거리: 2000px
- 포기 임계값: nn=15 (15회 연속 새 트윗 없으면 종료)

### 최적화 필터 키워드 (autoresearch 40회 실험 결과)

**포함 키워드 (score 0.9304→0.9370, noise 15.3%→7.4%):**
```javascript
const include = /\bai\b|AI[는가를의에]|claude|gpt|openai|anthropic|gemini|\bllm|agent|cod(?:ing|e\b|ex)|model|neural|deep.?learn|machine.?learn|robot|automat|startup|saas|\bapi\b|github|docker|kubernetes|cloud|server|database|crypto|blockchain|web3|apple|google|microsoft|nvidia|tesla|\bmeta\b|semiconductor|chip|\bgpu|\bcpu|quantum|\bmcp\b|cursor|copilot|vibe.?cod|prompt|pipeline|perplexity|midjourney|stable.?diffusion|supabase|vercel|nextjs|react|python|rust|swift|kotlin|typescript|hugging.?face|transformer|token|fine.?tun|rag\b|embed|vector|langchain|llamaindex|crew.?ai|autogen|n8n|zapier|NotebookLM|open.?source|developer|\btech\b|framework|deploy|infra|iOS|android|obsidian|algorithm|engineer|software|hardware/i;
```

**제외 키워드 (30+개 autoresearch 추가):**
```javascript
const exclude = /k.?pop|아이돌|컴백|팬사인|치킨|피자|배달|쿠폰|할인|이벤트|경품|추첨|야구|축구|농구|올림픽|월드컵|선거|대통령|국회|정당|탄핵|드라마|예능|웹툰|화장품|뷰티|패션|다이어트|\bMarines\b|cyberoffense|Saudi|Hollywood|actors union|\$milady|\$MILADY|Champs-|retro tech|Jony Ive|discontinuation|amzn\.to|sports data|Lockdown Mode|visa expires|hunter sneaking|FREE certifications|netacad\.com|paralyzed.*patient|touchscreen controls|hospital caregivers|Postman.*collaboration|thumbs down my own reply|Premium-Level Courses.*beginner|free courses to learn|Pure gold for.*learners|AI bootcamps|Intermediate.*Tutorials|highsfield|IPFire.*Bitcoin|Build A Chat Bot.*Python|Asustemos|lump of labor|Bay Area.*tech roles|Tesla FSD|Tesla Optimus|Stay there.*any other country|Mac Pro.*단종|Postman.*paid feature|Docker has an update|months.*zero code|Real talk.*AI can build/i;
```

### Cowork에서는 Chrome MCP GraphQL 사용

상세 설정은 `references/twitter-config.md`에 있다.
Chrome MCP가 없거나 X 로그인이 안 되어있으면 [수집 실패]로 표시하고 다른 파트를 계속 진행.

**수집 절차 요약 (Cowork/Chrome MCP):**
1. Chrome MCP로 x.com 열기
2. javascript_tool로 ct0 쿠키 추출
3. GraphQL API로 18페이지 배치 수집 (500+ 트윗)
4. 브라우저 JS로 필터링 + 14개 토픽 클러스터링
5. JSON.stringify()로 결과 반환 (raw string은 차단됨)

**출력 스타일: AI_trend_summary 내러티브 스타일**

이전 회차 출력물을 참고 모델로 한다. 핵심:
- 토픽별 내러티브 도입부 (가장 눈에 띄는 흐름 서술)
- 대표 트윗은 engagement 수치 + 원문 링크 [🔗](URL) 포함
- 각 토픽 끝에 `> **시사점:**` + 해시태그 `#키워드`
- 마지막에 감정/온도 분석 (🔴과열 🟢성장 🟡주의 🔵전환)
- 바이브 코딩 시사점 섹션 (사용자 맞춤 액션)

```markdown
# Part 3: X(트위터) AI 트렌드 — YYYY-MM-DD

> **데이터:** N개 트윗 분석 (AI/테크 N개 필터링, N%) | **주요 키워드 TOP 5:** Claude(N+), AI(N+), ...

오늘 타임라인에서 가장 눈에 띄는 흐름은 **[핵심 1문단]**이다.

---

## 1. Claude/Anthropic — "사랑과 분노 사이"

오늘 Claude 관련 트윗이 가장 많았고... "OpenAI가 Microsoft 같다면 Claude는 Apple 같다"는 트윗이 2,421 engagement로 최고 수치를 기록했다. (@handle) [🔗](URL)

주요 소식들:
- **Claude "Operon" 에이전트 개발 중** — 생물학 연구 특화 에이전트 (@handle, N eng) [🔗](URL)
- **Claude Code hooks에 if 조건 지원** — 세션 속도 개선 (@handle, N eng) [🔗](URL)

> **시사점:** Claude 생태계가 커지면서 양극화가 심해지고 있다...
> `#클로드레이트리밋양극화` `#오페론에이전트생물학특화`

---

## 📊 오늘의 감정/온도 분석
- 🔴 과열: ...
- 🟢 성장: ...
- 🟡 주의: ...
- 🔵 전환: ...

## 🎯 바이브 코딩 시사점
1. **구체적 액션** — 설명
2. ...
```

## Part 4: Reddit AI 커뮤니티

**수집 우선순위:**
1. **dev-browser DOM 스크롤** (추천) — 기존 Chrome 연결, 직접 포스트 수집
2. **WebSearch + WebFetch** (대체) — dev-browser 불가 시

### dev-browser DOM 수집 (기본 방식)

**전제:** Chrome 디버그 프로필에서 Reddit 캡차 1회 통과 (이후 세션 유지)
```bash
dev-browser --connect http://localhost:9222
```

**대상 서브레딧 (9개, AI 관련성 테스트 완료):**

| 서브레딧 | AI 비율 | 성격 |
|---------|:------:|------|
| r/artificial | 87.5% | AI 뉴스 종합 |
| r/mlops | 87.5% | ML 인프라/운영 |
| r/ClaudeAI | 84.0% | Claude 전반 |
| r/singularity | 69.2% | AGI/미래 |
| r/OpenAI | 68.0% | OpenAI/GPT |
| r/ClaudeCode | 56.0% | Claude Code 실전 |
| r/ChatGPT | 52.0% | ChatGPT 사용자 |
| r/LocalLLaMA | 40.0% | 로컬 LLM |
| r/MachineLearning | 40.0% | AI 연구 |

**수집 절차:**
1. 각 서브레딧 `/hot/` 페이지 이동
2. 스크롤 3-5회로 포스트 로드
3. DOM에서 제목, 업보트, 댓글 수 파싱 (`shreddit-post` 요소의 `score`, `comment-count` 속성)
4. AI 키워드 필터링 후 서브레딧별 TOP 포스트 추출

### WebSearch + WebFetch 대체 방식

dev-browser 불가 시 WebSearch 사용:

**검색 쿼리 (전부 실행):**
1. `reddit r/LocalLLaMA trending LLM local models this week YYYY`
2. `reddit r/ClaudeAI discussions Claude AI {month} YYYY`
3. `reddit r/ChatGPT trending discussions GPT {month} YYYY`
4. `reddit r/MachineLearning hot posts AI research {month} YYYY`
5. `reddit r/artificial intelligence news trending {month} YYYY`
6. `reddit r/singularity AI AGI trending {month} YYYY`
7. `reddit r/mlops AI infrastructure {month} YYYY`
8. `reddit r/ClaudeCode Claude Code tips {month} YYYY`
9. `reddit AI tools most upvoted YYYY ranked`
10. `reddit AI news this week {날짜}`

유용한 링크는 WebFetch로 상세 수집 (aitooldiscovery.com, dev.to, ainewslog.com 등).

**출력 스타일: 내러티브 + 업보트 + 댓글 인용**

서브레딧별로 분위기와 핵심 토론을 내러티브로 서술. 핵심 댓글 직접 인용 포함.

```markdown
# Part 4: Reddit AI 커뮤니티 — YYYY-MM-DD

> **데이터:** N개 서브레딧 스캔, AI 포스트 N개 | **가장 뜨거운 서브레딧:** r/ClaudeAI

오늘 Reddit의 가장 눈에 띄는 흐름은 **[핵심 1문단]**이다.

---

## 1. r/ClaudeAI — "앱스토어 1위의 명과 암"

Claude가 앱스토어 1위를 찍으면서 r/ClaudeAI 분위기가... 가장 많은 업보트를 받은 글은 "5년차 개발자인데 Claude Max 보고 내가 필요한가 자문했다"(N🔺, N댓글)...

주요 포스트:
- **"Claude Code가 Codex를 압도한다"** (N🔺, N댓글) — 커뮤니티 논의량 4배 차이 [🔗](URL)

> **시사점:** 개발자 정체성 위기와 도구 만족이 공존
> `#클로드앱스토어일위` `#개발자무용론논쟁`

---

## 📊 Reddit 감정/온도
| 서브레딧 | 감정 | 온도 | 핵심 키워드 |
...

## 🎯 바이브 코딩 시사점
1. ...
```

## Part 5: Hacker News

**수집:** dev-browser DOM 파싱 (차단 없음, 헤드리스 가능)

**수집 절차:**
1. `news.ycombinator.com` 프론트 페이지 + 2~3페이지 수집
2. `.athing` 요소에서 제목, URL, 포인트, 댓글 수, 시간 파싱
3. AI 키워드 필터링 → 포인트 순 정렬

**DOM 파싱 셀렉터:**
- 포스트: `.athing` → `.titleline a` (제목/URL)
- 메타: 다음 형제 요소 → `.score` (포인트), `a[댓글 링크]`, `.age` (시간)

**출력 형식:**
```markdown
# Part 5: Hacker News — YYYY-MM-DD

## AI/개발 TOP 포스트 (포인트 순)
| 순위 | 제목 | 포인트 | 댓글 | 시간 |
|:---:|------|------:|----:|------|
| 1 | 제목 | Npt | N | N hours ago |

## 핵심 토론 요약
### 1. 최다 댓글 포스트 (제목)
> 커뮤니티 핵심 논점 요약

## HN 온도
- 이번 주 AI 관련 포스트 비율: N%
- 커뮤니티 분위기: 긍정/회의/중립
```

**특성:** HN은 과대광고에 회의적이고 기술적 깊이를 선호. Reddit과 다른 시각 제공.

## Part 6: Polymarket 예측 시장

**수집:** dev-browser DOM 파싱 (차단 없음, 로그인 불필요)

**가치:** 돈이 걸린 집단지성 — 여론조사보다 정확한 예측 데이터. AI뿐 아니라 지정학/경제/테크 전반의 "시장이 보는 미래"를 제공.

**수집 절차:**
1. `polymarket.com/tech` 페이지 이동
2. AI(93개), Big Tech(144개), OpenAI(40개) 등 카테고리별 스크롤
3. 마켓 제목, 확률(%), 거래량 파싱
4. AI 관련 + 주요 동향 마켓 추출

**대상 카테고리:**

| 카테고리 | 마켓 수 | 용도 |
|---------|:------:|------|
| AI | 93 | AI 모델/기업 순위, 출시 예측 |
| Big Tech | 144 | 시가총액, 인수합병, 실적 |
| OpenAI | 40 | OpenAI 특화 이벤트 |
| Elon Musk | 52 | Tesla/xAI/SpaceX |
| Finance | 다수 | 경제 지표, 금리, 환율 |
| Geopolitics | 다수 | 전쟁/분쟁/정책 확률 |

**출력 형식:**
```markdown
# Part 6: Polymarket 예측 시장 — YYYY-MM-DD

## 🤖 AI 마켓 핵심
| 마켓 | 1위 예측 | 확률 | 거래량 |
|------|---------|:----:|------:|
| Best AI Model (월) | Anthropic | 99% | $16M |

## 💰 Big Tech 동향
| 마켓 | 예측 | 확률 | 거래량 |
|------|------|:----:|------:|
| 시가총액 1위 (월) | NVIDIA | 91% | $19M |

## 🌍 세계 동향 (거래량 TOP 10)
- 돈이 가장 많이 걸린 마켓 = 세상이 가장 주목하는 이슈

## 📊 시장 온도계
- AI 분야: Anthropic 독주 / OpenAI 하락 / xAI 부상
- 거시경제: 주요 경제 이벤트 확률
```

**특성:** 실제 돈이 걸려있어 감정적 편향이 적음. "시장이 보는 미래"로 다른 소스의 분석을 검증하는 앵커 역할.

## 종합 합본 작성법

파트별 파일이 모두 완성된 후, 종합 합본을 작성한다.
합본은 **단순 이어붙이기가 아니라**, 6개 소스를 교차 분석한 정리본이다.

**합본 구조:**
```markdown
# 오늘의 AI/개발 트렌드 — YYYY-MM-DD
**소스:** TrendShift · Product Hunt · X(트위터) · Reddit · Hacker News
**상세:** [Part 1](trending-YYYY-MM-DD/part1-github.md) · ...

## 핵심 트렌드 요약
> 5개 소스를 종합한 1문단 요약 (가장 큰 사건 + 3가지 메가 트렌드)

## Part 1 핵심 — GitHub (핵심 레포 테이블 + 신호)
## Part 2 핵심 — Product Hunt (핵심 제품 테이블 + 신호)
## Part 3 핵심 — X/트위터 (토픽 테이블 + 신호)
## Part 4 핵심 — Reddit (최대 화제 + 도구 순위 + 이슈)
## Part 5 핵심 — Hacker News (TOP 포스트 + 핵심 토론)
## Part 6 핵심 — Polymarket (AI 예측 + 세계 동향 + 시장 온도)

## 🔗 크로스 소스 인사이트
### 6개 소스 모두에서 확인 (최고 신뢰도)
### 5개 소스 교차 확인
### 4개 소스 교차 확인
### 3개 소스 교차 확인
### 2개 소스 교차 확인
### 단일 소스 숨은 트렌드

## 오늘의 메가 트렌드 5
## 오늘 바로 해볼 수 있는 액션 4
```

**크로스 소스 인사이트 작성 원칙:**
- 2개 이상 소스에서 같은 프로젝트/이슈가 나오면 교차 트렌드로 표시
- 4개 소스 = 최고 신뢰도, 3개 = 강한 신호, 2개 = 주시, 1개 = 숨은 트렌드
- 각 교차 항목에 어느 소스에서 어떻게 나타났는지 구체적으로 기술

**메가 트렌드 작성 원칙:**
- 교차 소스 분석에서 가장 강한 5가지 추출
- 각 트렌드에 📍 출처 소스 명시
- 간결한 1-2문장으로 핵심만 (상세는 파트 파일 참조)

**액션 아이템 작성 원칙:**
- 오늘 바로 실행 가능한 구체적 행동
- 설치 명령어나 첫 단계 포함
- 교차 검증된 도구 우선

## 공통 출력 스타일 가이드 (모든 파트 + 합본)

**참고 모델:** 이전 회차 출력물 (AI_trend_summary_YYYY-MM-DD.md)

모든 파트와 합본은 아래 스타일을 따른다:

### 1. 내러티브 우선 (테이블 보조)
- 토픽/카테고리별 **이야기체 도입부** (가장 눈에 띄는 흐름 1문단)
- 개별 항목은 bullet 리스트 + engagement 수치 + [🔗](URL) 링크
- 테이블은 요약용으로만 사용 (메인 형식 아님)

### 2. Engagement 수치 필수
- X: 좋아요/RT/조회수 + engagement 점수
- Reddit: 업보트/댓글 수
- HN: 포인트/댓글 수
- PH: 투표 수
- GitHub: Stars/Forks
- Polymarket: 확률/거래량

### 3. 원문 링크 포함
- 모든 대표 항목에 `[🔗](URL)` 또는 `(@handle, N eng) [🔗](URL)` 형식

### 4. 토픽 끝에 시사점 + 해시태그
```markdown
> **시사점:** 이 트렌드가 의미하는 것 1-2문장
> `#핵심키워드1` `#핵심키워드2` `#핵심키워드3`
```

### 5. 감정/온도 분석 (파트 마지막)
```markdown
## 📊 오늘의 감정/온도 분석
- 🔴 과열: [토픽] — 이유
- 🟢 실질적 성장: [토픽] — 이유
- 🟡 주의 필요: [토픽] — 이유
- 🔵 패러다임 전환: [토픽] — 이유
```

### 6. 바이브 코딩 시사점 (합본 마지막)
사용자의 실전 워크플로우에 바로 적용할 수 있는 구체적 액션:
```markdown
## 🎯 바이브 코딩 시사점
1. **구체적 기능/도구** — 적용 방법과 이유
2. **패턴/전략** — 실전 활용법
3. ...
```

## 개별 소스 요청 처리

사용자가 특정 소스만 요청하는 경우 (예: "GitHub 트렌딩만 분석해줘"):
- 해당 파트만 실행하여 파트 파일 생성
- 합본은 생성하지 않음
- 나중에 다른 소스를 추가 요청하면 기존 파트에 합쳐서 합본 생성 가능


## 실패 처리

각 소스는 독립적이므로, 하나가 실패해도 나머지는 계속 진행:
- **dev-browser 불가** → Part 3, 4를 WebSearch/WebFetch로 대체
- **Chrome 디버그 프로필 없음** → dev-browser 자체 브라우저 사용 (X 로그인 필요)
- **X 로그인 안 됨** → Part 3 WebSearch 대체 수집
- **Reddit 캡차** → 수동 통과 1회 필요, 이후 세션 유지
- **WebSearch 결과 부족** → 있는 데이터로 최대한 작성
- **전체 실패는 거의 없음** — Part 1은 WebFetch만으로 항상 동작

## dev-browser 설정 요약

**모든 파트(Part 3~6)가 하나의 Chrome 인스턴스를 공유한다.** 한번 띄우면 X, Reddit, HN, Polymarket 전부 같은 Chrome에서 수집.

```bash
# 설치 (최초 1회)
npm install -g dev-browser
dev-browser install

# Chrome 디버그 프로필 (최초 1회)
chrome.exe --remote-debugging-port=9222 --user-data-dir="~/.chrome-debug-profile"
# → X 수동 로그인 + Reddit 캡차 통과 (이후 세션 유지)

# 이후 사용 — 모든 파트가 이 명령 하나로 연결
dev-browser --connect http://localhost:9222
```

**수집 흐름:** Chrome 1개 → Part 3(X 탭) → Part 4(Reddit 9개 탭 순차) → Part 5(HN 탭) → Part 6(Polymarket 탭) 순서 또는 병렬 에이전트로 동시 실행.
