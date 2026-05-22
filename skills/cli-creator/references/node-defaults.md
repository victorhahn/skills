# Node / TypeScript Defaults

The exact package choices, project layout, and install patterns for a production-grade Node/TS CLI. This skill is opinionated: one stack, well-tuned. Diverge only with explicit reason.

---

## Package Manager — pnpm

**Always prefer `pnpm`.** Reasons:

- Strict by default — no phantom dependencies, fewer surprises in CI.
- Fast and disk-efficient (content-addressable store).
- Workspaces are first-class — useful when the CLI grows a TUI side or a shared types package.
- Compatible with everything `npm` does; the only switch users have to remember is `pnpm` instead of `npm`.

```bash
# Detect what's available; prefer pnpm
command -v pnpm npm tsx node || true
```

If `pnpm` is missing, install it (`corepack enable && corepack prepare pnpm@latest --activate`) rather than fall back to `npm`. This skill is pnpm-first by default.

**Never use `npx`.** Use `pnpm dlx` for one-shot package execution. Where the CLI itself ships an executable, prefer linking it (`pnpm link --global`) over re-running through `npx`.

**Lockfile:** commit `pnpm-lock.yaml`. Never commit `package-lock.json` or `yarn.lock` alongside it.

---

## Project Layout

```
my-cli/
├── package.json
├── pnpm-lock.yaml
├── tsconfig.json
├── tsup.config.ts
├── biome.json                  # or .prettierrc + .eslintrc if repo convention demands
├── README.md
├── src/
│   ├── index.ts                # entrypoint, dispatches to commands
│   ├── cli.ts                  # commander/cac wiring
│   ├── commands/
│   │   ├── doctor.ts
│   │   ├── list-*.ts
│   │   ├── get-*.ts
│   │   └── ...
│   ├── lib/
│   │   ├── http.ts             # native fetch wrapper, auth header injection
│   │   ├── config.ts           # config loading (env > file > flag)
│   │   ├── json.ts             # JSON envelope helpers (success / error)
│   │   └── errors.ts           # typed error classes
│   ├── ui/                     # only if the CLI also has a TUI surface (Ink)
│   │   └── App.tsx
│   └── types.ts                # generated from OpenAPI or zod schemas
├── tests/
│   └── *.test.ts
└── Makefile                    # install-local, build, test, lint
```

**Notes:**

- `src/cli.ts` defines the command surface; `src/commands/*` are pure functions that take parsed args and return JSON-shaped values. The CLI layer handles `--json` vs human rendering.
- `src/lib/http.ts` is the only place that calls `fetch()`. Centralized auth, retry, and error parsing live here.
- Keep `src/ui/` out of the agent path. Import lazily so `--json` runs don't even load Ink.

---

## package.json Skeleton

```json
{
  "name": "<tool-name>",
  "version": "0.1.0",
  "type": "module",
  "bin": { "<tool-name>": "./dist/index.js" },
  "engines": { "node": ">=20" },
  "files": ["dist", "README.md"],
  "scripts": {
    "build": "tsup src/index.ts --format esm --dts --clean",
    "dev": "tsx src/index.ts",
    "test": "vitest run",
    "test:watch": "vitest",
    "typecheck": "tsc --noEmit",
    "lint": "biome check .",
    "lint:fix": "biome check --write .",
    "prepublishOnly": "pnpm build"
  },
  "dependencies": {
    "commander": "^12"
  },
  "devDependencies": {
    "@biomejs/biome": "^1",
    "@types/node": "^20",
    "tsup": "^8",
    "tsx": "^4",
    "typescript": "^5",
    "vitest": "^2"
  }
}
```

**Hard preferences:**

- `"type": "module"` — ESM. The Node 20+ ecosystem is ESM-first.
- `"engines": { "node": ">=20" }` — lets you use native `fetch`, `crypto.subtle`, top-level await, and `import.meta`.
- Native `fetch` over `axios`, `node-fetch`, or `got` — unless there's a concrete reason (advanced retry, HTTP/2, etc.).
- `commander` for argument parsing — well-maintained, decent help output. Use `cac` only if you need a smaller bundle.
- `biome` for lint+format in a single tool — fast, zero-config. Only fall back to ESLint+Prettier if the surrounding repo demands it.
- `vitest` for tests. Faster than Jest, no config for TS, ESM-native.
- `zod` only if external payload validation prevents real breakage (untrusted input, contract-fragile API). Skip for internal-only services.

---

## TypeScript Config

```json
// tsconfig.json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "ESNext",
    "moduleResolution": "Bundler",
    "lib": ["ES2022"],
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "exactOptionalPropertyTypes": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "verbatimModuleSyntax": true,
    "declaration": true,
    "outDir": "dist"
  },
  "include": ["src"],
  "exclude": ["node_modules", "dist", "tests"]
}
```

`noUncheckedIndexedAccess` and `exactOptionalPropertyTypes` are non-negotiable for a CLI — they catch the exact class of bugs that cause "works on my machine, breaks on a fresh install."

---

## Build — tsup

```ts
// tsup.config.ts
import { defineConfig } from "tsup";

export default defineConfig({
  entry: ["src/index.ts"],
  format: ["esm"],
  target: "node20",
  dts: true,
  clean: true,
  shims: true,            // adds __dirname/__filename shims for ESM
  banner: { js: "#!/usr/bin/env node" },
});
```

The `banner` line makes the compiled `dist/index.js` directly executable on a Unix shebang — no wrapper script needed.

