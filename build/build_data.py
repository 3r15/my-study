# -*- coding: utf-8 -*-
import json, re, os, glob, collections, math, shutil

OUT = "/tmp/w/site"
os.makedirs(OUT + "/data", exist_ok=True)
os.makedirs(OUT + "/img", exist_ok=True)

UNITS = [
    ("1", "운영체제", 1, 23), ("1", "네트워크·데이터통신", 24, 34),
    ("1", "소프트웨어 공학", 35, 45), ("1", "객체지향·디자인 패턴", 46, 55),
    ("1", "테스트·UI·형상관리", 56, 66),
    ("2", "C 기초·연산자", 67, 76), ("2", "입·출력 함수", 77, 83),
    ("2", "제어문·배열·포인터", 84, 94), ("2", "Python", 95, 101),
    ("2", "HTML·JavaScript", 102, 108), ("2", "객체지향·스크립트 언어", 109, 117),
    ("2", "모듈·결합도·응집도", 118, 121), ("2", "보안·API", 122, 124),
    ("3", "자료구조", 125, 141), ("3", "DB 설계·데이터 모델", 142, 150),
    ("3", "키·무결성", 151, 157), ("3", "관계대수·관계해석", 158, 165),
    ("3", "정규화", 166, 170), ("3", "뷰·카탈로그·트랜잭션", 171, 174),
    ("3", "SQL", 175, 189), ("3", "기타(프로시저·옵티마이저)", 190, 193),
]
def unit_of(no):
    for s, name, a, b in UNITS:
        if a <= no <= b: return name
    return "기타"

STOP = set("""것은 것이 대한 설명 다음 옳지 않은 틀린 옳은 대하여 관한 사용 하는 하기 위해 있는 있다 이다 위한 경우 모두 아닌 해당 中
가장 무엇 어떤 종류 기법 방법 방식 기능 특징 내용 결과 실행 사용되는 나열 순서 올바른 알맞은 짝지어진 의미 관련 구성 요소 이용
및 등 수 것 그 이 저 때 중 로 를 은 는 가 의 에 와 과 함 시 후 전 하 로서 에서 으로 하여 하고 이며 하며 되는 된 될 한 할 함으로""".split())

def terms(s):
    out = []
    for m in re.finditer(r'[A-Za-z][A-Za-z0-9_+.#\-]{1,}', s):
        w = m.group(0)
        if len(w) >= 2: out.append(w.lower())
    for m in re.finditer(r'[가-힣]{2,}', s):
        w = m.group(0)
        if w in STOP: continue
        out.append(w)
        if len(w) >= 4:
            for i in range(len(w)-1):
                sub = w[i:i+2]
                if sub not in STOP: out.append(sub)
    return out

DECO2 = re.compile(r'\s*초\s*시험에\s*치기\s*나오는\s*것만\s*(공부한다!?)?\s*|\s*나오는 것만\s*공부한다!?\s*|\s*초\s*치기\s*')
def clean(t):
    t = DECO2.sub(' ', t)
    return re.sub(r'\s+', ' ', t).strip()


def flat(blocks):
    parts = []
    for b in blocks:
        if b['type'] == 'text': parts.append(b['text'])
        elif b['type'] in ('code', 'note'): parts.append(' '.join(b.get('lines', [])))
        elif b['type'] == 'table': parts.append(' '.join(' '.join(r) for r in b['grid']))
    return ' '.join(parts)

