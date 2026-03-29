# Daily Trend Briefing

6개 소스를 병렬 수집하여 AI/개발 트렌드 브리핑을 자동 생성하는 [Claude Code](https://claude.ai/code) 스킬.

매일 실행하면 **GitHub + Product Hunt + X + Reddit + Hacker News + Polymarket**에서 트렌드를 수집하고, 파트별 상세 분석 + 종합 합본 마크다운을 한 번에 만들어 줍니다.

## 왜 6개 소스인가

| 소스 | 관점 | 수집 방법 |
|------|------|----------|
| **GitHub TrendShift** | 개발자가 실제로 쓰는 도구 (공급) | WebFetch |
| **Product Hunt** | 새로 출시된 제품과 시장 반응 (시장) | WebFetch / Chrome MCP |
| **X (트위터)** | 실시간 여론과 바이럴 (여론) | dev-browser DOM 스크롤 |
| **Reddit** | 커뮤니티 심층 토론과 실전 후기 (실전) | dev-browser DOM |
| **Hacker News** | 기술적 깊이와 회의적 시각 (비평) | dev-browser DOM |
| **Polymarket** | 돈이 걸린 집단지성 예측 (시장 예측) | dev-browser DOM |

하나만 보면 편향됩니다. 6개를 교차하면 **진짜 트렌드**가 보입니다.
- 3개 이상 소스에서 동시에 등장하면 신뢰도 높음
- 1개 소스에서만 보이면 "숨은 트렌드"
- Polymarket 데이터로 다른 소스의 주장을 **돈으로 검증** 가능

## 출력 예시

```
trending-2026-03-29/          # 파트별 상세
├── part1-github.md           # GitHub 25개 레포 내러티브 분석
├── part2-producthunt.md      # PH 전제품 (오늘+어제)
├── part3-twitter.md          # X 토픽별 분석 + 통계
├── part4-reddit.md           # 9개 서브레딧 트렌드
├── part5-hackernews.md       # HN AI 포스트 + 핵심 토론
└── part6-polymarket.md       # 예측 시장 AI + 세계 동향

trending-2026-03-29.md        # 종합 합본 (교차 분석 + 액션 아이템)
```

## 설치

### 1. 스킬 복사

```bash
# daily-trend-briefing 스킬 설치
cp -r skill/ ~/.claude/skills/daily-trend-briefing/

# tweet-trend-analyzer 스킬 설치 (선택)
mkdir -p ~/.claude/skills/tweet-trend-analyzer/
cp skill/tweet-trend-analyzer-SKILL.md ~/.claude/skills/tweet-trend-analyzer/SKILL.md
```

### 2. dev-browser 설치 (X, Reddit, HN, Polymarket 수집용)

```bash
npm install -g dev-browser
dev-browser install
```

### 3. Chrome 디버그 프로필 설정 (최초 1회)

```bash
# 디버그 프로필로 Chrome 실행
chrome.exe --remote-debugging-port=9222 --user-data-dir="~/.chrome-debug-profile"
```

Chrome이 열리면:
1. X(트위터)에 로그인
2. Reddit에서 캡차 1회 통과

이후에는 이 프로필을 재사용하면 됩니다.

## 사용법

### Chrome 디버그 프로필 실행

```bash
chrome.exe --remote-debugging-port=9222 --user-data-dir="~/.chrome-debug-profile"
```

### Claude Code에서 실행

```
트렌드 브리핑 해줘
```

또는 스킬을 등록했다면:

```
/daily-trend-briefing
```

개별 소스만 요청할 수도 있습니다:

```
GitHub 트렌딩만 분석해줘
오늘 Product Hunt 정리해줘
X에서 AI 관련 뭐가 떴어?
```

## 실행 흐름

```
사용자 요청
    ↓
날짜 확인 (bash: date)
    ↓
6개 파트 병렬 수집 (에이전트 6개 동시)
    ├── Part 1: GitHub (WebFetch → TrendShift)
    ├── Part 2: Product Hunt (WebFetch / Chrome MCP)
    ├── Part 3: X/Twitter (dev-browser DOM 스크롤)
    ├── Part 4: Reddit (dev-browser DOM)
    ├── Part 5: Hacker News (dev-browser DOM)
    └── Part 6: Polymarket (dev-browser DOM)
    ↓
파트별 파일 저장 (trending-YYYY-MM-DD/part1~6.md)
    ↓
종합 합본 작성 (trending-YYYY-MM-DD.md)
    ├── 각 파트 핵심 테이블
    ├── 크로스 소스 인사이트
    ├── 메가 트렌드 5가지
    └── 오늘 바로 해볼 수 있는 액션 4가지
```

## 프로젝트 구조

```
├── skill/                           # 스킬 정의
│   ├── SKILL.md                     # daily-trend-briefing 메인 스킬
│   ├── tweet-trend-analyzer-SKILL.md  # 트위터 단독 분석 (참고용)
│   ├── evals/                       # 스킬 평가 데이터
│   └── references/                  # 트위터 GraphQL 설정 등 참조 문서
```

## 요구사항

- [Claude Code](https://claude.ai/code)
- [dev-browser](https://www.npmjs.com/package/dev-browser) (X, Reddit, HN, Polymarket 수집)
- Chrome (디버그 프로필)

## 라이선스

[MIT](LICENSE)
