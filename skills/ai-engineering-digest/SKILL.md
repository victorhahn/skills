---
name: ai-engineering-digest
description: Fetch a weekly briefing of what's trending and being discussed in the AI engineering landscape — HN, Reddit, GitHub — and synthesize it into a structured digest covering technical signal, notable projects, and the professional/cultural discourse around AI. Use when the user says "/ai-engineering-digest", "run the digest", "what's the ai meta this week", "weekly ai pulse", "what's trending in ai dev", or wants a broad briefing on the current state of AI engineering. Accepts an optional topic arg for on-demand narrower queries ("/ai-engineering-digest mcp").
allowed-tools: Bash, WebFetch, Write, Read
---

# AI Engineering Digest

Produce a weekly briefing on the AI engineering landscape — what's shipping, what's getting traction, and what professionals are actually talking about. Pulls from HN, GitHub Trending, and a curated set of subreddits, then synthesizes everything into a structured markdown report.

## Invocation

- `/ai-engineering-digest` — full weekly digest, writes markdown to CWD
- `/ai-engineering-digest --html` — same digest, rendered as a single-file interactive HTML artifact
- `/ai-engineering-digest <topic>` — on-demand briefing narrowed to a specific topic (e.g. `mcp`, `cursor`, `agents`)
- `/ai-engineering-digest <topic> --html` — topic-focused digest as HTML

Output files:
- Markdown: `ai-engineering-digest-<YYYY-MM-DD>.md`
- HTML: `ai-engineering-digest-<YYYY-MM-DD>.html`

Both written to the current working directory, or wherever the user specifies. The `--html` flag can be combined with a topic arg.

---

## Execution

### Step 1 — Establish time window

Use today's date to set the 7-day lookback window. All sources should be filtered to content from the past 7 days.

If a topic arg was provided, note it — it will be used as a secondary filter during the synthesis pass, not as a prefetch keyword filter.

### Step 2 — Fetch HN (Hacker News)

Use the Algolia HN Search API to pull top stories from the past week. Fetch broadly by points — do not keyword-filter upfront.

```
https://hn.algolia.com/api/v1/search?tags=story&numericFilters=created_at_i>UNIX_TIMESTAMP,points>50&hitsPerPage=50&attributesToRetrieve=title,url,points,num_comments,objectID
```

Replace `UNIX_TIMESTAMP` with the Unix timestamp for 7 days ago.

Also fetch Ask HN and Show HN separately (tag `ask_hn` and `show_hn`) — these often contain the richest practitioner discussions.

Collect: title, URL, points, comment count, HN discussion link (`https://news.ycombinator.com/item?id=<objectID>`).

### Step 3 — Fetch GitHub Trending

Scrape the GitHub trending page for the past week:

```
https://github.com/trending?since=weekly
```

Use WebFetch. Extract: repo name, description, stars, star delta this week, language, URL.

Also fetch the language-filtered view for Python and TypeScript (highest signal for AI tooling):

```
https://github.com/trending/python?since=weekly
https://github.com/trending/typescript?since=weekly
```

### Step 4 — Fetch Reddit

Pull top posts (past week) from each subreddit using Reddit's JSON API. Use `top.json?t=week&limit=25` for each.

**Technical subreddits:**
- `https://www.reddit.com/r/LocalLLaMA/top.json?t=week&limit=25`
- `https://www.reddit.com/r/ClaudeAI/top.json?t=week&limit=25`
- `https://www.reddit.com/r/AI_Agents/top.json?t=week&limit=25`
- `https://www.reddit.com/r/programming/top.json?t=week&limit=25`

**Social/professional sentiment subreddits:**
- `https://www.reddit.com/r/singularity/top.json?t=week&limit=25`
- `https://www.reddit.com/r/openai/top.json?t=week&limit=25`
- `https://www.reddit.com/r/artificial/top.json?t=week&limit=25`
- `https://www.reddit.com/r/ExperiencedDevs/top.json?t=week&limit=25`

For each post collect: title, score, comment count, URL, subreddit. Add a `User-Agent` header to avoid Reddit's bot block:

