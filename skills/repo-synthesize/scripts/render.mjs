#!/usr/bin/env node
/**
 * Render a repo-synthesize output directory into a self-contained HTML wiki.
 * Usage: node scripts/render.mjs <synthesis-dir>
 * Requires: pnpm, Node 18+
 */

import { execSync, spawnSync } from 'child_process';
import { readFileSync, writeFileSync, readdirSync, existsSync } from 'fs';
import { join, basename, extname, resolve } from 'path';

const synthDir = resolve(process.argv[2] ?? '');

if (!synthDir || !existsSync(synthDir)) {
  console.error('Usage: node render.mjs <synthesis-dir>');
  process.exit(1);
}

const PAGE_ORDER = [
  'overview', 'capabilities', 'architecture', 'api-surface',
  'data-model', 'frontend', 'background-jobs', 'deployment',
  'configuration', 'synthesis',
];

const mdFiles = readdirSync(synthDir)
  .filter(f => extname(f) === '.md')
  .sort((a, b) => {
    const ai = PAGE_ORDER.indexOf(basename(a, '.md'));
    const bi = PAGE_ORDER.indexOf(basename(b, '.md'));
    if (ai === -1 && bi === -1) return a.localeCompare(b);
    if (ai === -1) return 1;
    if (bi === -1) return -1;
    return ai - bi;
  });

if (mdFiles.length === 0) {
  console.error('No .md files found in', synthDir);
  process.exit(1);
}

