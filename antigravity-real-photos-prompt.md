# Task: fill IronSync's "Real photos" slots with real-looking muscle photos

You are working in this repository: **IronSync**, an offline gym planner. It's a single-page PWA: `index.html`, `sw.js`, `server.py`.
The app already has **Real photos** sliders for every muscle and every muscle part. They are all empty right now.
Your job is to **add images, and list each one in `parts.json`**.
**Do not change any app code** (`index.html`, `sw.js`, `server.py`).
The app picks the images up automatically.

## The reference image (attached)
I've attached one image. It shows a real, muscular man photographed from behind/side against a dark studio background.
- His triceps heads are tinted: **Long Head = red**, **Lateral Head = blue**, **Medial Head = green**.
- On the left is a black panel with three labels. Each label is white text on a thin coloured line ending in an angled coloured tail, in the matching colour.

This image is the **exact style target** for every image you add:
- the same kind of real person
- the same lighting
- the same layout
- the same tinted-overlay style
- the same label panel

Also **use the attached image itself** as the Triceps group image (see the list below).

## How the app reads the images (follow exactly)
- Put every image file in `images/parts/`. Name it `<firstTargetId>-<n>.jpg`, for example `tricep_long-1.jpg`.
- Register every image in **`parts.json`** in the repo root. The file must stay in exactly this shape:
  ```json
  {
    "images": [
      { "file": "images/parts/tricep_long-1.jpg", "targets": ["tricep_long", "tricep_lateral", "tricep_medial"], "ts": 1764240000 }
    ]
  }
  ```
- `targets` lists the muscle-part ids visible and highlighted in that image.
  - **Group image:** list *all* parts of that muscle. It then appears in the muscle's main slider, on every part, and on every exercise for that muscle.
  - **Close-up image:** list exactly **one** part id. It appears on that part's own slider and first on exercises that hit that part.
- `ts` is a Unix timestamp in seconds.
- Use only the ids listed below. Any other id is ignored.
- Format: **JPEG, 1280×720 (16:9), quality about 80, under 400 KB each.**
- Optional alternative: if `python3 server.py` is running, the app on `http://localhost:8765` can add images itself (Muscles tab → Add photo). Writing the files and `parts.json` directly is fine and simpler.

## Step 1: look for real photos first
For each item in the list below, first search the web for a real photo that already shows that muscle or part highlighted/coloured in this style. This is for my own personal, private use, so copyrighted sources are fine.

Only accept a found photo if all of these are true:
- It's a real person, not a drawing, 3D render or anatomy chart.
- The highlighted area is anatomically correct for that exact part.
- It's clear at phone size.

Crop or resize it to 1280×720. If the label panel is missing, you may add one in the same style.

## Step 2: if no good photo is found, generate one with Nano Banana
Use Gemini's image model (Nano Banana). **Every generated image must look like the attached reference.** Give Nano Banana the attached image as a style/subject reference each time.

Requirements for every generated image:
- **Photorealistic.** A real human photograph, not an illustration, cartoon, CGI or anatomy drawing.
- **The same man in every image**, matching the reference: lean, muscular, athletic, shirtless, short dark hair, about 40 years old.
- **Lighting and background:** dramatic studio lighting on a near-black background. On the left 40% of the frame, a black panel with the labels.
- **Highlight:** a semi-transparent coloured tint over **exactly** the named part, like the reference. Skin texture stays visible through the tint, and the edges follow the real muscle borders.
- **Accuracy matters more than looks.** Double-check the anatomy (positions are given below). Do not tint neighbouring muscles. Do not invent muscles.
- **Labels:** in the left panel, one label per highlighted part, in the same order as the colours.
  - Use the exact part names given below; check the spelling.
  - Same font look: white, bold, clean sans-serif. Thin coloured line above and below, angled coloured tail at the right.
  - No other text, logos, watermarks or brand names.
- **Colours:**
  - 3-part muscles: part 1 red `#E53935`, part 2 blue `#1E88E5`, part 3 green `#43A047`.
  - 2-part muscles: red, then blue.
  - Back (4 parts): red, blue, green, yellow `#FDD835`.
  - Close-up images: tint only that one part, in the same colour it has in its group image.
- **Camera angle:** pick the angle that shows the part best, as noted in each item.

If an image doesn't pass these checks, regenerate it. Don't save a bad one.

## The list: 10 group images + 28 close-ups = 38 images

Each line gives the file name, then its `targets`, then what to show. Names in quotes are the exact label text.

### Chest (front view, arms slightly out)
- `upper_chest-1.jpg`, all 3 parts: "Upper Chest" red, "Mid Chest" blue, "Lower Chest" green.
- `upper_chest-2.jpg`, close-up, `upper_chest`: "Upper Chest" (upper/clavicular pec, just under the collarbone) in red.
- `mid_chest-1.jpg`, close-up, `mid_chest`: "Mid Chest" (middle sternal pec, nipple height) in blue.
- `lower_chest-1.jpg`, close-up, `lower_chest`: "Lower Chest" (lower outer edge of the pec, above the ribs) in green.

### Back (rear view, arms slightly out / flexed)
- `lats_width-1.jpg`, all 4 parts: "Lats" red, "Mid-Back" blue, "Upper Traps" green, "Lower Back" yellow.
- `lats_width-2.jpg`, close-up, `lats_width`: "Lats" (latissimus dorsi, the V-shaped wings from armpit down to the waist) in red.
- `mid_back-1.jpg`, close-up, `mid_back`: "Mid-Back" (rhomboids and middle traps, between the shoulder blades) in blue.
- `traps_upper-1.jpg`, close-up, `traps_upper`: "Upper Traps" (from neck to shoulder top) in green.
- `lower_back-1.jpg`, close-up, `lower_back`: "Lower Back" (spinal erectors, the two columns either side of the lower spine) in yellow.