```bash
curl -H "User-Agent: ai-engineering-digest/1.0" "https://www.reddit.com/r/LocalLLaMA/top.json?t=week&limit=25"
```

### Step 5 — Synthesize

With all raw data collected, run a single synthesis pass. The goal is **editorial judgment, not keyword matching** — surface what a senior software engineer would actually find worth knowing.

Produce a structured markdown digest with these sections:

---

#### TL;DR
4–6 bullet points. "What happened this week in AI engineering" — themes, not a list of links. Write this for someone who has 60 seconds.

#### Technical Signal
What tools, frameworks, libraries, or patterns are visibly gaining traction this week? This is not a changelog — focus on community adoption signals: multiple independent discussions, unexpected star velocity, repeated mentions across sources. Include why it's getting attention, not just that it is.

#### GitHub Watches
3–5 repos from the trending pull worth tracking. For each: name, link, one-sentence description, and the signal (stars this week, what community is saying about it).

#### Professional Landscape
The human side of the discourse — disruption anxiety, job market discussion, AI replacing white-collar work, practitioner sentiment about the pace of change. Write this as a honest summary of the professional conversation, not filtered for optimism or pessimism. Senior engineers navigating this landscape deserve a straight read.

#### Reads Worth Your Time
5–8 specific links — HN threads, Reddit posts, articles — that surfaced as genuinely high-signal. Include: title, source, link, and one sentence on why it's worth reading.

---

If a topic arg was provided, add a final section:

#### `<topic>` Focus
Everything from the above data that touches the specified topic, synthesized into a tighter briefing.

### Step 6 — Write output

If `--html` was **not** specified, write the markdown digest to `ai-engineering-digest-<YYYY-MM-DD>.md` in the current working directory (or a user-specified path). Include a header block:

```markdown
# AI Engineering Digest — <date>
_Sources: Hacker News · GitHub Trending · Reddit (LocalLLaMA, ClaudeAI, AI_Agents, programming, singularity, openai, artificial, ExperiencedDevs)_
_Generated: <timestamp>_
```

If `--html` **was** specified, generate a single-file HTML artifact instead — see **HTML Artifact Spec** below. Write it to `ai-engineering-digest-<YYYY-MM-DD>.html`.

After writing either format, report the file path to the user and offer a one-line summary of the top theme from the TL;DR.

---

## HTML Artifact Spec

When `--html` is requested, generate a self-contained single-file HTML document with all CSS and JavaScript inlined. No external CDN dependencies. The file must open correctly with `open <filename>` in any browser, offline.

### Overall design

- **Dark mode by default.** Background `#0d1117` (GitHub dark), text `#e6edf3`.
- **Max content width: 900px, centered.** Generous padding. Readable at any viewport.
- **System font stack:** `ui-sans-serif, system-ui, -apple-system, sans-serif`.
- **No framework.** Vanilla HTML/CSS/JS only.

### Color palette

```
--bg:       #0d1117
--surface:  #161b22
--surface2: #1c2128
--border:   #30363d
--text:     #e6edf3
--muted:    #8b949e
--hn:       #ff6600
--gh:       #6e40c9
--rd:       #ff4500
--blue:     #58a6ff
--gold:     #f0c040
--green:    #3fb950
```

### Layout — five sections

Sticky header (title + date only, no source badges). Sticky sub-nav below it with scroll spy (5 items: TL;DR, Technical Signal, GitHub, Discourse, Reads). Footer: one line — "Generated by ai-engineering-digest · <date>". No source list in footer.

**1. TL;DR — horizontal card carousel**

7 large cards in a horizontally scrollable track with `scroll-snap-type: x mandatory`. Each card is ~360px wide, min 200px tall, `--surface` background, left border accent in `--hn`. Card contents:
- Small `#N` label (muted, uppercase)
- Large headline (17–18px, bold)
- 2–3 sentence summary (muted, 12.5px)
- `→ Source` CTA at bottom-right, linking to the original article/thread

Below the track: prev/next arrow buttons + dot indicators. Dots update on scroll. Arrows disable at boundaries.

**2. Technical Signal**

