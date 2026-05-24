---
name: html-artifact
description: >
  Produce a single-file interactive HTML artifact instead of markdown prose
  whenever HTML would communicate more clearly — and fire proactively, without
  waiting to be asked. Triggers include: explaining a multi-step process,
  presenting structured data or comparisons, generating reports with navigable
  sections, creating tools or calculators, showing code with syntax
  highlighting, timelines, dashboards, FAQs, or any response where a visual
  layout beats a wall of bullet points. The canonical no-build stack is Tailwind
  + DaisyUI + Alpine.js with contextual additions (Chart.js, Prism.js, D3) as
  needed. Do NOT use for short answers (< 3 sentences), single code snippets,
  conversational replies, or when the user explicitly says to keep it simple.
  Heuristic: if the content would take more than 30 seconds to scan as markdown,
  an HTML artifact almost certainly serves it better.
allowed-tools: Bash, Read, Write, Edit
---

# HTML Artifact

Produce single-file HTML artifacts that are visually expressive, contextually appropriate, and immediately useful — replacing bland markdown where a richer output adds genuine value.

---

## Step 1: Classify the request → pick an output mode

Before writing a line of HTML, identify which output mode fits:

| Request type | Output mode | Key libraries |
|---|---|---|
| Data / comparisons / metrics | **Dashboard** | Chart.js, DaisyUI stats/cards |
| Step-by-step process / tutorial | **Guided Steps** | Alpine.js steps, DaisyUI progress |
| Reference material / cheat sheet | **Reference Doc** | Sticky nav, DaisyUI table, Prism.js |
| Tool / calculator / interactive | **App** | Alpine.js reactive state |
| Report / long-form analysis | **Document** | Prose layout, ToC, DaisyUI collapse |
| Code explanation / review | **Code Walkthrough** | Prism.js, callouts, side-by-side |
| Timeline / history | **Timeline** | DaisyUI timeline component |
| Comparison (A vs B) | **Comparison** | Side-by-side cards or table |
| Q&A / FAQ | **Accordion** | DaisyUI collapse, Alpine.js |

The output mode drives all subsequent decisions — layout, library selection, typography, interaction pattern.

---

## Step 2: Base stack (always include)

Every artifact starts here. Load order matters: DaisyUI CSS must come before the Tailwind script.

```html
<!DOCTYPE html>
<html lang="en" data-theme="THEME">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>TITLE</title>

  <!-- DaisyUI first, then Tailwind -->
  <link href="https://cdn.jsdelivr.net/npm/daisyui@latest/dist/full.min.css"
        rel="stylesheet" type="text/css" />
  <script src="https://cdn.tailwindcss.com"></script>

  <!-- Alpine.js — always defer -->
  <script defer
    src="https://cdn.jsdelivr.net/npm/alpinejs@3/dist/cdn.min.js">
  </script>

  <!-- CONTEXTUAL ADDITIONS — see Step 3 -->
</head>
<body class="min-h-screen bg-base-100 text-base-content">
  <!-- content -->
</body>
</html>
```

**Theme selection** — match the theme to the content's tone:

| Tone | Theme |
|---|---|
| Technical / neutral | `corporate`, `nord`, `winter` |
| Creative / expressive | `synthwave`, `dracula`, `cyberpunk` |
| Professional dark | `business`, `dark`, `night` |
| Friendly / light | `cupcake`, `bumblebee`, `emerald` |
| Serious / data | `lofi`, `autumn`, `sunset` |

Default to `corporate` when tone is ambiguous.

---

## Step 3: Contextual library additions

Only add what the output mode needs.

### Data visualization
```html
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
```
Use for bar, line, pie/doughnut, scatter. Always set `responsive: true`. Match text color to DaisyUI's `base-content` CSS variable.

### Code syntax highlighting
```html
<link rel="stylesheet"
  href="https://cdn.jsdelivr.net/npm/prismjs@1/themes/prism-tomorrow.min.css">
<script src="https://cdn.jsdelivr.net/npm/prismjs@1/prism.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/prismjs@1/components/prism-javascript.min.js"></script>
<!-- add language components as needed -->
```

### Animation / motion
```html
<link rel="stylesheet"
  href="https://cdn.jsdelivr.net/npm/animate.css/animate.min.css">
```
Use `animate__animated animate__fadeInUp` for section reveals. Cap at 3 animated elements per page load — motion should feel intentional, not chaotic.

### Icons
```html
<script src="https://cdn.jsdelivr.net/npm/lucide@latest/dist/umd/lucide.min.js"></script>
```
Or use Unicode for lightweight needs (✓ ✗ ⚠ → ← etc.)

### Math rendering
```html
<script defer src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
```

### Complex diagrams / custom viz
```html
<script src="https://cdn.jsdelivr.net/npm/d3@7/dist/d3.min.js"></script>
```

### 3D / canvas
```html
<script src="https://cdn.jsdelivr.net/npm/three@latest/build/three.min.js"></script>
```

---

## Step 4: Layout patterns by output mode

### Dashboard
```html
<div class="navbar bg-base-200 px-4">
  <span class="text-xl font-bold">TITLE</span>
</div>
<div class="p-6 grid grid-cols-1 md:grid-cols-3 gap-4">
  <div class="stat bg-base-200 rounded-box">
    <div class="stat-title">Metric</div>
    <div class="stat-value">42</div>
    <div class="stat-desc">Context</div>
  </div>
  <div class="col-span-2 card bg-base-200">
    <div class="card-body">
      <canvas id="chart"></canvas>
    </div>
  </div>
</div>
```