### Shoulders (side view; rear delt from behind)
- `front_delt-1.jpg`, all 3 parts: "Front Delt" red, "Side Delt" blue, "Rear Delt" green.
- `front_delt-2.jpg`, close-up, `front_delt`: "Front Delt" (anterior deltoid, front of the shoulder) in red.
- `side_delt-1.jpg`, close-up, `side_delt`: "Side Delt" (lateral deltoid, outer cap of the shoulder) in blue.
- `rear_delt-1.jpg`, close-up, `rear_delt`: "Rear Delt" (posterior deltoid, back of the shoulder) in green.

### Biceps (front/side view, arm flexed)
- `bicep_long-1.jpg`, all 3 parts: "Long Head" red, "Short Head" blue, "Brachialis" green.
- `bicep_long-2.jpg`, close-up, `bicep_long`: "Long Head" (outer side of the biceps, the peak) in red.
- `bicep_short-1.jpg`, close-up, `bicep_short`: "Short Head" (inner side of the biceps, towards the chest) in blue.
- `brachialis-1.jpg`, close-up, `brachialis`: "Brachialis" (under the biceps on the outer arm, between the biceps and triceps, just above the elbow) in green.

### Triceps (rear/side view, like the reference)
- `tricep_long-1.jpg`, all 3 parts: **use the attached reference image itself**, resized to 1280×720.
- `tricep_long-2.jpg`, close-up, `tricep_long`: "Long Head" (inner/back part of the triceps, closest to the body) in red.
- `tricep_lateral-1.jpg`, close-up, `tricep_lateral`: "Lateral Head" (outer horseshoe part of the triceps) in blue.
- `tricep_medial-1.jpg`, close-up, `tricep_medial`: "Medial Head" (lower triceps just above the elbow) in green.

### Quads (front view, standing, legs flexed)
- `quad_rectus-1.jpg`, all 3 parts: "Rectus Femoris" red, "Outer Sweep" blue, "VMO Teardrop" green.
- `quad_rectus-2.jpg`, close-up, `quad_rectus`: "Rectus Femoris" (centre-front of the thigh, hip to knee) in red.
- `quad_outer-1.jpg`, close-up, `quad_outer`: "Outer Sweep" (vastus lateralis, outer side of the thigh) in blue.
- `quad_inner-1.jpg`, close-up, `quad_inner`: "VMO Teardrop" (vastus medialis, inner thigh just above the knee) in green.

### Hamstrings (rear view, standing)
- `ham_stretch-1.jpg`, both parts: "Upper Ham" red, "Lower Ham" blue.
- `ham_stretch-2.jpg`, close-up, `ham_stretch`: "Upper Ham" (upper back of the thigh, near the glutes) in red.
- `ham_curl-1.jpg`, close-up, `ham_curl`: "Lower Ham" (lower back of the thigh, near the knee) in blue.

### Glutes (rear view; side-rear for glute med)
- `glute_max-1.jpg`, both parts: "Glute Max" red, "Glute Med" blue.
- `glute_max-2.jpg`, close-up, `glute_max`: "Glute Max" (the main buttock muscle) in red.
- `glute_med-1.jpg`, close-up, `glute_med`: "Glute Med" (upper outer hip, above the glute max, below the hip bone) in blue.

### Calves (rear view, on toes)
- `gastroc-1.jpg`, both parts: "Gastrocnemius" red, "Soleus" blue.
- `gastroc-2.jpg`, close-up, `gastroc`: "Gastrocnemius" (upper calf, the diamond-shaped two heads) in red.
- `soleus-1.jpg`, close-up, `soleus`: "Soleus" (lower, flatter calf under and to the sides of the gastrocnemius) in blue.

### Core (front view, abs tensed)
- `upper_abs-1.jpg`, all 3 parts: "Upper Abs" red, "Lower Abs" blue, "Obliques" green.
- `upper_abs-2.jpg`, close-up, `upper_abs`: "Upper Abs" (top rows of the six-pack, below the chest) in red.
- `lower_abs-1.jpg`, close-up, `lower_abs`: "Lower Abs" (the abs below the belly button) in blue.
- `obliques-1.jpg`, close-up, `obliques`: "Obliques" (sides of the waist) in green.

For a **group** image, `targets` is every id of that muscle:

| Muscle | targets |
|---|---|
| chest | `upper_chest, mid_chest, lower_chest` |
| back | `lats_width, mid_back, traps_upper, lower_back` |
| shoulders | `front_delt, side_delt, rear_delt` |
| biceps | `bicep_long, bicep_short, brachialis` |
| triceps | `tricep_long, tricep_lateral, tricep_medial` |
| quads | `quad_rectus, quad_outer, quad_inner` |
| hamstrings | `ham_stretch, ham_curl` |
| glutes | `glute_max, glute_med` |
| calves | `gastroc, soleus` |
| core | `upper_abs, lower_abs, obliques` |

## Rules
- Don't edit `index.html`, `sw.js` or `server.py`. Only add files in `images/parts/` and entries in `parts.json`.
- Keep any entries already in `parts.json`; append yours.
- Don't commit or push. I'll review first.

## When you're done
1. Check that `parts.json` is valid JSON and that every `file` in it exists.
2. Check that every image is 1280×720 JPEG, under 400 KB.
3. Run `python3 server.py`, open `http://localhost:8765`, go to **Muscles**, and tap each muscle. Confirm that:
   - the group slider and each part's slider show the right images
   - opening an exercise (e.g. Cable Tricep Pushdown) starts with those images
4. Give me a table of all 38 images with these columns:
   - file name
   - targets
   - **found** (with source URL) or **generated**
   - anything you weren't sure about (e.g. "medial head is hard to see from this angle")
