# 빌드 스크립트

PDF → JSON 변환 파이프라인. 문제은행을 다시 만들거나 회차를 추가할 때 씁니다.

## 필요 패키지
```bash
pip install pdfplumber --break-system-packages
```

## 실행 순서
```bash
python parse_exam.py      # 기출 PDF → out/YYYY-N.json  (+ out/img/ 크롭 이미지)
python parse_summary.py   # 핵심요약집 PDF → out/summary.json
python build_data.py      # 위 결과 → site/data/*.json + site/img/  (태깅·용어사전 포함)
```

각 스크립트 상단의 경로 상수를 실제 PDF 위치로 맞춰 주세요.

## 회차 추가하기
`parse_exam.py` 맨 아래 파일 필터를 고칩니다.
```python
files = [f for f in files if re.search(r'(2022|2023|2024|2025)년', os.path.basename(f))]
```
2005~2021년 구 체계는 5과목 100문항이라 `SUBJ_CANON`(과목명)과 `UNITS`(단원 범위, `build_data.py`)도 함께 손봐야 합니다.

## 파서가 하는 일
- **2단 조판 분리** — 페이지를 x=297 기준으로 좌/우 컬럼으로 나눠 읽기 순서 복원
- **영역 인식** — 선분/사각형에서 닫힌 박스를 찾아 표(다중 셀) / 보기 박스 / 코드 블록으로 분류
- **그림 크롭** — 텍스트 사이 28pt 이상 빈 공간에 도형·이미지가 있으면 해당 영역만 PNG로 잘라냄 (워터마크 제외)
- **선택지가 그림인 문항** — 선택지 영역을 통째로 크롭
- **문항 분할** — 번호가 `expect`와 정확히 일치할 때만 새 문항으로 인정 (박스 안 숫자에 속지 않음)
- **정답 파싱** — 마지막 "정답" 페이지에서 `1.② 2.④ …` 추출

검증: 12회차 × 60문항 = 720, 정답 720/720, 보기 4개 미달 0건.
