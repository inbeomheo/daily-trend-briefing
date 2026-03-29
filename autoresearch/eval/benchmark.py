"""
Frozen Metric: 트윗 필터 품질 평가
- test_tweets.json (426개 DOM 수집 트윗 = 이미 AI 필터 통과한 것들)
- graphql_raw.json에서 전체 562개 트윗의 토픽별 데이터

메트릭:
1. precision: 필터 통과 트윗 중 실제 AI/테크 관련 비율 (수동 라벨 대신 토픽 매칭률로 대체)
2. recall_proxy: 고정 테스트셋 426개 중 새 필터로 몇 개가 통과하는지
3. topic_coverage: 14개 토픽 중 최소 1개 매칭되는 비율
4. noise_ratio: 어떤 토픽에도 안 걸리는 트윗 비율 (낮을수록 좋음)

종합 점수 = recall_proxy * 0.4 + topic_coverage * 0.3 + (1 - noise_ratio) * 0.3
"""

import json
import re
import sys
import os

def load_test_data():
    base = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(base, "test_tweets.json"), "r", encoding="utf-8") as f:
        return json.load(f)

def load_target_config():
    base = os.path.dirname(os.path.abspath(__file__))
    target_path = os.path.join(base, "..", "target", "filter_config.json")
    with open(target_path, "r", encoding="utf-8") as f:
        return json.load(f)

def compile_pattern(keywords):
    return re.compile("|".join(keywords), re.IGNORECASE)

def evaluate():
    tweets = load_test_data()
    config = load_target_config()

    include_re = compile_pattern(config["include_keywords"])
    exclude_re = compile_pattern(config["exclude_keywords"])

    # 토픽 정의 (고정)
    topic_defs = [
        ("Claude/Anthropic", re.compile(r"claude|anthropic|sonnet|opus|haiku|mcp|cowork", re.I)),
        ("OpenAI/GPT/Codex", re.compile(r"openai|gpt|codex|chatgpt|o[13]|dall-?e|sora", re.I)),
        ("Google/Gemini", re.compile(r"google|gemini|deepmind|gemma", re.I)),
        ("AI Agent", re.compile(r"agent|agentic|autonomous|workflow|automat|crew|devin|browser.use", re.I)),
        ("바이브코딩", re.compile(r"vibe.?cod|cursor|copilot|windsurf|bolt|lovable|replit|trae|ide|coding", re.I)),
        ("LLM/모델", re.compile(r"llm|model|benchmark|inference|training|fine.?tun|rlhf|transformer|reasoning", re.I)),
        ("AI인프라/GPU", re.compile(r"gpu|nvidia|amd|tsmc|chip|semiconductor|cloud|aws|gcp|azure|infra", re.I)),
        ("오픈소스", re.compile(r"open.?source|oss|github|hugging.?face|llama|mistral|qwen|deepseek", re.I)),
        ("AI규제/사회", re.compile(r"regulat|law|legal|copyright|safety|alignment|agi|policy", re.I)),
        ("AI크리에이티브", re.compile(r"image|video|3d|generat|multimodal|vision|art|midjourney|voice|tts", re.I)),
        ("프론트엔드/웹", re.compile(r"react|next\.?js|vercel|frontend|backend|supabase|saas|tailwind|vite", re.I)),
        ("스타트업", re.compile(r"startup|funding|yc|unicorn|acquisition|ipo|venture|founder", re.I)),
        ("xAI/Grok", re.compile(r"xai|grok|elon", re.I)),
        ("Perplexity/검색AI", re.compile(r"perplexity|search|rag|embedding|vector|retrieval", re.I)),
    ]

    total = len(tweets)
    passed = 0
    topic_matched = 0
    topic_counts = {name: 0 for name, _ in topic_defs}
    no_topic = 0

    for tw in tweets:
        text = tw.get("t", "")

        # 제외 필터
        if exclude_re.search(text):
            continue

        # 포함 필터
        if not include_re.search(text):
            continue

        passed += 1

        # 토픽 매칭
        matched_any = False
        for name, pattern in topic_defs:
            if pattern.search(text):
                topic_counts[name] += 1
                matched_any = True

        if matched_any:
            topic_matched += 1
        else:
            no_topic += 1

    recall_proxy = passed / total if total > 0 else 0
    topic_coverage = topic_matched / passed if passed > 0 else 0
    noise_ratio = no_topic / passed if passed > 0 else 0

    # 토픽 다양성: 14개 중 몇 개에 트윗이 있는지
    active_topics = sum(1 for c in topic_counts.values() if c > 0)
    topic_diversity = active_topics / len(topic_defs)

    # 종합 점수
    score = recall_proxy * 0.35 + topic_coverage * 0.25 + (1 - noise_ratio) * 0.2 + topic_diversity * 0.2

    result = {
        "score": round(score, 4),
        "recall_proxy": round(recall_proxy, 4),
        "topic_coverage": round(topic_coverage, 4),
        "noise_ratio": round(noise_ratio, 4),
        "topic_diversity": round(topic_diversity, 4),
        "passed": passed,
        "total": total,
        "active_topics": active_topics,
        "topic_counts": topic_counts,
    }

    return result

if __name__ == "__main__":
    result = evaluate()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    print(f"\n=== SCORE: {result['score']} ===")
    print(f"Recall: {result['recall_proxy']} ({result['passed']}/{result['total']})")
    print(f"Topic Coverage: {result['topic_coverage']}")
    print(f"Noise Ratio: {result['noise_ratio']}")
    print(f"Topic Diversity: {result['topic_diversity']} ({result['active_topics']}/14)")