### Guided Steps (Alpine.js)
```html
<div x-data="{ step: 1, total: 4 }">
  <ul class="steps steps-horizontal w-full mb-8">
    <li class="step" :class="step >= 1 ? 'step-primary' : ''">Setup</li>
    <li class="step" :class="step >= 2 ? 'step-primary' : ''">Configure</li>
  </ul>
  <div x-show="step === 1" class="card bg-base-200">
    <div class="card-body">...</div>
  </div>
  <div class="flex gap-2 mt-4">
    <button class="btn" @click="step--" x-show="step > 1">← Back</button>
    <button class="btn btn-primary" @click="step++" x-show="step < total">Next →</button>
  </div>
</div>
```

### Reference Doc (sticky sidebar nav)
```html
<div class="drawer lg:drawer-open">
  <input id="drawer" type="checkbox" class="drawer-toggle">
  <div class="drawer-content p-6 max-w-3xl">
    <section id="section-1">
      <h2 class="text-2xl font-bold mb-4">Section</h2>
      ...
    </section>
  </div>
  <div class="drawer-side">
    <ul class="menu p-4 w-48 bg-base-200 text-base-content">
      <li><a href="#section-1">Section 1</a></li>
    </ul>
  </div>
</div>
```

### App / Tool (Alpine.js reactive)
```html
<div class="max-w-2xl mx-auto p-6" x-data="appState()">
  <div class="form-control mb-4">
    <label class="label"><span class="label-text">Input</span></label>
    <input type="text" class="input input-bordered" x-model="inputValue">
  </div>
  <div class="alert alert-info" x-show="result">
    <span x-text="result"></span>
  </div>
  <button class="btn btn-primary" @click="compute()">Run</button>
</div>
<script>
  function appState() {
    return {
      inputValue: '',
      result: null,
      compute() { /* logic */ }
    }
  }
</script>
```

### Comparison (side-by-side)
```html
<div class="grid grid-cols-2 gap-4">
  <div class="card bg-base-200 border-2 border-primary">
    <div class="card-body">
      <h2 class="card-title">Option A</h2>
      <div class="badge badge-success">Pro</div>
    </div>
  </div>
  <div class="card bg-base-200 border-2 border-secondary">
    <div class="card-body">
      <h2 class="card-title">Option B</h2>
    </div>
  </div>
</div>
```

### Accordion / FAQ
```html
<div class="space-y-2">
  <div class="collapse collapse-arrow bg-base-200">
    <input type="radio" name="faq" checked>
    <div class="collapse-title text-lg font-medium">Question?</div>
    <div class="collapse-content"><p>Answer.</p></div>
  </div>
</div>
```

---

## Step 5: Design principles

### Color — never hardcode
Always use DaisyUI semantic tokens: `bg-primary`, `text-secondary`, `bg-base-200`, `text-success`, etc. Hardcoded `#fff` / `#000` breaks dark mode. Use `badge-primary`, `alert-warning`, etc. for semantic status.

### Typography
- Body text: `text-base-content` (respects theming automatically)
- Headings: Google Fonts via CDN when tone warrants it — `<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;700&display=swap" rel="stylesheet">`
- Code / numbers / technical values: `font-mono`
- Always declare `font-sans` as a system font fallback for offline/sandbox contexts

### Spacing
- Page padding: `p-6` or `p-8`
- Section spacing: `mb-8` or `space-y-6`
- Card interiors: `card-body` handles padding automatically
- Readable prose max-width: `max-w-3xl mx-auto`

### Interactivity (Alpine.js)
- Favor `x-show` over `x-if` for toggling (preserves DOM, avoids re-render)
- Scope `x-data` as close to the usage as possible
- Use `@click.prevent` for anything that could trigger browser defaults
- Keep state in plain JS objects — no imports, no build step needed

### Progressive enhancement
For heavy libraries (D3, Three.js), show a loading skeleton while the script initializes:
```html
<div class="skeleton h-48 w-full" id="chart-placeholder"></div>
```

### Accessibility basics
- Every `<input>` needs a `<label>` — use DaisyUI's `form-control` wrapper
- Interactive elements get focus styles automatically from DaisyUI
- Use semantic HTML: `<nav>`, `<main>`, `<section>`, `<article>`
- Never rely on color alone to convey meaning — pair with an icon or text label

---

## Step 6: Common gotchas

| Pitfall | Fix |
|---|---|
| DaisyUI styles overridden by Tailwind | Load DaisyUI CSS *before* the Tailwind `<script>` |
| Alpine.js attributes parsed before script | Always use `defer` on the Alpine script tag |
| Chart.js canvas sizing | Wrap `<canvas>` in a sized container; set `responsive: true` |
| Canvas libraries ignore CSS variables | Chart.js, D3, and `<canvas>` cannot read CSS custom properties — use explicit `rgba()`/hex colors matched to the active DaisyUI theme instead of `hsl(var(--er))` |
| DaisyUI collapse + Alpine.js conflict | Use `type="checkbox"` / `type="radio"` inputs, not `x-show` on collapse |
| Fonts missing in offline/sandbox | Always include `font-sans` as a fallback in font stacks |
| Hardcoded colors break dark mode | Use `bg-base-100` / `text-base-content` exclusively |

---

## Delivery

Write the artifact to a descriptively named file (e.g., `comparison-react-vs-vue.html`, `onboarding-guide.html`) in the current working directory, then open it:

```bash
open <filename>.html
```

Report the file path so the user can find or share it.

---

## When NOT to use this skill

- Short factual answers (< 3 sentences)
- Single code snippets (a markdown code block is fine)
- Conversational or back-and-forth replies
- When the user says "keep it simple" or "just markdown"
- Raw data dumps with no navigational benefit
