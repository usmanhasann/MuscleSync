const CACHE_NAME = 'ironsync-offline-v8';
const CORE_ASSETS = [
  './',
  './index.html',
  './exercises.json',
  './channels.json',
  './parts.json',
  './manifest.json',
  './icon.svg'
];
// Bundled public-domain exercise photos (images/ref/<id>-0.jpg start, -1.jpg end)
const REF_IDS = ["back-extension", "barbell-back-squat", "barbell-bent-over-row", "bayesian-cable-curl", "bulgarian-split-squat", "cable-chest-fly", "cable-face-pull", "cable-hip-abduction", "cable-kneeling-crunch", "cable-lateral-raise", "cable-overhead-curl", "cable-rope-pushdown", "cable-woodchopper", "chest-supported-row", "close-grip-bench", "concentration-curl", "db-lateral-raise", "db-shrug", "ez-skull-crusher", "flat-bb-bench-press", "glute-hip-thrust", "hack-squat-narrow", "hammer-curl", "hanging-leg-raise", "incline-db-curl", "incline-db-press", "leg-extension", "low-to-high-cable-fly", "lying-leg-curl", "overhead-cable-tricep-ext", "pec-deck-fly", "pendulum-sissy-squat", "preacher-curl", "pull-up", "reverse-ez-curl", "reverse-pec-deck", "romanian-deadlift", "seated-calf-raise", "seated-db-shoulder-press", "seated-leg-curl", "single-arm-cable-lat-row", "single-arm-reverse-pushdown", "spider-curl", "standing-calf-raise", "straight-arm-lat-pulldown", "tbar-row-cable-seated", "weighted-chest-dip", "wide-lat-pulldown"];
const REF_IMAGES = REF_IDS.flatMap((id) => [`./images/ref/${id}-0.jpg`, `./images/ref/${id}-1.jpg`])
  // No-machine alternative photos (images/alt/)
  .concat(["./images/alt/bench-dips-0.jpg", "./images/alt/bench-dips-1.jpg", "./images/alt/bent-over-dumbbell-rear-delt-raise-with-head-on-bench-0.jpg", "./images/alt/bent-over-dumbbell-rear-delt-raise-with-head-on-bench-1.jpg", "./images/alt/bent-over-two-dumbbell-row-0.jpg", "./images/alt/bent-over-two-dumbbell-row-1.jpg", "./images/alt/decline-dumbbell-bench-press-0.jpg", "./images/alt/decline-dumbbell-bench-press-1.jpg", "./images/alt/decline-dumbbell-flyes-0.jpg", "./images/alt/decline-dumbbell-flyes-1.jpg", "./images/alt/dumbbell-bench-press-0.jpg", "./images/alt/dumbbell-bench-press-1.jpg", "./images/alt/dumbbell-flyes-0.jpg", "./images/alt/dumbbell-flyes-1.jpg", "./images/alt/dumbbell-incline-row-0.jpg", "./images/alt/dumbbell-incline-row-1.jpg", "./images/alt/dumbbell-prone-incline-curl-0.jpg", "./images/alt/dumbbell-prone-incline-curl-1.jpg", "./images/alt/dumbbell-seated-one-leg-calf-raise-0.jpg", "./images/alt/dumbbell-seated-one-leg-calf-raise-1.jpg", "./images/alt/dumbbell-side-bend-0.jpg", "./images/alt/dumbbell-side-bend-1.jpg", "./images/alt/dumbbell-squat-0.jpg", "./images/alt/dumbbell-squat-1.jpg", "./images/alt/flat-bench-lying-leg-raise-0.jpg", "./images/alt/flat-bench-lying-leg-raise-1.jpg", "./images/alt/front-plate-raise-0.jpg", "./images/alt/front-plate-raise-1.jpg", "./images/alt/goblet-squat-0.jpg", "./images/alt/goblet-squat-1.jpg", "./images/alt/hyperextensions-with-no-hyperextension-bench-0.jpg", "./images/alt/hyperextensions-with-no-hyperextension-bench-1.jpg", "./images/alt/incline-dumbbell-flyes-0.jpg", "./images/alt/incline-dumbbell-flyes-1.jpg", "./images/alt/natural-glute-ham-raise-0.jpg", "./images/alt/natural-glute-ham-raise-1.jpg", "./images/alt/one-arm-dumbbell-row-0.jpg", "./images/alt/one-arm-dumbbell-row-1.jpg", "./images/alt/one-arm-side-laterals-0.jpg", "./images/alt/one-arm-side-laterals-1.jpg", "./images/alt/push-ups-close-triceps-position-0.jpg", "./images/alt/push-ups-close-triceps-position-1.jpg", "./images/alt/reverse-crunch-0.jpg", "./images/alt/reverse-crunch-1.jpg", "./images/alt/reverse-flyes-with-external-rotation-0.jpg", "./images/alt/reverse-flyes-with-external-rotation-1.jpg", "./images/alt/russian-twist-0.jpg", "./images/alt/russian-twist-1.jpg", "./images/alt/seated-bent-over-rear-delt-raise-0.jpg", "./images/alt/seated-bent-over-rear-delt-raise-1.jpg", "./images/alt/seated-triceps-press-0.jpg", "./images/alt/seated-triceps-press-1.jpg", "./images/alt/side-leg-raises-0.jpg", "./images/alt/side-leg-raises-1.jpg", "./images/alt/single-leg-glute-bridge-0.jpg", "./images/alt/single-leg-glute-bridge-1.jpg", "./images/alt/standing-dumbbell-calf-raise-0.jpg", "./images/alt/standing-dumbbell-calf-raise-1.jpg", "./images/alt/stiff-legged-dumbbell-deadlift-0.jpg", "./images/alt/stiff-legged-dumbbell-deadlift-1.jpg", "./images/alt/straight-arm-dumbbell-pullover-0.jpg", "./images/alt/straight-arm-dumbbell-pullover-1.jpg", "./images/alt/superman-0.jpg", "./images/alt/superman-1.jpg", "./images/alt/svend-press-0.jpg", "./images/alt/svend-press-1.jpg", "./images/alt/tate-press-0.jpg", "./images/alt/tate-press-1.jpg", "./images/alt/tricep-dumbbell-kickback-0.jpg", "./images/alt/tricep-dumbbell-kickback-1.jpg", "./images/alt/weighted-crunches-0.jpg", "./images/alt/weighted-crunches-1.jpg", "./images/alt/weighted-sissy-squat-0.jpg", "./images/alt/weighted-sissy-squat-1.jpg"]);

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => cache.addAll(CORE_ASSETS.map((u) => new Request(u, { cache: 'reload' })))
        // Photos are cached best-effort so one failed image never blocks the offline install
        .then(() => Promise.all(REF_IMAGES.map((u) => cache.add(u).catch(() => {}))))
        // Real muscle photos listed in parts.json (added on the Mac and pushed)
        .then(() => fetch('./parts.json', { cache: 'reload' }).then((r) => r.json()).then((d) => Promise.all((d.images || []).map((e) => cache.add('./' + e.file).catch(() => {}))))).catch(() => {}))
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
  // channels.json is treated like the page so newly pushed channels show up right away.
  const isPage = req.mode === 'navigate' || /\/(index\.html|channels\.json|parts\.json)?$/.test(new URL(req.url).pathname);
  if (isPage) {
    event.respondWith(
      Promise.race([
        fetch(req).then((res) => putInCache(req, res)),
        new Promise((_, reject) => setTimeout(() => reject(new Error('timeout')), 3500))
      ]).catch(() =>
        caches.match(req).then((c) => c || (/(channels|parts)\.json$/.test(req.url) ? new Response(req.url.endsWith('parts.json') ? '{"images":[]}' : '{"channels":[]}', { headers: { 'Content-Type': 'application/json' } }) : caches.match('./index.html')))
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
