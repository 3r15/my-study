/* 정처산기 학습 사이트 — 오프라인 캐시
   데이터를 바꾸면 아래 V 값을 올리면 됩니다. */
const V = "jbsg-v5";
const SHELL = ['./', 'index.html', 'data/index.json', 'data/summary.json'];

self.addEventListener('install', e => {
  e.waitUntil(caches.open(V).then(c => c.addAll(SHELL)).then(() => self.skipWaiting()));
});

self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys()
      .then(ks => Promise.all(ks.filter(k => k !== V).map(k => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', e => {
  const req = e.request;
  if (req.method !== 'GET' || new URL(req.url).origin !== location.origin) return;

  // 이미지: 한 번 받으면 안 바뀌므로 캐시 우선
  if (/\.(png|jpg|svg|webp)$/i.test(req.url)) {
    e.respondWith(
      caches.match(req).then(hit => hit || fetch(req).then(res => {
        const copy = res.clone();
        caches.open(V).then(c => c.put(req, copy));
        return res;
      }))
    );
    return;
  }

  // HTML·JSON: 캐시를 바로 보여주고 뒤에서 갱신 (stale-while-revalidate)
  e.respondWith(
    caches.match(req).then(hit => {
      const net = fetch(req).then(res => {
        if (res && res.ok) {
          const copy = res.clone();
          caches.open(V).then(c => c.put(req, copy));
        }
        return res;
      }).catch(() => hit);
      return hit || net;
    })
  );
});
