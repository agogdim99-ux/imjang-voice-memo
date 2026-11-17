# 항목 추출 정확도

정답표: `data/ground_truth.json` (매물 5건 × 15항목 = 75칸). 녹음에 없는 항목은 '확인 필요'로 비워야 정답.

| 결과 파일 | 추출 | 받아쓰기 입력 | 정확도 | 누락 표시(확인 필요) 정확도 | 1건 평균 처리 시간 |
|---|---|---|---|---|---|
| extracted_rules_scripts.json | 규칙 기반 | `data/scripts.json` | **74/75 (99%)** | 17/17 | 0.0초 |
| extracted_rules_small_clean_noprompt.json | 규칙 기반 | `data/transcripts/small_clean_noprompt.json` | **64/75 (85%)** | 17/17 | 3.2초 |
| extracted_rules_small_clean_prompt.json | 규칙 기반 | `data/transcripts/small_clean_prompt.json` | **69/75 (92%)** | 17/17 | 2.8초 |
| extracted_rules_small_noisy_noprompt.json | 규칙 기반 | `data/transcripts/small_noisy_noprompt.json` | **63/75 (84%)** | 17/17 | 2.8초 |
| extracted_rules_small_noisy_prompt.json | 규칙 기반 | `data/transcripts/small_noisy_prompt.json` | **67/75 (89%)** | 17/17 | 2.7초 |
| extracted_rules_turbo_clean_noprompt.json | 규칙 기반 | `data/transcripts/turbo_clean_noprompt.json` | **69/75 (92%)** | 17/17 | 1.8초 |
| extracted_rules_turbo_clean_prompt.json | 규칙 기반 | `data/transcripts/turbo_clean_prompt.json` | **73/75 (97%)** | 17/17 | 1.6초 |
| extracted_rules_turbo_noisy_noprompt.json | 규칙 기반 | `data/transcripts/turbo_noisy_noprompt.json` | **68/75 (91%)** | 17/17 | 2.0초 |
| extracted_rules_turbo_noisy_prompt.json | 규칙 기반 | `data/transcripts/turbo_noisy_prompt.json` | **73/75 (97%)** | 17/17 | 1.7초 |

## 틀린 칸 — extracted_rules_scripts.json

| 매물 | 항목 | 정답 | 추출값 |
|---|---|---|---|
| s5 | 전세가 | 36000 | 38000 |

## 틀린 칸 — extracted_rules_small_clean_noprompt.json

| 매물 | 항목 | 정답 | 추출값 |
|---|---|---|---|
| s1 | 매매가 | 72000 | None |
| s1 | 연식 | 2008 | None |
| s1 | 역 도보(분) | 8 | None |
| s1 | 초품아 | True | None |
| s1 | 융자 유무 | False | None |
| s3 | 매매가 | 28000 | None |
| s4 | 평형 | 27 | None |
| s5 | 매매가 | 99000 | None |
| s5 | 전세가 | 36000 | 38000 |
| s5 | 연식 | 1995 | None |
| s5 | 융자 유무 | True | None |

## 틀린 칸 — extracted_rules_small_clean_prompt.json

| 매물 | 항목 | 정답 | 추출값 |
|---|---|---|---|
| s1 | 평형 | 24 | None |
| s1 | 연식 | 2008 | None |
| s1 | 역 도보(분) | 8 | None |
| s4 | 평형 | 27 | None |
| s5 | 전세가 | 36000 | 38000 |
| s5 | 연식 | 1995 | None |

## 틀린 칸 — extracted_rules_small_noisy_noprompt.json

| 매물 | 항목 | 정답 | 추출값 |
|---|---|---|---|
| s1 | 동 | 당산동 | 방산동 |
| s1 | 매매가 | 72000 | None |
| s1 | 연식 | 2008 | None |
| s1 | 역 도보(분) | 8 | None |
| s1 | 초품아 | True | None |
| s1 | 융자 유무 | False | True |
| s3 | 매매가 | 28000 | None |
| s4 | 평형 | 27 | None |
| s5 | 매매가 | 99000 | None |
| s5 | 전세가 | 36000 | 38000 |
| s5 | 연식 | 1995 | None |
| s5 | 융자 유무 | True | None |

## 틀린 칸 — extracted_rules_small_noisy_prompt.json

| 매물 | 항목 | 정답 | 추출값 |
|---|---|---|---|
| s1 | 동 | 당산동 | 방산동 |
| s1 | 평형 | 24 | None |
| s1 | 연식 | 2008 | None |
| s1 | 역 도보(분) | 8 | None |
| s1 | 융자 유무 | False | True |
| s4 | 평형 | 27 | None |
| s5 | 전세가 | 36000 | 38000 |
| s5 | 연식 | 1995 | None |

## 틀린 칸 — extracted_rules_turbo_clean_noprompt.json

| 매물 | 항목 | 정답 | 추출값 |
|---|---|---|---|
| s1 | 주차(1대 기준) | 1대 이상 | None |
| s1 | 초품아 | True | None |
| s2 | 주차(1대 기준) | 1대 이상 | None |
| s3 | 주차(1대 기준) | 1대 미만 | None |
| s4 | 평형 | 27 | None |
| s5 | 전세가 | 36000 | 38000 |

## 틀린 칸 — extracted_rules_turbo_clean_prompt.json

| 매물 | 항목 | 정답 | 추출값 |
|---|---|---|---|
| s4 | 평형 | 27 | None |
| s5 | 전세가 | 36000 | 38000 |

## 틀린 칸 — extracted_rules_turbo_noisy_noprompt.json

| 매물 | 항목 | 정답 | 추출값 |
|---|---|---|---|
| s1 | 주차(1대 기준) | 1대 이상 | None |
| s1 | 초품아 | True | None |
| s2 | 주차(1대 기준) | 1대 이상 | None |
| s3 | 주차(1대 기준) | 1대 미만 | None |
| s4 | 평형 | 27 | None |
| s5 | 전세가 | 36000 | 38000 |
| s5 | 엘리베이터 | True | None |

## 틀린 칸 — extracted_rules_turbo_noisy_prompt.json

| 매물 | 항목 | 정답 | 추출값 |
|---|---|---|---|
| s4 | 평형 | 27 | None |
| s5 | 전세가 | 36000 | 38000 |