# ---------- sections ----------
secs = json.load(open('/tmp/w/out/summary.json'))
MANUAL = {
 8: dict(title="스케줄링 - FCFS(FIFO)", body=[
   dict(type='text', text="준비상태 큐에 도착한 순서에 따라 차례로 CPU를 할당하는 기법이다.", bullet=True),
   dict(type='text', text="가장 간단한 비선점(Non-preemptive) 스케줄링 기법이다.", bullet=True),
   dict(type='text', text="평균 반환 시간 = (각 프로세스의 완료시간 합) / 프로세스 수, 평균 대기 시간 = (각 프로세스의 대기시간 합) / 프로세스 수", bullet=True)]),
 9: dict(title="스케줄링 - SJF(Shortest Job First)", subject="1과목 정보시스템 기반 기술",
   body=[dict(type='text', text="실행 시간이 가장 짧은 프로세스에게 먼저 CPU를 할당하는 기법이다.", bullet=True),
         dict(type='text', text="비선점 기법으로, 평균 대기 시간을 최소화한다.", bullet=True),
         dict(type='text', text="실행 시간이 긴 작업은 무한 연기(기아) 상태가 발생할 수 있다.", bullet=True)], page=2),
}
byno = {s['no']: s for s in secs}
for no, patch in MANUAL.items():
    if no in byno:
        byno[no].update({k: v for k, v in patch.items() if k != 'subject'})
        byno[no].pop('garbled', None)
    else:
        base = dict(no=no, subject=patch.get('subject'), title=patch['title'], body=patch['body'],
                    page=patch.get('page', 1), image=f"sec_{no:03d}.png" if os.path.exists(f"/tmp/w/out/img/sec_{no:03d}.png") else None)
        secs.append(base)
secs.sort(key=lambda s: s['no'])
TITLE_FIX = {103: 'HTML - 테이블의 주요 태그'}
for s in secs:
    s['title'] = TITLE_FIX.get(s['no'], clean(s['title']))
    for b in s['body']:
        if b['type'] == 'text': b['text'] = clean(b['text'])
        elif b['type'] in ('code', 'note'): b['lines'] = [clean(x) if b['type'] == 'note' else x for x in b['lines']]
    s['body'] = [b for b in s['body'] if b['type'] != 'text' or b['text']]
    s['unit'] = unit_of(s['no'])
    s['subjectNo'] = int((s['subject'] or '1')[0])
    if not s.get('image'): s.pop('image', None)

# section keyword vectors
sec_vec = {}
for s in secs:
    c = collections.Counter()
    for t in terms(s['title']): c[t] += 4
    for t in terms(flat(s['body'])): c[t] += 1
    sec_vec[s['no']] = c
df = collections.Counter()
for c in sec_vec.values():
    for t in c: df[t] += 1
N = len(sec_vec)
idf = {t: math.log(1 + N / (1 + d)) for t, d in df.items()}

# ---------- questions ----------
exams = []
allq = []
for f in sorted(glob.glob('/tmp/w/out/*.json')):
    if 'summary' in f: continue
    d = json.load(open(f))
    for q in d['questions']:
        q['exam'] = d['id']
        q['qid'] = f"{d['id']}-{q['no']:02d}"
        q['subjectNo'] = int(re.search(r'제(\d)과목', q['subject']).group(1))
        txt = flat(q['stem']) + ' ' + ' '.join(o['text'] for o in q['options'])
        qc = collections.Counter(terms(txt))
        scores = []
        for s in secs:
            v = sec_vec[s['no']]
            sc = sum(min(qc[t], 3) * v[t] * idf.get(t, 0) for t in qc if t in v)
            if s['subjectNo'] == q['subjectNo']: sc *= 1.6
            if sc > 0: scores.append((sc, s['no']))
        scores.sort(reverse=True)
        top = [n for _, n in scores[:3]]
        q['refs'] = top
        q['unit'] = unit_of(top[0]) if top else '기타'
        # per-option concept refs: what concept does this choice involve?
        for o in q['options']:
            oc = collections.Counter(terms(o['text']))
            osc = []
            for s2 in secs:
                v2 = sec_vec[s2['no']]
                sc2 = sum(min(oc[t], 2) * v2[t] * idf.get(t, 0) for t in oc if t in v2)
                if s2['subjectNo'] == q['subjectNo']: sc2 *= 1.6
                if sc2 > 0: osc.append((sc2, s2['no']))
            osc.sort(reverse=True)
            o['refs'] = [n for _, n in osc[:2]] or top[:1]
        allq.append(q)
    exams.append(dict(id=d['id'], year=d['year'], session=d['session'], title=d['title'], count=len(d['questions'])))
    json.dump(d, open(f"{OUT}/data/exam-{d['id']}.json", 'w'), ensure_ascii=False, separators=(',', ':'))

