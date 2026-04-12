---
name: daily-trend-briefing
description: |
  매일 GitHub TrendShift + Product Hunt + X(트위터) + Reddit 4개 소스를 수집하여
  AI/개발 트렌드 브리핑 마크다운 + HTML 대시보드를 자동 생성하는 스킬.
  X 수집은 tweet-trend-analyzer 스킬의 Phase 0/1(Chrome MCP + DuckDB)을 사용하고,
  전 소스를 CSV 정규화 → DuckDB 크로스 소스 JOIN으로 교차 분석한다.

  반드시 사용해야 하는 트리거:
  - "트렌드 브리핑", "오늘 트렌드", "트렌딩 정리해줘", "AI 트렌드 분석"
  - "4-in-1 브리핑", "4소스 분석", "오늘 뭐가 떴어", "요즘 AI 뭐가 핫해"
  - "TrendShift", "PH 분석", "트윗 분석", "레딧 분석" (개별 소스도 이 스킬 사용)
  - 사용자가 AI/개발 트렌드를 파악하려는 모든 요청
  이 스킬은 ai-tool-learner와 tweet-trend-analyzer를 통합 교체한다.
  스케줄 실행 지원: scheduled-tasks로 등록하면 매일 자동 실행 가능.
---

# Daily Trend Briefing v2

4개 소스에서 AI/개발 트렌드를 수집·분석하여 마크다운 + HTML 대시보드를 생성한다.

**레포:** https://github.com/inbeomheo/daily-trend-briefing

