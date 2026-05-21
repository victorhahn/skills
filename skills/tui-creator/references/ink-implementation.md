# Ink Implementation Guide

Concrete component, hook, and option recipes for building production-grade TUIs with Ink. **Grounded in the [Ink README](https://github.com/vadimdemedes/ink) for Ink 7 / React 19** — verified against the npm registry and the upstream readme.

> **Re-verify before scaffolding.** Ink moves through majors. The shape of this guide stays stable, but exact peer versions drift. Check:
> ```bash
> curl -s https://registry.npmjs.org/ink | jq -r '."dist-tags".latest'
> curl -s https://registry.npmjs.org/ink | jq -r '.versions[."dist-tags".latest] | {peerDependencies, engines}'
> ```
> If the latest `ink` major has moved past 7, scan the README's hooks/API section for breaking changes before applying these recipes verbatim.

---

## 1. Stack snapshot (verified)

| Package | Current | Notes |
|---|---|---|
| `ink` | `^7.0` | Node `>=22`, React `>=19.2` peer |
| `react` | `^19.2` | Required peer |
| `ink-text-input` | `^6.0` | Single-line text input |
| `ink-select-input` | `^6.2` | Vertical select list |
| `ink-spinner` | `^5.0` | (Or use Ink's `useAnimation` directly — see §9) |
| `ink-link` | `^5.0` | OSC-8 clickable links |
| `ink-gradient` | `^4.0` | Gradient text |
| `ink-table` | `^3.1` | Read-only table |
| `ink-testing-library` | `^4.0` | dev-only testing harness |

Note: many "ink-" community packages exist (forms, big-text, progress-bar, scroll-list, virtual-list, etc.). Pull them in **lazily**, behind the interactive entry point — never ship them on the agent (JSON) path.

---

## 2. Bootstrap

```bash
pnpm dlx create-ink-app --typescript my-cli
```

For an existing CLI codebase adding TUI:

```bash
pnpm add ink@^7 react@^19
pnpm add -D @types/react ink-testing-library@^4
```

`package.json` essentials:

```json
{
  "type": "module",
  "engines": { "node": ">=22" }
}
```

Mount and shut down cleanly:

```tsx
// src/ui/runTui.tsx
import { render } from "ink";
import { App } from "./App.js";

export async function runTui() {
  const { waitUntilExit } = render(<App />, {
    // see §14 for the full options matrix; these are the defaults worth knowing
    exitOnCtrlC: true,
    patchConsole: true,
    maxFps: 30,
    incrementalRendering: true,   // flicker reducer; enable explicitly
    alternateScreen: false,        // inline default; flip for vim/htop-style
    kittyKeyboard: { mode: "auto" }, // for distinguishing Tab vs Ctrl+I, Shift+Enter, etc.
  });
  await waitUntilExit();
}
```

`runTui` is loaded lazily from the CLI entry (see the `cli-creator` skill's `node-defaults.md` §"When the CLI Also Needs a TUI") so the agent/JSON path never pays the React boot cost.

---

## 3. Layout paradigms → `<Box>` recipes

Ink layout is Yoga flexbox — every `<Box>` is `display: flex`. Map the seven paradigms from `design-principles.md` §1 (also in the parent SKILL.md §2):

### Persistent Multi-Panel (lazygit / Studio direction)

```tsx
<Box flexDirection="row" height="100%">
  {/* Left rail of nouns */}
  <Box flexDirection="column" width={28} flexShrink={0}>
    <PanelHeader title="Status" focused={focus === "status"} />
    <Status />
    <PanelHeader title="Files" focused={focus === "files"} />
    <Files />
    <PanelHeader title="Branches" focused={focus === "branches"} />
    <Branches />
  </Box>
  {/* Swappable detail */}
  <Box flexGrow={1} flexDirection="column" paddingLeft={1}>
    <DetailFor selection={selected} />
  </Box>
</Box>
```

Rule: panels stay in fixed positions. Use `flexShrink={0}` on the rail so the detail pane absorbs window-width changes, not the rail.

### Miller Columns (yazi / ranger)

```tsx
<Box flexDirection="row">
  <Box width="20%" borderStyle="round" borderColor={focusedColor("parent")}><Parent /></Box>
  <Box width="35%" borderStyle="round" borderColor={focusedColor("current")}><Current /></Box>
  <Box flexGrow={1} borderStyle="round" borderColor={focusedColor("preview")}><Preview /></Box>
</Box>
```

### Widget Dashboard (btop / bottom)

```tsx
<Box flexDirection="column">
  <Box flexDirection="row" gap={1}>
    <Widget title="CPU" flexGrow={1}><CpuChart /></Widget>
    <Widget title="Memory" flexGrow={1}><MemChart /></Widget>
  </Box>
  <Box flexDirection="row" gap={1} marginTop={1}>
    <Widget title="Network" flexGrow={1}><NetChart /></Widget>
    <Widget title="Disk" flexGrow={1}><DiskChart /></Widget>
  </Box>
  <Box flexGrow={1} marginTop={1}><ProcessTable /></Box>
</Box>
```

`gap`, `columnGap`, `rowGap` are first-class in Ink 7 — use them instead of margins between siblings for cleaner reflow.

### IDE Three-Panel (harlequin / posting)

```tsx
<Box flexDirection="column" height="100%">
  <TabBar tabs={tabs} active={activeTab} />
  <Box flexDirection="row" flexGrow={1}>
    {sidebarOpen && <Box width={24}><Sidebar /></Box>}
    <Box flexGrow={1}><Editor /></Box>
  </Box>
  <Box height={resultsExpanded ? "60%" : 10}><Results /></Box>
  <Footer />
</Box>
```

### Overlay / Popup (atuin / fzf)

Use `position="absolute"` with `top`/`left` for centered overlays. Pair with `alternateScreen: true` if it should preserve scrollback (most popups should not — render inline).

```tsx
<Box position="absolute" top="20%" left="20%" width="60%" height="60%"
     borderStyle="round" borderColor="cyan" backgroundColor="black">
  <CommandPalette />
</Box>
```

### Header + Scrollable List (htop / tig)

```tsx
<Box flexDirection="column" height="100%">
  <Box height={6} flexDirection="row" gap={2}><Meters /></Box>
  <Box flexGrow={1}><ScrollList items={items} /></Box>
  <Footer />
</Box>
```

For large lists, use `ink-virtual-list` rather than rendering every item — Ink's React reconciler is fast but Yoga layout still walks every node.

---

## 4. Focus and keyboard navigation

Ink ships `useFocus` and `useFocusManager` — the three-layer discoverability stack (parent SKILL.md §3, cross-cutting pattern 5) maps cleanly:

```tsx
import { Box, Text, useFocus, useFocusManager, useInput } from "ink";

function Panel({ id, title, children }: { id: string; title: string; children: React.ReactNode }) {
  const { isFocused } = useFocus({ id });
  return (
    <Box flexDirection="column" borderStyle="round"
         borderColor={isFocused ? "cyan" : "gray"}>
      <Text bold={isFocused} dimColor={!isFocused}>{title}</Text>
      {children}
    </Box>
  );
}

function App() {
  const { focus, focusNext, focusPrevious, activeId } = useFocusManager();

  // Tab / Shift-Tab are handled by Ink automatically.
  // Add direct focus shortcuts:
  useInput((input, key) => {
    if (key.ctrl && input === "1") focus("status");
    if (key.ctrl && input === "2") focus("files");
    if (key.ctrl && input === "3") focus("branches");
  });

  return (
    <Box flexDirection="column">
      <Box flexDirection="row" flexGrow={1}>
        <Panel id="status" title="Status">…</Panel>
        <Panel id="files" title="Files">…</Panel>
        <Panel id="branches" title="Branches">…</Panel>
      </Box>
      <Footer activePanel={activeId} />
    </Box>
  );
}
```

Important: `useFocus({ id })` adds the component to the focus ring **in render order**. If the visual order matters, ensure the JSX tree is also in that order.

For panels that should be skippable (collapsed, hidden), pass `isActive: false` to `useFocus` so they stay in the order but don't receive focus.

---

## 5. Input — `useInput`, `usePaste`, and the kitty protocol

```tsx
useInput((input, key) => {
  // Single character or short string (pasted input → usePaste, not here)
  if (input === "q") exit();
  if (input === "/") setSearchOpen(true);
  if (input === ":") setPaletteOpen(true);
  if (input === "?") setHelpOpen(true);

  if (key.escape) closeOverlays();
  if (key.return) confirm();
  if (key.tab && key.shift) focusPrevious();
  if (key.upArrow) move(-1);
  if (key.downArrow) move(1);

  // Ink 7 + kitty protocol: distinguishes Tab vs Ctrl+I, Shift+Enter, super/hyper keys.
  // Without kitty protocol, key.tab alone fires for both Tab and Ctrl+I.
}, { isActive: !overlayOpen });
```

Use `{ isActive }` to **scope input by mode**. The footer/palette/which-key overlays all hold input; the main panel handler should pass `isActive: !overlayOpen`. This is how you implement mode-aware footer rewriting (zellij pattern, §6 cross-cutting).

Pasted text uses bracketed paste mode (`\x1b[?2004h`) and is delivered as one string via `usePaste`:

```tsx
usePaste((text) => {
  // Multi-line paste arrives as a single string. Newlines and ANSI sequences are preserved verbatim.
  insertAtCursor(text);
});
```

`useInput` will *not* receive pasted content when `usePaste` is active. This is the right pattern for any text input where Enter must mean "submit" — without `usePaste`, a pasted newline would trigger Enter mid-paste.

### Kitty keyboard protocol

```tsx
render(<App />, { kittyKeyboard: { mode: "auto" } });
```

`mode: "auto"` heuristically detects supporting terminals (kitty, WezTerm, Ghostty) and falls back silently elsewhere. Worth turning on for any TUI that wants:

- Tab and Ctrl+I to be distinct
- Shift+Enter (for multi-line input fields)
- Super / Hyper modifiers
- Press vs repeat vs release events (`key.eventType`)

Set `flags: ['disambiguateEscapeCodes', 'reportEventTypes']` for the latter.

---

## 6. Color system → Ink

The semantic slot table from `design-principles.md` §4 maps to a small theme module. Ink accepts named colors, hex, RGB, and HSL (passed through to chalk):

```tsx
// src/ui/theme.ts
export const theme = {
  fg: {
    default: "#c0caf5",
    muted: "#565f89",
    emphasis: "#e0e0e0",
  },
  bg: {
    base: undefined,           // let terminal show through
    surface: "#24283b",
    overlay: "#414868",
    selection: "#364a82",
  },
  accent: {
    primary: "#7aa2f7",        // the ONE accent — see parent SKILL.md §3 (pattern 2)
  },
  status: {
    error: "#f7768e",
    warning: "#e0af68",
    success: "#9ece6a",
    info: "#7dcfff",
  },
} as const;
```

Pass through semantic slots, never hard-coded hex at the call site:

```tsx
<Text color={theme.fg.muted}>commit abc1234</Text>
<Text color={theme.status.error} bold>delete</Text>
<Box backgroundColor={isSelected ? theme.bg.selection : undefined}>…</Box>
```

### NO_COLOR + tier fallback

Ink uses chalk under the hood and respects chalk's environment detection. To explicitly degrade:

```tsx
const colorEnabled = !process.env.NO_COLOR;
const color = colorEnabled ? theme.accent.primary : undefined;
```

For graceful degradation, never make state legible by color alone. Pair with bold/dim/underline/inverse (`design-principles.md` §4).

---

## 7. Borders — state-bearing

The borders rule (parent SKILL.md §3, pattern 3): state-bearing or absent. In Ink that means `borderStyle="round"` with `borderColor` driven by focus/mode state.

```tsx
function ModeBox({ mode, children }: { mode: "read" | "plan" | "write"; children: React.ReactNode }) {
  const borderColor =
    mode === "read"  ? theme.fg.muted :
    mode === "plan"  ? theme.status.info :
    /* write */        theme.status.warning;

  return (
    <Box borderStyle="round" borderColor={borderColor} padding={1}>
      {children}
    </Box>
  );
}
```

This is the **claude-code mode-colored prompt border** pattern — state in chrome, zero status-bar real estate.

Available `borderStyle` values: `single | double | round | bold | singleDouble | doubleSingle | classic`. **Use `round` as default.** Critics consistently dislike `double` and ASCII fallbacks. You can also pass a `BoxStyle` object for fully custom characters.

Per-edge controls (`borderTop`, `borderBottom`, `borderLeft`, `borderRight`, all `boolean`, default `true`) let you draw "open" boxes — a panel with only a top edge, etc. Useful for the lazydocker "rail of nouns" look.

For the "absent border, layered background" Atelier direction:

```tsx
<Box flexDirection="row" gap={1}>
  <Box backgroundColor={theme.bg.surface} padding={1} flexGrow={1}>…</Box>
  <Box backgroundColor={theme.bg.overlay} padding={1} flexGrow={1}>…</Box>
</Box>
```

A 3–5% lightness step + 1-cell `gap` reads as two panes without chrome.

---

## 8. Async I/O — render off the main path

The single highest-leverage rule (parent SKILL.md §3, pattern 7). In Ink, render is React; everything else is just Node.

```tsx
function Files() {
  const [files, setFiles] = useState<File[] | null>(null);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const data = await scanFiles();   // returns a promise; doesn't touch React
        if (!cancelled) setFiles(data);
      } catch (e) {
        if (!cancelled) setError(e as Error);
      }
    })();
    return () => { cancelled = true; };
  }, []);

  if (error) return <Text color={theme.status.error}>{error.message}</Text>;
  if (!files) return <PanelHeader title="Files" loading />;   // header spinner
  return <FileList files={files} />;
}
```

Always:

1. **Run the I/O in `useEffect`**, not at render-time.
2. **Show the spinner in the panel header**, not the panel body. The user reads "loading" without losing the body layout.
3. **Cancel on unmount** with the `cancelled` flag, or use `AbortController` for fetch-shaped APIs.
4. **Never await before the first paint.** The first render must return immediately with a skeleton, never block on `await`.

For child processes (the classic CLI case — `git status`, `kubectl get`, etc.):

```tsx
import { execa } from "execa";

useEffect(() => {
  const proc = execa("git", ["status", "--porcelain"]);
  proc.then(({ stdout }) => setStatus(parse(stdout))).catch(setError);
  return () => proc.kill();   // cancellation if component unmounts mid-flight
}, []);
```

---

## 9. Animation — one shared timer with `useAnimation`

Ink 7 ships `useAnimation`, which consolidates all animated components into a single render cycle. **Always prefer this over `setInterval`** — it respects `maxFps` and shares timer state with sibling animations.

```tsx
function Spinner() {
  const { frame } = useAnimation({ interval: 80 });
  const chars = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"];
  return <Text color={theme.accent.primary}>{chars[frame % chars.length]}</Text>;
}

function HeaderSpinner({ loading }: { loading: boolean }) {
  // Stop the shared timer when nothing needs it — saves CPU on long-idle TUIs.
  const { frame } = useAnimation({ interval: 80, isActive: loading });
  if (!loading) return null;
  return <Spinner />;
}
```

For continuous (non-frame-indexed) motion, use `time` or `delta`:

```tsx
const { time } = useAnimation({ interval: 50 });
const wave = Math.sin(time / 1000 * Math.PI * 2);   // value in [-1, 1]
```

Anti-pattern: don't drive *state* updates from `useAnimation` — only visuals. `useAnimation` returns values; updating state every tick will spam the reconciler.

### Spinners and progress

Use `ink-spinner` for the convenience surface; use `useAnimation` directly when you want to share the timer with other components (palette fade, sparkline ticks, etc.).

Throttle status-indicator updates to event-driven changes or 1 Hz max — parent SKILL.md §3, pattern 6. btop's own README recommends 2000ms. Don't poll on a tick.

---

## 10. Three-layer discoverability in Ink

The footer / which-key / palette pattern (parent SKILL.md §3, pattern 5), implemented:

### Single keymap as source of truth

```tsx
// src/ui/keymap.ts
export type Action = "quit" | "search" | "help" | "palette" | "focusNext" | ...;

export const keymap: Record<Action, { key: string; label: string; group: string }> = {
  quit:        { key: "q",      label: "quit",       group: "global" },
  search:      { key: "/",      label: "search",     group: "global" },
  help:        { key: "?",      label: "help",       group: "global" },
  palette:     { key: ":",      label: "command",    group: "global" },
  focusNext:   { key: "Tab",    label: "next panel", group: "navigation" },
  // ... per-panel actions tagged with their panel id in `group`
};
```

### Footer (always visible, context-scoped)

```tsx
function Footer({ activePanel }: { activePanel: string | undefined }) {
  const items = Object.values(keymap).filter(
    a => a.group === "global" || a.group === activePanel
  );
  return (
    <Box flexDirection="row" gap={2}>
      {items.map(a => (
        <Text key={a.key} dimColor>
          <Text bold color={theme.accent.primary}>[{a.key}]</Text>{" "}{a.label}
        </Text>
      ))}
    </Box>
  );
}
```

### Which-key popup (`?`)

```tsx
function HelpOverlay({ open, onClose }: { open: boolean; onClose: () => void }) {
  useInput((_, key) => { if (key.escape) onClose(); }, { isActive: open });
  if (!open) return null;
  const grouped = groupBy(Object.values(keymap), a => a.group);
  return (
    <Box position="absolute" top="10%" left="15%" width="70%"
         borderStyle="round" borderColor={theme.accent.primary}
         backgroundColor={theme.bg.overlay} padding={1} flexDirection="column">
      <Text bold>Keybindings</Text>
      {Object.entries(grouped).map(([group, actions]) => (
        <Box key={group} flexDirection="column" marginTop={1}>
          <Text color={theme.fg.muted} bold>{group}</Text>
          {actions.map(a => (
            <Box key={a.key} gap={2}>
              <Box width={10}><Text color={theme.accent.primary}>{a.key}</Text></Box>
              <Text>{a.label}</Text>
            </Box>
          ))}
        </Box>
      ))}
    </Box>
  );
}
```

### Command palette (`:`)

Use `ink-text-input` for the input field, fuzzy-match against the keymap:

```tsx
import TextInput from "ink-text-input";

function Palette({ open, onClose, onAction }: PaletteProps) {
  const [query, setQuery] = useState("");
  const matches = fuzzyMatch(query, Object.values(keymap));

  useInput((_, key) => {
    if (key.escape) onClose();
    if (key.return && matches[0]) onAction(matches[0]);
  }, { isActive: open });

  if (!open) return null;

  return (
    <Box position="absolute" top="20%" left="20%" width="60%"
         borderStyle="round" borderColor={theme.accent.primary}
         backgroundColor={theme.bg.overlay} padding={1} flexDirection="column">
      <Box><Text>: </Text><TextInput value={query} onChange={setQuery} /></Box>
      {matches.slice(0, 8).map((a, i) => (
        <Text key={a.key} color={i === 0 ? theme.accent.primary : undefined}
              backgroundColor={i === 0 ? theme.bg.selection : undefined}>
          {a.key.padEnd(8)} {a.label}
        </Text>
      ))}
    </Box>
  );
}
```

All three layers draw from the same `keymap` table → they cannot disagree.

---

## 11. Modals, confirmations, view-stack navigation

### Inline confirmation (lazygit pattern)

For destructive actions, the rule is **explicit-choice labels**, not `y/n` (parent SKILL.md §3, pattern 4):

```tsx
function ConfirmDelete({ target, onConfirm, onCancel }: ConfirmProps) {
  const [choice, setChoice] = useState<0 | 1>(1);   // default: cancel

  useInput((_, key) => {
    if (key.leftArrow || key.rightArrow) setChoice(c => (c === 0 ? 1 : 0));
    if (key.return) (choice === 0 ? onConfirm : onCancel)();
    if (key.escape) onCancel();
  });

  return (
    <Box flexDirection="column" borderStyle="round" borderColor={theme.status.error} padding={1}>
      <Text>Delete <Text bold>{target}</Text>?</Text>
      <Text dimColor>This cannot be undone.</Text>
      <Box marginTop={1} gap={2}>
        <Text inverse={choice === 0} color={theme.status.error}> Force delete </Text>
        <Text inverse={choice === 1}> Cancel </Text>
      </Box>
    </Box>
  );
}
```

Note: `inverse` (SGR 7) is the most reliable selection indicator across terminals — it works even in monochrome.

### View-stack navigation (tig pattern)

`Enter` drills, `Esc`/`q` pops. Implement as a stack in state, not as nested modals:

```tsx
type View = { kind: "list" } | { kind: "detail"; id: string } | { kind: "logs"; id: string };

function App() {
  const [stack, setStack] = useState<View[]>([{ kind: "list" }]);
  const top = stack[stack.length - 1];

  useInput((_, key) => {
    if (key.escape && stack.length > 1) setStack(s => s.slice(0, -1));
  });

  return (
    <>
      <Breadcrumb stack={stack} />
      {top.kind === "list"   && <List   onSelect={id => setStack(s => [...s, { kind: "detail", id }])} />}
      {top.kind === "detail" && <Detail id={top.id} onLogs={() => setStack(s => [...s, { kind: "logs", id: top.id }])} />}
      {top.kind === "logs"   && <Logs   id={top.id} />}
    </>
  );
}
```

Single source of truth, breadcrumb is derived, no modal nesting.

---

## 12. Inline vs alternate-screen mode

```tsx
render(<App />, { alternateScreen: false });  // claude-code style: stays in scrollback
render(<App />, { alternateScreen: true });   // vim / htop style: separate buffer
```

Inline is the default and the right call for:

- Coding agents, REPLs, anything where session output should remain readable after exit.
- Tools where the user might want to scroll back to prior renders.

Alternate-screen is the right call for:

- Full-screen editors and dashboards (htop, vim, btop).
- Tools where mixing live UI with scrollback would be confusing.
- Cases where you don't want the final frame to clutter the user's shell history.

Per the Ink readme: in alternate-screen mode, **teardown-time output is disposable** — `useStdout().write()` after unmount won't appear. Plan exit messages to render *before* unmount, or print them with plain `console.log` after `waitUntilExit()` resolves.

---

## 13. Rendering quality — the flicker fix

Ink 7 introduced `incrementalRendering` — this is the fix for "signature flicker" that plagued earlier Ink versions in long sessions.

```tsx
render(<App />, {
  maxFps: 30,                  // default; lower to 10–15 for very calm UIs to save CPU
  incrementalRendering: true,  // only redraw changed lines, not the full frame
  concurrent: true,            // React 19 Concurrent Mode — enables useTransition, Suspense
});
```

Recommendations:

- `incrementalRendering: true` for any TUI that updates more than once per second.
- `maxFps: 30` is the default. Set `15` if you have a dashboard that updates rarely; set `60` only if you have measured perceptible jank at 30 (rare in terminals).
- `concurrent: true` if you use `Suspense`, `useTransition`, or `useDeferredValue` — Ink 7 supports React Concurrent Mode. Without it those hooks degrade silently.

For very wide / very fast updates (logs, streaming output), prefer `<Static>` so finalized lines are emitted once and never re-laid-out:

```tsx
<Static items={completedLogs}>
  {(line, i) => <Text key={i}>{line}</Text>}
</Static>
{/* Live tail: */}
<Text dimColor>tail: {currentLine}</Text>
```

`<Static>` only renders new items; mutations to previously-rendered items are ignored. This is the path used by Gatsby's build log and Tap's test runner.

---

## 14. `render()` options matrix

| Option | Default | When to flip it |
|---|---|---|
| `exitOnCtrlC` | `true` | Set `false` only if you handle `Ctrl+C` manually (rare). |
| `patchConsole` | `true` | Keep `true`; Ink intercepts `console.*` so it doesn't shred the frame. |
| `maxFps` | `30` | Lower (10–15) for calm UIs; only raise if measured. |
| `incrementalRendering` | `false` | **Set `true`** for any TUI that updates frequently — flicker fix. |
| `concurrent` | `false` | Set `true` to use `Suspense`/`useTransition`/`useDeferredValue`. |
| `interactive` | auto | Override only if you have custom CI/TTY detection. In non-interactive mode, Ink skips ANSI cursor magic and emits only the final frame. |
| `alternateScreen` | `false` | Set `true` for vim/htop-style full-screen apps. |
| `kittyKeyboard` | `undefined` | Set `{ mode: "auto" }` for proper Tab/Ctrl+I, Shift+Enter, super/hyper key handling. |
| `debug` | `false` | Useful for printing every frame as a separate output (manual diff). |
| `isScreenReaderEnabled` | from env | Set explicitly to force on/off; honored by ARIA props. |

---

## 15. Accessibility

Ink 7 supports a subset of ARIA. Always set role + state on interactive elements:

```tsx
<Box aria-role="checkbox" aria-state={{ checked: isChecked, disabled: !canToggle }}>
  <Text>{isChecked ? "[x]" : "[ ]"} Enable feature</Text>
</Box>
```

Screen-reader output for the above: `(checked) checkbox: [x] Enable feature` (or similar).

Supported `aria-role` values: `button`, `checkbox`, `combobox`, `list`, `listbox`, `listitem`, `menu`, `menuitem`, `option`, `progressbar`, `radio`, `radiogroup`, `tab`, `tablist`, `table`, `textbox`, `timer`, `toolbar`.

Supported `aria-state` keys: `busy`, `checked`, `disabled`, `expanded`, `multiline`, `multiselectable`, `readonly`, `required`, `selected`.

Use `aria-label` for components that render visually but need a different description for screen readers (a progress bar that says "50%" should `aria-label="Progress: 50%"`).

For components that should be invisible to screen readers (purely decorative borders, dividers), set `aria-hidden`.

Detect screen reader at runtime:

```tsx
import { useIsScreenReaderEnabled } from "ink";

function ProgressBar({ value }: { value: number }) {
  const sr = useIsScreenReaderEnabled();
  if (sr) return <Text aria-label={`Progress: ${value}%`}>{value}%</Text>;
  return <Bar value={value} />;
}
```

---

## 16. Testing

```tsx
// tests/App.test.tsx
import { render } from "ink-testing-library";
import { App } from "../src/ui/App.js";

test("renders status panel", () => {
  const { lastFrame } = render(<App />);
  expect(lastFrame()).toContain("Status");
});

test("Tab moves focus", () => {
  const { stdin, lastFrame } = render(<App />);
  stdin.write("\t");
  expect(lastFrame()).toContain("Files"); // focus moved
});
```

`ink-testing-library` provides `lastFrame()`, `frames` (history), `stdin.write()`, and `rerender()`. Use it for:

- Snapshot-style assertions on rendered output.
- Keyboard simulation — `stdin.write("\t")` for Tab, `stdin.write("")` for Escape, `stdin.write("[A")` for Up arrow.
- Mode and overlay testing — drive the state through input events, assert on `lastFrame()`.

For pure layout/visual tests without a terminal, use Ink's own `renderToString(tree, { columns: 80 })` — returns a string synchronously, doesn't allocate stdin/stdout listeners.

---

## 17. Common Ink pitfalls

| Pitfall | Fix |
|---|---|
| Text outside `<Text>` causes runtime warnings | All text must be wrapped in `<Text>`. `<Box>` cannot contain raw strings. |
| Component re-renders every tick because of `useAnimation` | Don't use `useAnimation`'s return values to drive `useState`. Read them at render-time only. |
| `useEffect` async fetch fires twice in strict mode | Use the `cancelled` flag pattern (§8). Strict mode in React 19 runs effects twice; idempotent cleanup makes that safe. |
| Long lists tank performance | Use `ink-virtual-list` or paginate; Yoga walks every node. |
| Pasted text triggers Enter mid-paste | Use `usePaste` separately from `useInput` (§5). |
| Tab vs Ctrl+I conflated | Enable `kittyKeyboard: { mode: "auto" }`. |
| Spinners keep terminal awake on idle | Pass `isActive: loading` to `useAnimation`. |
| `console.log` from app code shreds the frame | `patchConsole: true` (default). For deliberate writes outside Ink, use `useStdout().write()`. |
| Output looks wrong when piped | Set `interactive: false` for piped/CI; emit final frame only. Ink does this automatically when `stdout.isTTY` is false. |
| Selection invisible in monochrome | Use `inverse` (SGR 7) for selection, not just color. |

---

## 18. Related references

- **Universal TUI design principles** — `design-principles.md` (this skill's sibling reference). Layout selection, color tiers, animation rules, the seven design principles.
- **Real-world precedent and the 18-tool catalog** — see the parent `SKILL.md` and the three cluster files (`cluster-a-devops.md`, `cluster-b-modern.md`, `cluster-c-monitors.md`) for direction archetypes, cross-cutting patterns, and ranked anti-patterns.
- **The agent CLI side** — see the `cli-creator` skill. The Node/TS + pnpm stack, JSON contract, lazy-loading the TUI from the same binary.

Re-verify the Ink version + peer requirements via `curl -s https://registry.npmjs.org/ink | jq '."dist-tags".latest, .versions[."dist-tags".latest].peerDependencies'` before scaffolding if it has been more than a few months since this file was updated.
