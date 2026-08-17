#!/usr/bin/env python3
"""bank1~3.json → data/mock-bank.json

모의고사에 쓰는 직접 제작 문항을 하나로 합치고 검증한다.
`sec`(핵심요약 항목 번호)로 과목·단원·항목 제목을 채워 넣으므로
원본에는 그 세 값을 적지 않는다.
"""
import json, os, sys, collections

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'data')

summary = json.load(open(os.path.join(ROOT, 'data', 'summary.json'), encoding='utf-8'))
sec = {s['no']: s for s in summary}

qs = []
for name in ['bank1.json', 'bank2.json', 'bank3.json']:
    qs += json.load(open(os.path.join(HERE, name), encoding='utf-8'))

bad, ids = [], set()
for q in qs:
    # notes 는 원본에서 misread 로 적혀 있어도 받아 준다
    if 'notes' not in q and 'misread' in q:
        q['notes'] = q.pop('misread')
    checks = [
        (q['id'] in ids, '중복 id'),
        (len(q['options']) != 4, '보기가 4개가 아님'),
        (len(set(q['options'])) != 4, '보기 문구 중복'),
        (not (1 <= q['answer'] <= 4), 'answer 가 1~4 범위 밖'),
        (len(q.get('notes', [])) != 4, 'notes 가 4개가 아님'),
        (q['sec'] not in sec, 'sec=%s 인 요약 항목이 없음' % q['sec']),
        (not q.get('why', '').strip(), 'why 없음'),
        (not any(n.strip() for n in q.get('notes', [])), '보기 설명이 하나도 없음'),
    ]
    for cond, msg in checks:
        if cond:
            bad.append('%s : %s' % (q['id'], msg))
    ids.add(q['id'])
    if q['sec'] in sec:
        s = sec[q['sec']]
        # 정답 위치에 설명이 있으면 "옳지 않은 것은?" 유형이다
        q['neg'] = 1 if q['notes'][q['answer'] - 1].strip() else 0
        q['subjectNo'] = s['subjectNo']
        q['unit'] = s['unit']
        q['secTitle'] = s['title']

if bad:
    print('검증 실패 %d건' % len(bad))
    for b in bad:
        print(' -', b)
    sys.exit(1)

json.dump({'meta': {'n': len(qs),
                    'src': '직접 제작 — 요약집 193항목과 12회차 기출 출제 경향을 근거로 새로 작성'},
           'questions': qs},
          open(os.path.join(OUT, 'mock-bank.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, separators=(',', ':'))

subj = collections.Counter(q['subjectNo'] for q in qs)
print('문항 %d · 과목별 %s · 부정형 %d · 코드 포함 %d · 서로 다른 개념 %d'
      % (len(qs), dict(sorted(subj.items())), sum(q['neg'] for q in qs),
         sum(1 for q in qs if q.get('code')), len({q['sec'] for q in qs})))
