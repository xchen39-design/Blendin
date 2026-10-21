import { spawn } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { existsSync } from 'node:fs';
export const root = fileURLToPath(new URL('../', import.meta.url));
export const python = fileURLToPath(new URL(process.platform === 'win32' ? '../.venv/Scripts/python.exe' : '../.venv/bin/python', import.meta.url));
if (process.argv[1] === fileURLToPath(import.meta.url)) {
  if (!existsSync(python)) { console.error('Run npm run setup first.'); process.exit(1); }
  const child = spawn(python, process.argv.slice(2), {cwd:root, stdio:'inherit'});
  child.on('error', error => {console.error(error.message); process.exitCode=1;});
  child.on('exit', code => {process.exitCode=code ?? 1;});
}
