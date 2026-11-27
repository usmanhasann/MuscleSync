# IronSync — Offline Muscle & Form Planner

A minimal, zero-landing-page, offline-first gym planner built for iPhone 14, Android, and desktop.

## Files
- [index.html](file:///Users/sam/Downloads/gym%20go/index.html) — Self-contained offline app (works even if opened directly as a single file).
- [exercises.json](file:///Users/sam/Downloads/gym%20go/exercises.json) — Clean JSON copy of the exercise database.
- [manifest.json](file:///Users/sam/Downloads/gym%20go/manifest.json) & [sw.js](file:///Users/sam/Downloads/gym%20go/sw.js) — PWA support for Home Screen installation and permanent offline caching.
- [icon.svg](file:///Users/sam/Downloads/gym%20go/icon.svg) — App icon.

## How to Use Offline on iPhone 14 or Android
1. **Option A — Home Screen App (Best Experience on iPhone 14 / Android):**
   - Host the folder on GitHub Pages / Netlify, or open once on your local Wi-Fi (`python3 -m http.server 8080` on Mac and visit `http://<your-mac-ip>:8080` on your phone).
   - On **iPhone 14 (Safari)**: Tap **Share → Add to Home Screen**.
   - On **Android (Chrome)**: Tap **Menu (⋮) → Install App / Add to Home Screen**.
   - Once opened once, the Service Worker caches everything so it launches **100% offline** in the gym forever.
2. **Option B — Single File:**
   - Send `index.html` to your phone and open it directly in a browser/HTML viewer — all muscle maps, smart sync logic, and animated angle/ROM guides are embedded directly inside `index.html`.
3. **Option C — Export PDF Handout:**
   - Tap **PDF** in the top bar anytime to save/print Today's Synced Session as a clean PDF.

## Reading the app
- **Every muscle has its own colour.** Each exercise card shows a mini body map plus a strip of that muscle's parts:
  **● main target**, **◐ assists**, **○ not trained** (crossed out). For example, Incline DB Press shows ● Upper Chest · ◐ Mid Chest · ○ Lower Chest.
- **Today** tab: the ring counts only parts that are a *main* target. Untrained parts pulse orange on the body map, and assist-only parts are flagged. Tap **+ Add** to fix either.
- **Muscles** tab: tap a muscle, then a part (e.g. Upper Chest) to see every exercise that trains it.
- **Exercise detail**: "Not trained by this" lists the parts it misses, plus exercises to pair with it.

## Photos per exercise
Open any exercise → **Add photo** (camera or gallery, several allowed). Photos are resized on the phone and stored offline in IndexedDB. The first photo becomes the card thumbnail; ★ changes the cover.
Photos live only on that phone, so use **More → Backup & restore → Full backup (with photos)** before clearing browser data or switching phones. Install to the Home Screen so iOS/Android don't clean the storage.

## Adding Offline Videos (YouTube Auto-Download or Manual)
- **Auto-Download from YouTube into Project (`videos/`):**
  Run `python3 server.py` inside this folder and open `http://localhost:8765`.
  Tap any exercise → paste a YouTube link → click **Download**. It saves the `.mp4` directly into `videos/<exercise-id>.mp4` and plays right inside that exercise (also works when adding custom exercises in the **Update** tab, or via CLI: `python3 server.py --download "<url>" --id <exercise-id>`).
- **Manual / Offline Phone Video:**
  Tap any exercise → **+ Attach Local Video (.mp4/.mov)** to save a video from your phone directly into offline browser storage (`IndexedDB`).
- Use the **Update** tab to add new exercises on the fly or merge/export `exercises.json`.

## Reference photos & pins
- `images/ref/<exercise-id>-0.jpg` (start) and `-1.jpg` (end) are public-domain photos from [free-exercise-db](https://github.com/yuhonas/free-exercise-db) (Unlicense). They're cached for offline use. Your own photos always appear first.
- **Library → Your pins** lists every pinned exercise, grouped by body area (Chest, Back, Shoulders, Arms, Legs, Core) with highlighted muscle words. Pins stay until you unpin them, and pinned exercises are always included when that muscle is in today's workout.
- **More → Muscle names in Roman Urdu** explains every muscle and part with a highlighted body illustration, and has a switch to show or hide the Urdu lines across the app. The same list opens as a full page from the **Urdu names** button next to Re-sync on Today.
- **Tap any part** in that list (e.g. Upper Ham) to open a page with every exercise that trains it: *Main target* first, then *Also helps*.
