import { createRequire } from 'node:module';
import { readdirSync, readFileSync } from 'node:fs';
import { resolve, join } from 'node:path';
const require = createRequire(resolve('apps/web/package.json'));
const ts = require('typescript');
function files(dir) {
  return readdirSync(dir, { withFileTypes: true }).flatMap((entry) => entry.isDirectory() ? files(join(dir, entry.name)) : [join(dir, entry.name)]);
}
const errors = [];
for (const file of [...files('apps/web/src'), ...files('apps/web/tests'), ...files('packages/shared-types/src')]) {
  if (!/\.tsx?$/.test(file) || file.endsWith('generated-api.d.ts')) continue;
  const source = readFileSync(file, 'utf8');
  const tree = ts.createSourceFile(file, source, ts.ScriptTarget.Latest, true);
  let classes = 0;
  function visit(node) { if (ts.isClassDeclaration(node) || ts.isClassExpression(node)) classes++; ts.forEachChild(node, visit); }
  visit(tree);
  if (classes > 1) errors.push(`${file}: more than one handwritten class`);
  const components = tree.statements.filter((node) => (ts.isFunctionDeclaration(node) || ts.isClassDeclaration(node)) && node.name && /^[A-Z]/.test(node.name.text));
  if (file.startsWith('apps/web/src/') && file.endsWith('.tsx') && components.length > 1) errors.push(`${file}: more than one React component`);
  if (source.split('\n').length > 400) errors.push(`${file}: exceeds 400 lines`);
  if (file.startsWith('packages/shared-types/') && /from\s+['"].*(?:apps\/web|@mcp-workspace\/web)/.test(source)) errors.push(`${file}: shared types import web application`);
}
if (errors.length) { process.stderr.write(errors.join('\n') + '\n'); process.exit(1); }
process.stdout.write('Frontend class/component ownership checks passed\n');
