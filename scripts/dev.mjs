import { spawn } from 'node:child_process';
import { existsSync } from 'node:fs';
import { root, python } from './python.mjs';
if (!existsSync(python)) {console.error('Run npm run setup first.');process.exit(1);}
const children = [spawn(python,['-m','uvicorn','server.main:app','--host','127.0.0.1','--port','8001','--reload'],{cwd:root,stdio:'inherit'}),spawn(process.platform==='win32'?'npm.cmd':'npm',['run','dev','--workspace','client'],{cwd:root,stdio:'inherit',shell:process.platform==='win32'})];
let stopping=false;
function stop(code=0){if(stopping)return;stopping=true;children.forEach(child=>child.kill());process.exitCode=code;}
for(const child of children){child.on('error',error=>{console.error(error.message);stop(1)});child.on('exit',code=>stop(code||0));}
process.on('SIGINT',()=>stop());process.on('SIGTERM',()=>stop());
