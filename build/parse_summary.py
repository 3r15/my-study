# -*- coding: utf-8 -*-
import re, os, json, pdfplumber
from parse_exam import page_elements, looks_code, CIRC_RE

SRC = "/sessions/relaxed-dreamy-brahmagupta/mnt/산업기사필기/핵심요약집_2026_정보처리산업기사핵심요약.pdf"
IMG = "/tmp/w/out/img"
os.makedirs(IMG, exist_ok=True)

NUM_RE = re.compile(r'^(\d{3})\b\s*(.*)$')
SUBJ_RE = re.compile(r'^([1-3])\s*과목\s+(.+)$')
JUNK = re.compile(r'^(정보처리산업기사|핵심 요약|초|치기|공부한다!|나오는 것만|시험에|\d{1,3}|)$')

def run():
    pdf = pdfplumber.open(SRC)
    els = []
    for i, pg in enumerate(pdf.pages):
        for e in page_elements(pg, i+1, IMG, "sum"):
            e['page'] = i+1
            els.append(e)
    els.sort(key=lambda e: (e['page'], e['col'], e['top']))

    secs = []
    cur = None
    subject = None
    state = None   # 'title' | 'body'
    pending = [None]
    expect = 1
    for e in els:
        if e['kind'] == 'text':
            t = e['text'].strip()
            if not t: continue
            sm = SUBJ_RE.match(t)
            if sm and e['size'] >= 14:
                subject = f"{sm.group(1)}과목 {sm.group(2).strip()}"; pending[0] = None
                continue
            if re.fullmatch(r'([1-3])\s*과목', t) and e['size'] >= 14:
                pending[0] = t[0]; continue
            if pending[0] and e['size'] >= 13 and len(t) < 30:
                subject = f"{pending[0]}과목 {t}"; pending[0] = None; continue
            nm = NUM_RE.match(t)
            if nm and ((expect <= int(nm.group(1)) <= expect + 3 and e['size'] >= 12)
                       or (int(nm.group(1)) == expect and e['size'] >= 6)):
                if cur: secs.append(cur)
                n = int(nm.group(1))
                cur = dict(no=n, subject=subject, title='', body=[], page=e['page'],
                           _pos=(e['page'], e['col'], e['top']))
                expect = n + 1
                state = 'title'
                rest = nm.group(2).strip()
                if rest: cur['title'] += ' ' + rest
                continue
            if cur is None: continue
            if state == 'title':
                cleaned = re.sub(r'^(초|치기)\s*', '', t)
                cleaned = re.sub(r'^(초|치기)\s*', '', cleaned).strip()
                base = 42.5 if e['col'] == 0 else 321.0
                if e['size'] <= 12.5 and e['x0'] > base + 35 and cleaned and not JUNK.fullmatch(t) \
                   and not BULLET.match(t):
                    if len(cur['title']) < 40:
                        cur['title'] += ' ' + cleaned
                        continue
                if JUNK.fullmatch(t): continue
                state = 'body'
            if JUNK.fullmatch(t) or re.fullmatch(r'정보처리산업기사|핵심 요약', t): continue
            add_text(cur, t, e)
        else:
            state = 'body'
            if cur is None:
                probe0 = ' '.join(sum(e['grid'], []) if e['kind'] == 'table' else [x or '' for x in e.get('lines', [])])
                sm0 = SUBJ_RE.match(probe0.strip())
                if sm0: subject = f"{sm0.group(1)}과목 {sm0.group(2).strip()}"
                continue
            probe = ' '.join(sum(e['grid'], []) if e['kind'] == 'table' else [x or '' for x in e.get('lines', [])])
            sm2 = SUBJ_RE.match(probe.strip())
            if sm2:
                subject = f"{sm2.group(1)}과목 {sm2.group(2).strip()}"
                continue
            if e['kind'] == 'table':
                cur['body'].append(dict(type='table', grid=e['grid']))
            elif e['kind'] == 'figure_img':
                cur['body'].append(dict(type='image', src=e['src'], w=e['w'], h=e['h']))
            else:
                ls = [x for x in e.get('lines', []) if x.strip()]
                if ls:
                    cur['body'].append(dict(type='code' if looks_code(ls) else 'note', lines=ls))
    if cur: secs.append(cur)
    render_sections(pdf, secs)
    for s in secs:
        s['title'] = re.sub(r'\s+', ' ', s['title']).strip()
        s['body'] = [b for b in s['body'] if b['type'] != 'text' or b['text'].strip()]
    return secs

GARBLE = re.compile(r'(\b\d+\s+){4,}|실행 시작|도착 대기|진행시간')
def render_sections(pdf, secs):
    for i, sec in enumerate(secs):
        pg_i, col, top = sec.pop('_pos')
        pg = pdf.pages[pg_i-1]
        bot = pg.height - 40
        if i+1 < len(secs):
            n_pg, n_col, n_top = secs[i+1]['_pos']
            if n_pg == pg_i and n_col == col: bot = n_top - 8
        x0 = 34 if col == 0 else 312
        x1 = 306 if col == 0 else 584
        if bot - top < 20: continue
        name = f"sec_{sec['no']:03d}.png"
        try:
            pg.crop((x0, max(60, top-6), x1, min(bot, pg.height-38))).to_image(resolution=150).save(os.path.join(IMG, name))
            sec['image'] = name
        except Exception:
            pass
        txt = ' '.join(b.get('text','') for b in sec['body'] if b['type'] == 'text')
        if GARBLE.search(txt): sec['garbled'] = True


BULLET = re.compile(r'^[•·ㆍ‣∙]')
DECO = re.compile(r'\s*초\s*시험에\s*치기\s*나오는 것만\s*(공부한다!)?\s*')
def add_text(cur, t, e):
    t = DECO.sub(' ', t).strip()
    if not t: return
    b = cur['body']
    if BULLET.match(t):
        b.append(dict(type='text', text=re.sub(r'^[•·ㆍ‣∙]\s*', '', t), bullet=True))
    elif b and b[-1]['type'] == 'text' and e['x0'] > 45 and (e['x0'] % 300) > 8:
        b[-1]['text'] += ' ' + t
    else:
        b.append(dict(type='text', text=t, bullet=False))

if __name__ == '__main__':
    secs = run()
    print("sections:", len(secs))
    import collections
    print(collections.Counter(s['subject'] for s in secs))
    print(collections.Counter(b['type'] for s in secs for b in s['body']))
    for s in secs[:4] + secs[-3:]:
        print(f"\n[{s['no']:03d}] {s['subject']} | {s['title']}")
        for b in s['body'][:4]:
            print("   ", b['type'], (b.get('text') or b.get('lines') or b.get('grid') or b.get('src'))[:80] if isinstance(b.get('text') or b.get('src'), str) else b.get('lines') or b.get('grid'))
    json.dump(secs, open('/tmp/w/out/summary.json','w'), ensure_ascii=False, indent=1)