---

## Install Patterns

### Personal / local install (preferred)

```makefile
# Makefile
.PHONY: build install-local link clean

build:
	pnpm install --frozen-lockfile
	pnpm build

install-local: build
	pnpm link --global
	@echo "Installed: $$(command -v $(BIN_NAME))"

link: install-local

clean:
	rm -rf dist node_modules
```

After `make install-local`, the binary works from any directory because `pnpm link --global` puts a symlink into pnpm's global bin dir (which should already be on PATH).

### Alternative — `~/.local/bin` wrapper

Use when `pnpm link --global` isn't desired (e.g., shared machine, isolated install):

```makefile
install-local: build
	@mkdir -p ~/.local/bin
	@printf '#!/bin/sh\nexec node %s/dist/index.js "$$@"\n' "$$(pwd)" > ~/.local/bin/$(BIN_NAME)
	@chmod +x ~/.local/bin/$(BIN_NAME)
	@echo "Installed: $$(command -v $(BIN_NAME))"
```

### Publishing

When ready for `pnpm install -g <tool-name>`:

1. `pnpm publish --access public` (or `--access restricted` for internal scopes).
2. Verify with `pnpm dlx <tool-name> --help` from a clean directory.

---

## HTTP Layer Pattern

```ts
// src/lib/http.ts
import { loadConfig } from "./config.js";

export type ApiOptions = {
  method?: "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
  body?: unknown;
  query?: Record<string, string | number | boolean | undefined>;
};

export async function api<T>(path: string, opts: ApiOptions = {}): Promise<T> {
  const { token, baseUrl } = loadConfig();
  const url = new URL(path, baseUrl);
  for (const [k, v] of Object.entries(opts.query ?? {})) {
    if (v !== undefined) url.searchParams.set(k, String(v));
  }

  const res = await fetch(url, {
    method: opts.method ?? "GET",
    headers: {
      ...(token ? { authorization: `Bearer ${token}` } : {}),
      ...(opts.body ? { "content-type": "application/json" } : {}),
      accept: "application/json",
    },
    body: opts.body ? JSON.stringify(opts.body) : undefined,
  });

  if (!res.ok) {
    const body = await res.text();
    throw new ApiError(res.status, res.statusText, body);
  }
  return (await res.json()) as T;
}

export class ApiError extends Error {
  constructor(public status: number, public statusText: string, public body: string) {
    super(`${status} ${statusText}`);
  }
}
```

Keep it boring. Native `fetch`, JSON in and JSON out, one typed error class.

---

## JSON Envelope Helpers

```ts
// src/lib/json.ts
export type Ok<T> = { data: T; meta?: Record<string, unknown> };
export type Err = { error: { code: string; message: string; status?: number } };

export function ok<T>(data: T, meta?: Record<string, unknown>): Ok<T> {
  return meta ? { data, meta } : { data };
}

export function err(code: string, message: string, status?: number): Err {
  return { error: status !== undefined ? { code, message, status } : { code, message } };
}

export function emit(obj: unknown): never {
  process.stdout.write(JSON.stringify(obj) + "\n");
  process.exit("error" in (obj as object) ? 1 : 0);
}
```

The agent path is always `console.log(JSON.stringify(...))`. Never mix `console.error` or progress text into a `--json` run.

---

## Test Conventions

- `vitest` with `--run` in CI, `vitest` (watch) locally.
- Unit-test the request builder, pagination, and the JSON envelope helpers.
- Mock `fetch` with the global `vi.stubGlobal("fetch", ...)` — don't pull in `msw` unless multiple suites share fixtures.
- One integration test that runs `doctor` with no auth and asserts `missing_setup` is populated.
- Smoke test in the Makefile: `make install-local && cd /tmp && <tool-name> --help && <tool-name> --json doctor`.

---

## When the CLI Also Needs a TUI (Ink)

If `<tool>` (without `--json`) should open a polished interactive surface, add Ink lazily:

```ts
// src/index.ts
if (process.argv.includes("--json") || hasJsonSubcommand(process.argv)) {
  await runAgentPath();
} else if (isInteractiveCommand(process.argv)) {
  const { runTui } = await import("./ui/runTui.js");  // lazy — keeps agent path lean
  await runTui();
} else {
  await runAgentPath();  // default: still JSON-friendly
}
```

**Current stable versions (verified against npm registry):**

| Package | Version | Notes |
|---|---|---|
| `ink` | `^7.0` | Node 22+, React 19.2+ peer |
| `react` | `^19.2` | Required by Ink 7 |
| `ink-text-input` | `^6.0` | |
| `ink-select-input` | `^6.2` | |
| `ink-spinner` | `^5.0` | |
| `ink-testing-library` | `^4.0` | dev-only |

If the CLI uses Ink, bump `"engines"` to `"node": ">=22"`. The pure agent path can stay at Node 20+; the bump is Ink's requirement, not the CLI's.

```bash
pnpm add ink@^7 react@^19
pnpm add -D @types/react ink-testing-library@^4
```

Always **verify the current `latest` tag before scaffolding**. Ink moves through majors fairly often — check `https://registry.npmjs.org/ink` for `dist-tags.latest` rather than relying on this doc for the exact version. The shape of the API stays similar across majors but peer requirements (React, Node) drift.

Design the TUI surface using the `tui-creator` skill — it covers layout, focus, color, animation, real-world precedent across 18 reference TUIs, and Ink 7 / React 19 implementation recipes.
