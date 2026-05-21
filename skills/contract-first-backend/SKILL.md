---
name: contract-first-backend
description: Bootstrap and work with contract-first TypeScript/Express backends where openapi.yaml is the source of truth and all types, runtime validation, and consumer clients are generated from the spec. Use when setting up a new service, adding routes, updating schemas, or generating typed clients.
category: framework
risk: low
source: local
date_added: '2026-05-16'
---

# Contract-First TypeScript Backend

You are an expert at contract-first API development using TypeScript, Express v5, and OpenAPI. The core principle: **`openapi.yaml` is edited by hand; everything else is generated from it.**

## When invoked

Determine the user's goal and act accordingly:

- **New project** → scaffold the full boilerplate (see Scaffolding)
- **Add a route** → walk through the spec-first workflow
- **Update a schema** → update spec, regenerate, fix handlers
- **Generate a client** → pick the right codegen tool for the consumer
- **Debug a validation error** → diagnose spec vs handler mismatch

Read `openapi.yaml`, `src/types/api.gen.ts`, and `src/types/helpers.ts` before writing any code. The existing spec and generated types are authoritative.

---

## Core stack

| Concern | Tool |
|---|---|
| Runtime validation | `express-openapi-validator` (reads spec at startup, enforces every req/res) |
| Type generation | `openapi-typescript` (generates `src/types/api.gen.ts`) |
| Type utilities | `src/types/helpers.ts` (ReqBody / ResBody / PathParams / QueryParams) |
| Framework | Express v5 (async handlers, no try-catch needed) |
| Testing | Vitest + supertest |
| Lint/format | Biome |
| Package manager | pnpm |

---

## Scaffolding a new project

When bootstrapping from scratch, create this structure:

```
my-service/
├── openapi.yaml
├── src/
│   ├── types/
│   │   ├── api.gen.ts        ← generated (gitignored)
│   │   └── helpers.ts
│   ├── routes/
│   │   └── <resource>.ts
│   ├── middleware/
│   │   └── error-handler.ts
│   ├── app.ts
│   └── server.ts
├── test/
│   └── <resource>.test.ts
├── package.json
├── tsconfig.json
├── biome.json
└── .gitignore
```

### `package.json`

```json
{
  "name": "my-service",
  "version": "0.1.0",
  "type": "module",
  "packageManager": "pnpm@9.0.0",
  "scripts": {
    "generate": "openapi-typescript openapi.yaml -o src/types/api.gen.ts",
    "predev": "pnpm generate",
    "dev": "tsx watch src/server.ts",
    "start": "tsx src/server.ts",
    "typecheck": "tsc --noEmit",
    "lint": "biome check .",
    "format": "biome format --write .",
    "test": "vitest run",
    "test:watch": "vitest"
  },
  "dependencies": {
    "express": "^5.1.0",
    "express-openapi-validator": "^5.4.6"
  },
  "devDependencies": {
    "@biomejs/biome": "^1.9.4",
    "@types/express": "^5.0.1",
    "@types/node": "^22.13.0",
    "@types/supertest": "^6.0.2",
    "openapi-typescript": "^7.6.1",
    "supertest": "^7.0.0",
    "tsx": "^4.19.3",
    "typescript": "^5.7.3",
    "vitest": "^3.0.4"
  }
}
```

### `tsconfig.json`

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "Preserve",
    "moduleResolution": "Bundler",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "noEmit": true,
    "resolveJsonModule": true
  },
  "include": ["src", "test", "vitest.config.ts"]
}
```

### `biome.json`

```json
{
  "$schema": "https://biomejs.dev/schemas/1.9.4/schema.json",
  "organizeImports": { "enabled": true },
  "linter": { "enabled": true, "rules": { "recommended": true } },
  "formatter": { "enabled": true, "indentStyle": "space", "indentWidth": 2, "lineWidth": 100 },
  "files": { "ignore": ["src/types/api.gen.ts", "node_modules"] }
}
```

### `src/types/helpers.ts`

```typescript
import type { operations } from './api.gen'

export type ReqBody<Op extends keyof operations> =
  operations[Op] extends { requestBody: { content: { 'application/json': infer B } } }
    ? B
    : never

export type ResBody<Op extends keyof operations, S extends number = 200> =
  operations[Op] extends { responses: { [K in S]: { content: { 'application/json': infer R } } } }
    ? R
    : never

export type PathParams<Op extends keyof operations> =
  operations[Op] extends { parameters: { path: infer P } }
    ? P
    : Record<string, string>

export type QueryParams<Op extends keyof operations> =
  operations[Op] extends { parameters: { query?: infer Q } }
    ? NonNullable<Q>
    : never
```

### `src/middleware/error-handler.ts`

```typescript
import type { ErrorRequestHandler } from 'express'

interface OpenApiValidatorError extends Error {
  status?: number
  errors?: Array<{ path: string; message: string }>
}

export const errorHandler: ErrorRequestHandler = (err: OpenApiValidatorError, _req, res, _next) => {
  const status = err.status ?? 500
  res.status(status).json({
    message: err.message,
    ...(err.errors && { errors: err.errors }),
  })
}
```

### `src/app.ts`

```typescript
import express from 'express'
import { middleware as openApiValidator } from 'express-openapi-validator'
import { fileURLToPath } from 'node:url'
import { dirname, join } from 'node:path'
import { errorHandler } from './middleware/error-handler'
// import { widgetsRouter } from './routes/widgets'

const __dirname = dirname(fileURLToPath(import.meta.url))

