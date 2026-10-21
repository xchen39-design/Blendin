import { spawnSync } from 'node:child_process';
import { root, python } from './python.mjs';
const systemPython = process.env.PYTHON || (process.platform === 'win32' ? 'python' : 'python3');
for (const [command,args] of [[systemPython,['-m','venv','.venv']], [python,['-m','pip','install','-r','server/requirements.lock.txt']]]) {
  const result = spawnSync(command,args,{cwd:root,stdio:'inherit'});
  if (result.error || result.status !== 0) { console.error(result.error?.message || 'Setup failed. Requires Python 3.11+.'); process.exit(1); }
}
