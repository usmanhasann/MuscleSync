const CACHE_NAME = 'ironsync-offline-v4';
const CORE_ASSETS = [
  './',
  './index.html',
  './exercises.json',
  './manifest.json',
  './icon.svg'
];
// Bundled public-domain exercise photos (images/ref/<id>-0.jpg start, -1.jpg end)
const REF_IDS = ["back-extension", "barbell-back-squat", "barbell-bent-over-row", "bayesian-cable-curl", "bulgarian-split-squat", "cable-chest-fly", "cable-face-pull", "cable-hip-abduction", "cable-kneeling-crunch", "cable-lateral-raise", "cable-overhead-curl", "cable-rope-pushdown", "cable-woodchopper", "chest-supported-row", "close-grip-bench", "concentration-curl", "db-lateral-raise", "db-shrug", "ez-skull-crusher", "flat-bb-bench-press", "glute-hip-thrust", "hack-squat-narrow", "hammer-curl", "hanging-leg-raise", "incline-db-curl", "incline-db-press", "leg-extension", "low-to-high-cable-fly", "lying-leg-curl", "overhead-cable-tricep-ext", "pec-deck-fly", "pendulum-sissy-squat", "preacher-curl", "pull-up", "reverse-ez-curl", "reverse-pec-deck", "romanian-deadlift", "seated-calf-raise", "seated-db-shoulder-press", "seated-leg-curl", "single-arm-cable-lat-row", "single-arm-reverse-pushdown", "spider-curl", "standing-calf-raise", "straight-arm-lat-pulldown", "tbar-row-cable-seated", "weighted-chest-dip", "wide-lat-pulldown"];
const REF_IMAGES = REF_IDS.flatMap((id) => [`./images/ref/${id}-0.jpg`, `./images/ref/${id}-1.jpg`]);

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => cache.addAll(CORE_ASSETS.map((u) => new Request(u, { cache: 'reload' })))
        // Photos are cached best-effort so one failed image never blocks the offline install
        .then(() => Promise.all(REF_IMAGES.map((u) => cache.add(u).catch(() => {})))))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k)))
    ).then(() => self.clients.claim())
  );
});

function putInCache(request, response) {
  if (response && response.status === 200 && response.type === 'basic') {
    const copy = response.clone();
    caches.open(CACHE_NAME).then((cache) => cache.put(request, copy));
  }
  return response;
}

self.addEventListener('fetch', (event) => {
  const req = event.request;
  if (req.method !== 'GET') return;
  if (req.url.includes('/api/')) return;
  if (!req.url.startsWith(self.location.origin)) return;

  // The app page: try the network first (so GitHub Pages updates arrive), fall back to cache offline.
  const isPage = req.mode === 'navigate' || /\/(index\.html)?$/.test(new URL(req.url).pathname);
  if (isPage) {
    event.respondWith(
      Promise.race([
        fetch(req).then((res) => putInCache(req, res)),
        new Promise((_, reject) => setTimeout(() => reject(new Error('timeout')), 3500))
      ]).catch(() =>
        caches.match(req).then((c) => c || caches.match('./index.html'))
      )
    );
    return;
  }

  // Everything else: cache first, then network.
  event.respondWith(
    caches.match(req).then((cached) => {
      if (cached) return cached;
      return fetch(req)
        .then((res) => putInCache(req, res))
        .catch(() => caches.match('./index.html'));
    })
  );
});
