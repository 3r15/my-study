#!/usr/bin/env python3
"""card1~3.json → data/memo-cards.json

자주 틀리는 개념을 시각 자료와 예시로 정리한 암기 카드를 합치고 검증한다.
`secs` 에 적힌 핵심요약 항목 번호로 앱이 "내 취약 개념"과 카드를 이어 붙인다.
"""
import json, os, sys, collections

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'data')

VIS = {'table', 'scale', 'layers', 'steps', 'calc', 'code', 'tree', 'note'}

summary = json.load(open(os.path.join(ROOT, 'data', 'summary.json'), encoding='utf-8'))
sec = {s['no']: s for s in summary}

cards = []
for name in ['card1.json', 'card2.json', 'card3.json']:
    cards += json.load(open(os.path.join(HERE, name), encoding='utf-8'))

bad, ids, seen = [], set(), {}
for c in cards:
    if c['id'] in ids:
        bad.append('%s : 중복 id' % c['id'])
    ids.add(c['id'])
    if not c.get('key', '').strip():
        bad.append('%s : key 없음' % c['id'])
    if not c.get('visuals'):
        bad.append('%s : 시각 자료 없음' % c['id'])
    for v in c.get('visuals', []):
        if v.get('type') not in VIS:
            bad.append('%s : 모르는 시각 자료 type=%s' % (c['id'], v.get('type')))
        if v.get('type') == 'table' and not v.get('rows'):
            bad.append('%s : table 에 rows 없음' % c['id'])
        if v.get('type') == 'tree':
            nid = {n['id'] for n in v.get('nodes', [])}
            for a, b in v.get('edges', []):
                if a not in nid or b not in nid:
                    bad.append('%s : tree 간선이 없는 노드를 가리킴 (%s-%s)' % (c['id'], a, b))
    for n in c['secs']:
        if n not in sec:
            bad.append('%s : sec=%s 인 요약 항목이 없음' % (c['id'], n))
        elif n in seen:
            bad.append('%s : sec=%s 를 %s 와 중복으로 다룸' % (c['id'], n, seen[n]))
        else:
            seen[n] = c['id']
    # 과목은 첫 sec 에서 채운다
    if c['secs'] and c['secs'][0] in sec:
        c['subjectNo'] = sec[c['secs'][0]]['subjectNo']
        c['unit'] = sec[c['secs'][0]]['unit']

if bad:
    print('검증 실패 %d건' % len(bad))
    for b in bad:
        print(' -', b)
    sys.exit(1)

json.dump({'meta': {'n': len(cards), 'covers': len(seen),
                    'src': '오답 선택지로 자주 쓰인 개념을 골라 시각 자료·예시와 함께 정리'},
           'cards': cards},
          open(os.path.join(OUT, 'memo-cards.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, separators=(',', ':'))

vt = collections.Counter(v['type'] for c in cards for v in c['visuals'])
print('카드 %d개 · 요약 항목 %d개 연결 · 과목별 %s'
      % (len(cards), len(seen),
         dict(sorted(collections.Counter(c['subjectNo'] for c in cards).items()))))
print('시각 자료', dict(vt))