**v2 핵심 변경:**
- X 수집을 tweet-trend-analyzer Phase 0/1로 교체 (500+ 트윗, DuckDB 분석)
- 전 소스 CSV 정규화 → DuckDB 크로스 소스 JOIN 자동 교차 분석
- HTML 대시보드 자동 생성 (Chart.js)
- GitHub MCP / \`gh\` CLI 백업 소스 추가

## 아키텍처

\`\`\`
Step 1~4: 병렬 수집 → CSV 정규화
    ├── /tmp/github_trending.csv
    ├── /tmp/producthunt_today.csv
    ├── /tmp/tw_timeline_YYYYMMDD.csv → DuckDB → /tmp/tw_*.json
    └── /tmp/reddit_trends.csv
         ↓
Step 5: DuckDB 크로스 소스 JOIN → /tmp/cross_source.json
         ↓
Step 6: trending-YYYY-MM-DD.md
Step 7: trending-YYYY-MM-DD.html (대시보드)
\`\`\`

## 핵심 규칙

1. **모든 소스 동등** — 한쪽만 상세하고 나머지 축약 금지
2. **축약 금지** — 25개 레포면 25개 전부 같은 형식
3. **걱정 금지** — 일단 시도, 안 되면 [수집 실패]
4. **날짜 확인** — bash \`date +%Y-%m-%d\` 먼저 실행
5. **CSV 실패해도 MD 진행** — 크로스 분석만 수동 전환

---

## Step 1: GitHub (TrendShift)

WebFetch \`https://trendshift.io/\` → 25개 전부 동일 형식
실패 시 → \`gh api /search/repositories\` 또는 GitHub MCP 백업

**각 항목 형식:**
- 이름, 설명, 언어, Stars, Forks, 링크
- 핵심도(★1~5), 초보자용(⬤1~5), 통찰 1문장

**CSV:** \`/tmp/github_trending.csv\` (rank,name,description,language,stars,forks,url,keywords)

## Step 2: Product Hunt (Chrome MCP)

\`read_page\` → \`producthunt.com\` 오늘+어제 전부 동일 형식
Chrome MCP 없으면 WebFetch 대체

**각 항목 형식:**
- 이름, 설명, 투표수, 링크, 카테고리
- 핵심도, 초보자용, 통찰

**CSV:** \`/tmp/producthunt_today.csv\` (rank,name,description,votes,url,category,keywords)

## Step 3: X(트위터) — tweet-trend-analyzer 방식

**실행 전 반드시 Read:**
1. \`skills/tweet-trend-analyzer/references/graphql-config.md\`
2. \`skills/tweet-trend-analyzer/references/browser-collect.md\`
3. \`skills/tweet-trend-analyzer/references/topic-definitions.md\`
4. \`skills/tweet-trend-analyzer/references/duckdb-queries.md\`

**Phase 0:** browser-collect.md 그대로 실행 (batchFetch(13), ~500개)
→ \`/tmp/tw_timeline_YYYYMMDD.csv\`

**Phase 1:** DuckDB 설치 → duckdb-queries.md 6개 쿼리 실행
→ \`/tmp/tw_stats.json\`, \`tw_topics.json\`, \`tw_top_tweets.json\`, \`tw_authors.json\`, \`tw_keywords.json\`, \`tw_uncategorized.json\`

**출력 형식:** 토픽별 한국어 서술, [🔗](URL) 인용 필수, 한글 단위(25만, 2.5천)

## Step 4: Reddit (WebSearch)

5개 검색 (MONTH/YYYY 현재 연월 치환):
- \`reddit r/{LocalLLaMA|ClaudeAI|ChatGPT|MachineLearning|artificial} ... MONTH YYYY\`

유용한 링크 WebFetch 상세 수집

**CSV:** \`/tmp/reddit_trends.csv\` (subreddit,title,description,upvotes,url,keywords)

**출력 구조:** 이번 주 최대 화제 → Reddit 추천 AI 도구 → 서브레딧별 동향 → 감정/온도

## Step 5: DuckDB 크로스 소스 분석

4개 CSV/JSON을 DuckDB UNION ALL → 이름/키워드 기반 교차 매칭

\`\`\`sql
WITH all_sources AS (
    SELECT 'github' AS source, name, keywords FROM read_csv('/tmp/github_trending.csv', ...)
    UNION ALL SELECT 'producthunt', name, keywords FROM read_csv('/tmp/producthunt_today.csv', ...)
    UNION ALL SELECT 'twitter', topic, '' FROM read_json('/tmp/tw_topics.json')
    UNION ALL SELECT 'reddit', title, keywords FROM read_csv('/tmp/reddit_trends.csv', ...)
)
-- 이름/키워드 겹침 탐지 → /tmp/cross_source.json
\`\`\`

→ "크로스 소스 인사이트" 자동 생성

## Step 6: MD 작성

파일명: \`trending-YYYY-MM-DD.md\`

\`\`\`
# 오늘의 AI/개발 트렌드 — YYYY-MM-DD
**소스:** TrendShift · Product Hunt · X(트위터) · Reddit
**레포:** [inbeomheo/daily-trend-briefing](https://github.com/inbeomheo/daily-trend-briefing)
## 핵심 트렌드 요약 (4개 소스 종합 1문단)
## Part 1: GitHub 트렌딩 — 25개 전부
## Part 2: Product Hunt — 전부
## Part 3: X(트위터) — 15개 토픽 전부
## Part 4: Reddit — 5개 서브레딧
## 🔗 크로스 소스 인사이트 (cross_source.json 기반)
## 오늘의 메가 트렌드 — 5가지
## 오늘 바로 해볼 수 있는 액션 4가지
## 📚 수집 소스 (원본 URL 전부)
\`\`\`

## Step 7: HTML 대시보드

파일명: \`trending-YYYY-MM-DD.html\`
Chart.js CDN, 다크 테마, 모바일 반응형.

구성:
- 카드 4개: 소스별 수집 통계
- 도넛차트: GitHub 언어 분포
- 바차트: X 토픽별 engagement
- 히트맵: 크로스 소스 매칭
- 테이블: 2개+ 소스 언급 항목
- 카드: 메가 트렌드 5개

data 플러그인 있으면 \`build-dashboard\` 스킬 활용.

---

## 개별 소스 요청

특정 소스만 요청 시 해당 Step만 실행. 합본·대시보드는 전체 실행 시에만 생성.

## 실패 처리

각 소스 독립 — 하나 실패해도 나머지 계속 진행.
- Chrome MCP 없음 → Part 2, 3을 WebFetch/WebSearch 대체 시도
- X 로그인 안 됨 → Part 3 [수집 실패]
- CSV 정규화 실패 → MD는 진행, 크로스 분석만 수동

## 스케줄 실행

\`scheduled-tasks\`로 등록 시:
- 전제: Chrome에서 x.com + producthunt.com 로그인 유지
- cron: \`0 8 * * *\` (매일 오전 8시)
- 출력: 워크스페이스 폴더
