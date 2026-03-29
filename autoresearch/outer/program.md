# Autoresearch Program: 트윗 필터 최적화

## 목표
AI/개발 트렌드 트윗 수집 필터의 품질을 극대화한다.

## Frozen Metric
- **score** = recall * 0.35 + topic_coverage * 0.25 + (1-noise) * 0.2 + diversity * 0.2
- recall: 426개 테스트셋 중 필터 통과 비율 (높을수록 좋음)
- topic_coverage: 통과 트윗 중 14개 토픽에 매칭되는 비율 (높을수록 좋음)
- noise_ratio: 토픽 미매칭 비율 (낮을수록 좋음)
- topic_diversity: 14개 토픽 중 활성 비율 (높을수록 좋음)

## 수정 대상
`target/filter_config.json`의 include_keywords, exclude_keywords만 수정

## 제약
- 제외 키워드에 AI/테크 용어 넣지 말 것
- 포함 키워드는 정규식 호환이어야 함
- 너무 광범위한 키워드 (예: "the", "is") 금지
- 토픽 정의(benchmark.py)는 수정 불가

## 전략 힌트
1. 포함 키워드 추가: 최근 AI 트렌드 용어 (DeepSeek, Qwen, Ollama, Windsurf 등)
2. 포함 키워드 정밀화: 너무 넓은 패턴 축소 (예: \bdev\b → developer)
3. 제외 키워드 확장: 노이즈 패턴 추가
4. 토픽 커버리지 약한 영역 보강
5. 키워드 겹침 정리: 중복 제거로 성능 개선
