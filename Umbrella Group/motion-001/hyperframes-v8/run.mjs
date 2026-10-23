// Use project-local dependencies, or the existing pinned V7 runtime in this repo.
import {spawnSync} from 'node:child_process';
import {existsSync} from 'node:fs';
import {fileURLToPath} from 'node:url';
import {createRequire} from 'node:module';
const root=fileURLToPath(new URL('.',import.meta.url));
const dependencies=existsSync(new URL('node_modules/hyperframes/bin/hyperframes.mjs',import.meta.url))
  ?root:fileURLToPath(new URL('../hyperframes-v7/',import.meta.url));
const require=createRequire(dependencies+'package.json');
const env={...process.env,HYPERFRAMES_NO_TELEMETRY:'1',DO_NOT_TRACK:'1'};
if(!env.HYPERFRAMES_FFPROBE_PATH)env.HYPERFRAMES_FFPROBE_PATH=require('@ffprobe-installer/ffprobe').path;
if(process.platform==='win32'){
  const chrome='C:/Program Files/Google/Chrome/Application/chrome.exe';
  const ffmpeg='C:/Program Files/ShareX/ffmpeg.exe';
  if(!env.HYPERFRAMES_BROWSER_PATH&&existsSync(chrome))env.HYPERFRAMES_BROWSER_PATH=chrome;
  if(!env.HYPERFRAMES_FFMPEG_PATH&&existsSync(ffmpeg))env.HYPERFRAMES_FFMPEG_PATH=ffmpeg;
}
const r=spawnSync(process.execPath,[dependencies+'node_modules/hyperframes/bin/hyperframes.mjs',...process.argv.slice(2)],
  {cwd:root,env,stdio:'inherit',windowsHide:true});
if(r.error)throw r.error;process.exit(r.status??1);