export function createApp() {
  const app = express()

  app.use(express.json())

  app.use(
    openApiValidator({
      apiSpec: join(__dirname, '../openapi.yaml'),
      validateRequests: true,
      validateResponses: process.env.NODE_ENV !== 'production',
    }),
  )

  app.get('/health', (_req, res) => {
    res.json({ status: 'ok' })
  })

  // app.use('/widgets', widgetsRouter)

  app.use(errorHandler)
  return app
}
```

### `src/server.ts`

```typescript
import { createApp } from './app'

const port = Number(process.env.PORT ?? 3000)
createApp().listen(port, () => console.log(`listening on http://localhost:${port}`))
```

---

## Adding a route

### Step 1 — Edit `openapi.yaml`

Always include:
- A unique `operationId` (drives the type helpers)
- All response codes the handler can return
- Schemas for all request bodies and responses

```yaml
/widgets/{id}:
  parameters:
    - in: path
      name: id
      required: true
      schema:
        type: string
  get:
    operationId: getWidget
    summary: Get a widget
    responses:
      '200':
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/Widget'
      '404':
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/Error'
```

### Step 2 — Regenerate types

```bash
pnpm generate
```

### Step 3 — Write the handler

```typescript
import { Router } from 'express'
import type { RequestHandler } from 'express'
import type { ResBody, PathParams } from '../types/helpers'

export const widgetStore = new Map<string, ResBody<'getWidget'>>()
const router = Router()

const getWidget: RequestHandler<PathParams<'getWidget'>, ResBody<'getWidget'> | { message: string }> = (req, res) => {
  const item = widgetStore.get(req.params.id)
  if (!item) {
    res.status(404).json({ message: 'Widget not found' })
    return
  }
  res.json(item)
}

router.get('/:id', getWidget)
export { router as widgetsRouter }
```

### Step 4 — Mount in `src/app.ts`

```typescript
import { widgetsRouter } from './routes/widgets'
app.use('/widgets', widgetsRouter)
```

### Step 5 — Write tests

```typescript
import { describe, it, expect, beforeEach } from 'vitest'
import supertest from 'supertest'
import { createApp } from '../src/app'
import { widgetStore } from '../src/routes/widgets'

const req = supertest(createApp())
beforeEach(() => widgetStore.clear())

it('returns 404 for unknown id', async () => {
  const res = await req.get('/widgets/nope')
  expect(res.status).toBe(404)
})
```

---

## Updating a schema

1. Change the schema in `openapi.yaml`
2. Run `pnpm generate`
3. TypeScript errors surface every handler/test that broke — fix them
4. Run `pnpm test` to confirm runtime validation still passes

**Adding a required field to a response:** handlers returning that resource must include the new field. TypeScript will error if they don't.

**Making a field optional:** no breaking change to handlers, but tests asserting on that field may need updating.

**Renaming a field:** `pnpm generate` causes type errors everywhere the old name is used — TypeScript guides you to every callsite.

---

## Generating consumer clients

All consumers derive from `openapi.yaml`. Run these from the service root.

### TypeScript — fetch client (zero runtime deps)

```bash
pnpm add openapi-fetch
pnpm dlx openapi-typescript openapi.yaml -o client/api.gen.ts
```

```typescript
import createClient from 'openapi-fetch'
import type { paths } from './client/api.gen'

const client = createClient<paths>({ baseUrl: 'http://localhost:3000' })

// Fully typed — params, body, and response
const { data, error } = await client.GET('/widgets/{id}', {
  params: { path: { id: 'abc' } },
})
```

### TypeScript — React Query hooks (Orval)

```bash
pnpm add -D orval
```

`orval.config.ts`:
```typescript
import { defineConfig } from 'orval'
export default defineConfig({
  myApi: {
    input: { target: 'openapi.yaml' },
    output: {
      mode: 'single',
      target: 'client/api.ts',
      client: 'react-query',
    },
  },
})
```

### Go SDK

`sdk.cfg.yaml`:
```yaml
package: mysdk
generate:
  models: true
  client: true
output: pkg/sdk/client.gen.go
```

```bash
go run github.com/oapi-codegen/oapi-codegen/v2/cmd/oapi-codegen \
  --config sdk.cfg.yaml openapi.yaml
```

### Python / any language

```bash
pnpm dlx @openapitools/openapi-generator-cli generate \
  -i openapi.yaml -g python -o client/python/
```

### MCP tool definitions

OpenAPI operation schemas map directly to MCP tool definitions. Pass `openapi.yaml` to any MCP codegen tool, or hand-write the mapping using the spec's `operationId`, `parameters`, and `requestBody` as the tool's `name`, `inputSchema`.

---

## Debugging validation errors

### 400 on a valid-looking request

Run `pnpm generate` — the validator reads the _file_, not the generated types. They may have drifted.

Check the error response body — `express-openapi-validator` returns structured errors:
```json
{
  "message": "request/body must have required property 'name'",
  "errors": [{ "path": "/body/name", "message": "..." }]
}
```

### 500 with a validator message (dev only)

The handler returned a response that doesn't match the spec. Check `err.message` — it will name the field and path. Fix the handler's response shape, not the spec (unless the spec is wrong).

### Route returns 404 from the validator (not your handler)

The path or method isn't defined in the spec. The validator rejects unknown routes before they reach your router. Add the route to `openapi.yaml` first.

---

## Key invariants to preserve

- `src/types/api.gen.ts` is always gitignored and regenerated — never hand-edit it
- Every route in `app.ts` must have a corresponding path in `openapi.yaml` or the validator will 404 it
- `operationId` must be globally unique across the spec — the type helpers key off it
- `validateResponses` stays off in production — it adds overhead and can 500 on edge cases not worth guarding in prod
- Store/repository state must be clearable between tests — use `beforeEach(() => store.clear())` or inject a test double