function extractTitle(content) {
  const match = content.match(/^#\s+(.+)$/m);
  return match ? match[1] : null;
}

function convertMarkdown(content) {
  const mermaidBlocks = [];
  const withPlaceholders = content.replace(/```mermaid\n([\s\S]*?)```/g, (_, code) => {
    const idx = mermaidBlocks.length;
    mermaidBlocks.push(code.trim());
    return `MERMAID_BLOCK_${idx}_END`;
  });

  // pnpm dlx fetches marked and pipes content through it
  const html = execSync('pnpm dlx --yes marked --gfm', {
    input: withPlaceholders,
    encoding: 'utf8',
  });

  // marked may wrap placeholder text in <p> tags
  return html
    .replace(/<p>MERMAID_BLOCK_(\d+)_END<\/p>/g, (_, i) =>
      `<pre class="mermaid">${mermaidBlocks[parseInt(i)]}</pre>`
    )
    .replace(/MERMAID_BLOCK_(\d+)_END/g, (_, i) =>
      `<pre class="mermaid">${mermaidBlocks[parseInt(i)]}</pre>`
    );
}

console.log(`Rendering ${mdFiles.length} page(s) from ${synthDir}...`);

const pages = mdFiles.map(file => {
  const filePath = join(synthDir, file);
  const content = readFileSync(filePath, 'utf8');
  const id = basename(file, '.md');
  const title = extractTitle(content) ?? id;
  process.stdout.write(`  ${file} → `);
  const html = convertMarkdown(content);
  console.log('done');
  return { id, title, html };
});

const projectName = basename(synthDir).replace(/-synthesis$/, '');

const navItems = pages.map((p, i) =>
  `<li><a href="#" data-page="${p.id}"${i === 0 ? ' class="active"' : ''}>${p.title}</a></li>`
).join('\n        ');

const articleSections = pages.map((p, i) =>
  `<article id="page-${p.id}" class="page${i === 0 ? ' active' : ''}">\n${p.html}\n</article>`
).join('\n\n');

const output = `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>${projectName}</title>
  <script src="https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.min.js"></script>
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/highlight.js@11.9.0/styles/github.min.css">
  <script src="https://cdn.jsdelivr.net/npm/highlight.js@11.9.0/lib/core.min.js"></script>
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

    body {
      display: flex;
      min-height: 100vh;
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif;
      font-size: 15px;
      color: #24292f;
      background: #fff;
    }

    #sidebar {
      width: 240px;
      min-height: 100vh;
      background: #f6f8fa;
      border-right: 1px solid #d0d7de;
      padding: 24px 0;
      position: fixed;
      top: 0; left: 0; bottom: 0;
      overflow-y: auto;
    }

    #sidebar h1 {
      font-size: 13px;
      font-weight: 600;
      color: #57606a;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      padding: 0 16px 14px;
      border-bottom: 1px solid #d0d7de;
      margin-bottom: 8px;
      word-break: break-word;
    }

    #sidebar nav ul { list-style: none; }

    #sidebar nav a {
      display: block;
      padding: 6px 16px;
      font-size: 14px;
      color: #24292f;
      text-decoration: none;
      border-left: 3px solid transparent;
    }

    #sidebar nav a:hover { background: #eaeef2; }

    #sidebar nav a.active {
      color: #0969da;
      border-left-color: #0969da;
      background: #dbeafe;
      font-weight: 500;
    }

    #content {
      margin-left: 240px;
      flex: 1;
      padding: 40px 56px;
      max-width: 1100px;
    }

    .page { display: none; }
    .page.active { display: block; }

    .page h1 { font-size: 1.9em; font-weight: 600; margin-bottom: 16px; padding-bottom: 10px; border-bottom: 1px solid #d0d7de; }
    .page h2 { font-size: 1.35em; font-weight: 600; margin: 32px 0 10px; padding-bottom: 6px; border-bottom: 1px solid #d0d7de; }
    .page h3 { font-size: 1.1em; font-weight: 600; margin: 24px 0 8px; }
    .page h4 { font-size: 0.95em; font-weight: 600; margin: 18px 0 6px; }

    .page p { line-height: 1.75; margin: 12px 0; }
    .page ul, .page ol { padding-left: 24px; margin: 12px 0; }
    .page li { line-height: 1.7; margin: 4px 0; }
    .page a { color: #0969da; text-decoration: none; }
    .page a:hover { text-decoration: underline; }

    .page code {
      font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
      font-size: 0.875em;
      background: #f6f8fa;
      border: 1px solid #d0d7de;
      border-radius: 4px;
      padding: 1px 5px;
    }

    .page pre {
      background: #f6f8fa;
      border: 1px solid #d0d7de;
      border-radius: 6px;
      padding: 16px;
      overflow-x: auto;
      margin: 16px 0;
    }

    .page pre code { background: none; border: none; padding: 0; font-size: 0.85em; line-height: 1.6; }

    .page pre.mermaid {
      background: none;
      border: none;
      text-align: center;
      padding: 24px 0;
    }

    .page table { width: 100%; border-collapse: collapse; margin: 16px 0; font-size: 0.9em; }
    .page th { background: #f6f8fa; font-weight: 600; text-align: left; padding: 8px 12px; border: 1px solid #d0d7de; }
    .page td { padding: 8px 12px; border: 1px solid #d0d7de; vertical-align: top; }
    .page tr:nth-child(even) td { background: #f6f8fa; }

    .page blockquote { border-left: 4px solid #d0d7de; padding: 0 16px; color: #57606a; margin: 16px 0; }

    @media (max-width: 768px) {
      #sidebar { display: none; }
      #content { margin-left: 0; padding: 24px 20px; }
    }
  </style>
</head>
<body>

<aside id="sidebar">
  <h1>${projectName}</h1>
  <nav>
    <ul>
        ${navItems}
    </ul>
  </nav>
</aside>

<main id="content">

${articleSections}

</main>

<script>
  mermaid.initialize({ startOnLoad: false, theme: 'neutral', securityLevel: 'loose' });

  document.querySelectorAll('[data-page]').forEach(link => {
    link.addEventListener('click', e => {
      e.preventDefault();
      const id = link.dataset.page;
      document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
      document.querySelectorAll('[data-page]').forEach(l => l.classList.remove('active'));
      const page = document.getElementById('page-' + id);
      page.classList.add('active');
      link.classList.add('active');
      mermaid.run({ nodes: page.querySelectorAll('.mermaid') });
    });
  });

  const firstPage = document.querySelector('.page.active');
  if (firstPage) mermaid.run({ nodes: firstPage.querySelectorAll('.mermaid') });

  document.querySelectorAll('pre code').forEach(block => hljs.highlightElement(block));
</script>

</body>
</html>`;

const outPath = join(synthDir, 'index.html');
writeFileSync(outPath, output, 'utf8');
console.log(`\nWrote ${outPath}`);

const opener = spawnSync('open', [outPath]);
if (opener.status !== 0) {
  console.log(`Open in browser: file://${outPath}`);
}