# reverse index: section -> question ids
rev = collections.defaultdict(list)
for q in allq:
    for n in q['refs']: rev[n].append(q['qid'])
for s in secs:
    s['qids'] = rev.get(s['no'], [])[:40]

exams.sort(key=lambda e: (-e['year'], -e['session']))
json.dump(dict(exams=exams, units=[dict(subject=int(s), name=n, from_=a, to=b) for s, n, a, b in UNITS]),
          open(f"{OUT}/data/index.json", 'w'), ensure_ascii=False, separators=(',', ':'))


json.dump(secs, open(f"{OUT}/data/summary.json", 'w'), ensure_ascii=False, separators=(',', ':'))

# glossary: 용어(영문) 패턴 추출
BAD_TERM = set("""종류 정의 기호 예제 특징 구성 장점 단점 단계 방법 방식 기능 목적 개요 원칙 순서 과정 유형 조건 요소 항목 종속
결과 내용 사용 표기 표현 형식 참고 주의 비고 기타 초기 상태 회전 문법 규칙 처리 관리 설정 지정 출력 입력 저장 삭제 수정 검색
값 수 등 및 그 이 저 것 예 참 거짓 위치 크기 범위 시간 공간 이름 번호 개수 최대 최소 평균 합계 전체 부분 일부 대상 기준 단위""".split())
def good_term(k):
    k = k.strip()
    if len(k) < 2 or len(k) > 40: return False
    if k in BAD_TERM: return False
    core = re.sub(r'\(.*?\)', '', k).strip()
    if core in BAD_TERM or not core: return False
    if re.search(r'[A-Za-z]{2,}', k): return True
    return len(core) >= 3 and not re.fullmatch(r'[0-9가-힣]{1,3}', core)

gloss = {}
for s in secs:
    for b in s['body']:
        t = b.get('text', '')
        for m in re.finditer(r'([가-힣A-Za-z0-9 ]{2,30}?\([A-Za-z][A-Za-z0-9 \-/.]{1,40}\))\s*[:：]\s*(.+?)(?=$)', t):
            k = m.group(1).strip(); v = m.group(2).strip()
            v = clean(v)
            if 3 < len(v) < 220 and k not in gloss and good_term(k) and not re.search(r'(,\s*[A-Z]\b){3,}', v):
                gloss[k] = dict(term=k, desc=v, sec=s['no'], subject=s['subjectNo'], unit=s['unit'])
        for m in re.finditer(r'^([가-힣A-Za-z0-9 ()\-]{2,30}?)\s*[:：]\s*(.{5,300})$', t):
            k = m.group(1).strip(); v = m.group(2).strip()
            k = clean(k); v = clean(v)
            if k and len(v) < 220 and k not in gloss and good_term(k) and not re.search(r'(,\s*[A-Z]\b){3,}', v):
                gloss[k] = dict(term=k, desc=v, sec=s['no'], subject=s['subjectNo'], unit=s['unit'])
json.dump(sorted(gloss.values(), key=lambda g: g['term']), open(f"{OUT}/data/glossary.json", 'w'),
          ensure_ascii=False, separators=(',', ':'))

# images
used = set()
for q in allq:
    for b in q['stem']:
        if b['type'] == 'image': used.add(b['src'])
    if q.get('optionsImage'): used.add(q['optionsImage'])
for s in secs:
    if s.get('image'): used.add(s['image'])
    for b in s['body']:
        if b['type'] == 'image': used.add(b['src'])
for n in used:
    p = f"/tmp/w/out/img/{n}"
    if os.path.exists(p): shutil.copy(p, f"{OUT}/img/{n}")

print("exams", len(exams), "questions", len(allq), "sections", len(secs), "glossary", len(gloss), "images", len(used))
print("unit dist:", collections.Counter(q['unit'] for q in allq).most_common())
print("no refs:", sum(1 for q in allq if not q['refs']))