Free-flowing editorial text. Inline chips for specific repos/tools:
```html
<a class="chip" href="<url>" target="_blank">owner/repo ↗</a>
```
Chips: `--surface` bg, `--border` border, `--blue` text, lift box-shadow on hover.

**3. GitHub**

Full-width sortable table. Show top ~11 rows by default; remaining rows hidden with `hidden` attribute and a "Show all N repos ↓" toggle button below. Clicking toggles visibility and button label. Column headers are clickable to sort (asc/desc toggle) — default sort: weekly delta descending. Columns: Repo (linked), Description, Lang (colored badge), ⭐ Total, 📈 This Week. Delta coloring: gold if >5k, green if >2k, muted otherwise. Language badge colors: Python `rgba(53,114,165,.2)` / TypeScript `rgba(49,120,198,.2)` / Rust `rgba(222,165,132,.2)` / Shell `rgba(137,224,81,.2)` / JS `rgba(241,224,90,.2)`.

Include ALL repos from the trending pull (main + Python + TypeScript, deduplicated). This should be 25–35 repos, not 6.

**4. Discourse (was "Professional Landscape")**

Two subsections, each with a `disc-sub` label:
- **AI, Work & the Profession** — job market, cost/billing disruption, productivity studies, cultural backlash
- **Engineering & Systems Discourse** — language debates, security incidents, infrastructure choices, ecosystem events

Each paragraph gets a left border `3px solid --rd` and left padding. Bold the topic sentence lead for scannability.

**5. Reads**

Two tabs: [Hacker News (N)] [Reddit (N)]. Each tab shows a flat dense list — no cards, no hook sentences, pure density. Each row:

```
[HN pill] Title as clickable link             pts · comments
[r/ pill] [subreddit] Title as clickable link  score · comments
```

Target **25 items per tab minimum**. For HN: top stories sorted by points. For Reddit: top posts across all subreddits sorted by score, with subreddit label on each row. Tabs switch with vanilla JS (add/remove `.on` class). No filtering, no accordions — just two tabs of dense links.

### Interactivity

1. **Scroll spy** — `IntersectionObserver` highlights active section in sub-nav.
2. **Header shrink** — at 50px scroll, reduce padding + add backdrop-filter blur.
3. **Carousel** — prev/next buttons + dot nav, driven by `scrollTo`. Scroll listener updates active dot.
4. **GitHub table sort** — click column header to sort asc/desc. Active column shows ↑ or ↓ indicator.
5. **GitHub show more** — toggle hidden rows + button label.
6. **Reads tabs** — click tab to switch panel visibility.
7. All external links: `target="_blank" rel="noopener"`.
8. No animations, typewriter effects, or gratuitous transitions.

### Data depth requirements (inform Step 5 output)

- HN: collect top 50 stories; use top 25 for Reads tab, filter for relevance in Technical Signal narrative
- Reddit: collect top 25 per subreddit; use top 25 cross-subreddit for Reads tab (sort by score across all subreddits)
- GitHub: include all trending repos from main + Python + TypeScript pulls (deduplicated, ~30 total)
- Carousel cards: 6–8 cards, each linking to its canonical source

### Generation guidance

Build the full HTML in memory and write it in a single operation. Do not write placeholder content — populate every section with the synthesized data from Step 5.

---

## Failure handling

- If a Reddit endpoint returns a non-200 or rate-limit response, skip that subreddit and note it in the output header.
- If GitHub trending is unavailable, skip it and note it.
- Never fail silently — always tell the user which sources were skipped and why.
- Partial data is fine — a digest from 6/8 sources is still useful.

---

## Design notes

- **Engagement-first, not keyword-first.** Pull by score/upvotes/stars, then let the synthesis pass apply relevance judgment. This catches organic discussions that don't use expected terminology.
- **Senior-eng lens.** Bias toward substance over hype: real usage reports, architectural discussions, tooling comparisons, practitioner war stories. Filter out pure product announcements with no community discussion.
- **Both lenses matter.** Technical signal and professional/cultural sentiment are equally important outputs. A senior engineer needs to know what's shipping *and* what their peers think about what it means for the profession.
