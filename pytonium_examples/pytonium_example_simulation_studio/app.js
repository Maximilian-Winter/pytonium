import {Viewport} from './renderer.js';
const $=id=>document.getElementById(id);
const names={gathering:'Gathering',crossing:'Crossing streams',obstacle:'Around the obstacle'};
const presets={gathering:{separation:1.5,alignment:1,cohesion:.8,obstacle:false},crossing:{separation:2,alignment:.6,cohesion:.4,obstacle:false},obstacle:{separation:1.7,alignment:1.2,cohesion:.8,obstacle:true}};
const defaults={population:500,seed:42,separation:1.5,alignment:1,cohesion:.8,radius:10,speed:12,obstacle:false,preset:'gathering'};
let config={...defaults},status={mode:'live',paused:false,time:0,recording:false},runs=[],experiments=[],history=[],generation=null,sequence=-1,ready=false;
const selectedRuns=new Set(),pending=new Map();let fileMode=null,fileRun=null,folder='',selectedFile='',cameraDriver=0;
const notify=message=>{$('notice').hidden=false;$('notice').querySelector('span').textContent=message;};
$('notice').querySelector('button').onclick=()=>{$('notice').hidden=true;};
async function command(action,args={}){
  if(!ready){notify('The Python bridge is not ready. Launch this app with python main.py.');return null;}
  try{const response=await Pytonium.studio.command(action,args);if(!response.accepted){notify(response.error);return null;}return response.id;}
  catch(error){notify(`Could not send command: ${error.message}`);return null;}
}
let view,second;
try{view=new Viewport($('scene'),id=>{command('select',{id});$('selection').textContent=`Agent ${id+1} · nearby agents highlighted when Neighborhood is enabled`;});}
catch(error){notify(`3D rendering could not start: ${error.message}. Check graphics drivers and WebGL support.`);}
function ensureSecond(){if(!second){second=new Viewport($('scene-b'),id=>{$('selection').textContent=`Agent ${id+1} selected in comparison`;});second.overlays=$('neighbors').checked;second.trails=$('trails').checked;}return second;}
$('scene').addEventListener('pointerdown',()=>cameraDriver=0);$('scene-b').addEventListener('pointerdown',()=>cameraDriver=1);
$('scene').addEventListener('wheel',()=>cameraDriver=0);$('scene-b').addEventListener('wheel',()=>cameraDriver=1);
function cameraLoop(){if(second&&status.mode==='compare'){if(cameraDriver) view?.sync(second);else if(view)second.sync(view);}requestAnimationFrame(cameraLoop);}cameraLoop();
setInterval(()=>{if(view)$('render-stats').textContent=`${Math.round(view.engine.getFps())} fps · ${view.count} agents`;},1000);
const controls=[['separation','Separation',0,4,.1,'Give close neighbors more room.'],['alignment','Alignment',0,4,.1,'Match the surrounding direction and speed.'],['cohesion','Cohesion',0,4,.1,'Steer toward the local group.'],['radius','Neighborhood radius',3,20,.5,'How far each agent can sense.'],['speed','Speed limit',2,25,.5,'Maximum speed in world units per second.']];
for(const [key,label,min,max,step,hint]of controls){const box=document.createElement('div');box.className='slider-control';const row=document.createElement('div');row.className='slider-label';const l=document.createElement('label');l.htmlFor=key;l.textContent=label;const out=document.createElement('output');out.id=`${key}-value`;const input=document.createElement('input');Object.assign(input,{id:key,type:'range',min,max,step,value:config[key]});out.value=config[key];row.append(l,out);const p=document.createElement('p');p.textContent=hint;box.append(row,input,p);$('sliders').append(box);input.oninput=()=>out.value=input.value;input.onchange=()=>command('configure',{changes:{[key]:Number(input.value)}});}
function setControls(c){config={...c};for(const[key]of controls){if(document.activeElement!==$(key))$(key).value=c[key];$(`${key}-value`).value=c[key];}for(const key of ['population','seed','preset']){if(document.activeElement!==$(key))$(key).value=c[key];}$('obstacle').checked=c.obstacle;}
function resetConfig(){return {...config,population:Number($('population').value),seed:Number($('seed').value),preset:$('preset').value};}
$('preset').onchange=()=>{const p=$('preset').value;config={...config,...presets[p],preset:p};for(const[key]of controls){$(key).value=config[key];$(`${key}-value`).value=config[key];}$('obstacle').checked=config.obstacle;};
$('obstacle').onchange=()=>command('configure',{changes:{obstacle:$('obstacle').checked}});
$('reset').onclick=()=>command('reset',{config:resetConfig()});
$('new').onclick=()=>command('reset',{config:{...defaults}});
$('use-settings').onclick=()=>command('reset',{config:{...config}});
$('play').onclick=()=>command('pause',{paused:!status.paused});$('step').onclick=()=>command('step');
$('speed').onchange=()=>command('speed',{value:Number($('speed').value)});
$('record').onclick=()=>command(status.recording?'stop_recording':'record',status.recording?{}:{name:$('record-name').value.trim()||`${names[config.preset]} experiment`});
let seekTimer;$('seek').oninput=()=>{clearTimeout(seekTimer);seekTimer=setTimeout(()=>command('seek',{time:Number($('seek').value)}),40);};
$('camera').onclick=()=>{view?.resetCamera();second?.resetCamera();};
$('trails').onchange=()=>{if(view)view.trails=$('trails').checked;if(second)second.trails=$('trails').checked;};
$('neighbors').onchange=()=>{if(view)view.overlays=$('neighbors').checked;if(second)second.overlays=$('neighbors').checked;$('vector-legend').hidden=!$('neighbors').checked;};
$('toggle-inspector').onclick=()=>{const hidden=document.body.classList.toggle('inspector-hidden');$('toggle-inspector').textContent=hidden?'Show controls':'Hide controls';$('toggle-inspector').setAttribute('aria-expanded',String(!hidden));};
$('help').onclick=()=>$('guide').showModal();
document.addEventListener('keydown',event=>{if(event.code==='Space'&&!['INPUT','SELECT','TEXTAREA','BUTTON'].includes(document.activeElement.tagName)&&!document.querySelector('dialog[open]')){event.preventDefault();$('play').click();}});
function updateStatus(s){
  status=s;$('connection').textContent='Python connected';$('mode').textContent=s.mode==='live'?'LIVE OBSERVATION':s.mode==='compare'?'COMPARING EXPERIMENTS':'RECORDED EXPERIMENT';
  $('play').textContent=s.paused?'Play':'Pause';$('step').disabled=s.mode!=='live'||!s.paused;$('clock').textContent=`${s.time.toFixed(2)} s`;$('speed').value=s.speed;
  $('record').textContent=s.recording?'■ Save recording':'● Record';$('record').classList.toggle('recording',s.recording);$('record').disabled=s.mode!=='live';$('record-name').disabled=s.recording||s.mode!=='live';
  $('parameters').disabled=s.mode!=='live';$('use-settings').hidden=s.mode==='live';$('seek').disabled=s.mode==='live';$('seek').max=s.duration||1;if(document.activeElement!==$('seek'))$('seek').value=s.time;
  $('timeline-label').textContent=s.recording?`Recording ${s.recorded.toFixed(1)} / 120 s · parameter changes are included`:s.mode==='live'?'Live simulation · record to create a replay':`${s.time.toFixed(1)} / ${s.duration.toFixed(1)} s · scrub to explore`;
  $('second-view').hidden=s.mode!=='compare';if(s.mode==='compare')ensureSecond();
  if(s.mode==='live')$('label-a').textContent=names[config.preset];
}
async function ask(title,text,value=null){const d=$('confirm-dialog');$('confirm-title').textContent=title;$('confirm-text').textContent=text;$('confirm-input').hidden=value===null;$('confirm-input').value=value||'';d.returnValue='';d.showModal();return new Promise(resolve=>d.addEventListener('close',()=>resolve(d.returnValue==='ok'?(value===null?true:$('confirm-input').value):null),{once:true}));}
function button(label,action){const b=document.createElement('button');b.textContent=label;b.onclick=action;return b;}
function renderLibrary(library){
  runs=library.runs;for(const id of selectedRuns)if(!runs.some(r=>r.id===id))selectedRuns.delete(id);$('runs').replaceChildren();
  if(!runs.length){const p=document.createElement('p');p.className='empty';p.textContent='Your first experiment starts here. Give the flock a name and press Record.';$('runs').append(p);}
  for(const run of runs){const item=document.createElement('article');item.className='run';const heading=document.createElement('div');heading.className='run-title';const check=document.createElement('input');check.type='checkbox';check.id=`run-${run.id}`;check.checked=selectedRuns.has(run.id);check.onchange=()=>{if(check.checked){if(selectedRuns.size===2){check.checked=false;notify('Choose at most two experiments to compare.');return;}selectedRuns.add(run.id);}else selectedRuns.delete(run.id);updateCompare();};const label=document.createElement('label');label.htmlFor=check.id;label.textContent=run.name;heading.append(check,label);const meta=document.createElement('div');meta.className='meta';meta.textContent=`${run.duration.toFixed(1)} s · ${run.config.population} agents`;const actions=document.createElement('div');actions.className='run-actions';actions.append(button('Replay',()=>command('replay',{ids:[run.id]})),button('Rename',async()=>{const name=await ask('Rename experiment','Choose a name you will recognize.',run.name);if(name!==null)command('rename',{id:run.id,name});}),button('Archive',()=>openFiles('archive',run)),button('CSV',()=>openFiles('csv',run)),button('Delete',async()=>{if(await ask('Delete experiment?',`Delete “${run.name}” from your library? This cannot be undone.`))command('delete',{id:run.id});}));item.append(heading,meta,actions);$('runs').append(item);}
  updateCompare();if(library.errors.length)notify(library.errors.join(' '));
}
function updateCompare(){$('compare').disabled=selectedRuns.size!==2;$('compare').textContent=`Compare selected (${selectedRuns.size}/2)`;}
$('compare').onclick=()=>command('compare',{ids:[...selectedRuns]});
function renderExperiments(value){experiments=value;$('markers').replaceChildren();if(!value.length)return;$('label-a').textContent=value[0].metadata.name;if(value[1])$('label-b').textContent=value[1].metadata.name;
  const duration=Math.max(...value.map(r=>r.metadata.duration),.001);for(const [i,run]of value.entries())for(const event of run.metadata.events){const marker=button('',()=>command('seek',{time:event.time}));marker.className='event-marker';marker.style.left=`${event.time/duration*100}%`;marker.style.top=`${i*4}px`;marker.title=`${event.time.toFixed(2)} s · ${run.metadata.name}: ${Object.entries(event.changes).map(([k,v])=>`${k} ${v}`).join(', ')}`;marker.setAttribute('aria-label',marker.title);$('markers').append(marker);}charts();}
function charts(){const series=status.mode==='live'?[history]:experiments.map(r=>r.metrics);const colors=['#a56540','#3f859e'];for(let metric=0;metric<3;metric++){const svg=$(`chart-${metric}`);svg.replaceChildren();const values=series.flatMap(s=>s.map(row=>row[metric+1]));if(!values.length)continue;const max=metric===1?1:Math.max(...values,.001),min=0;const maxTime=Math.max(...series.map(s=>s.at(-1)?.[0]||0),.001),minTime=Math.min(...series.map(s=>s[0]?.[0]||0));const current=series.map(s=>{let row=s[0];for(const candidate of s){if(candidate[0]>status.time)break;row=candidate;}return row?.[metric+1];});$(`metric-${metric}`).textContent=current.map(v=>v===undefined?'—':v.toFixed(2)).join(' / ');series.forEach((s,i)=>{if(!s.length)return;const path=document.createElementNS('http://www.w3.org/2000/svg','path');path.setAttribute('d',s.map((row,j)=>`${j?'L':'M'}${((row[0]-minTime)/Math.max(maxTime-minTime,.001)*236+2).toFixed(2)},${(46-(row[metric+1]-min)/(max-min)*42).toFixed(2)}`).join(' '));path.setAttribute('fill','none');path.setAttribute('stroke',colors[i]);path.setAttribute('stroke-width','1.7');svg.append(path);});}}
setInterval(charts,200);
async function openFiles(mode,run=null){fileMode=mode;fileRun=run;selectedFile='';$('file-error').textContent='';$('file-title').textContent=mode==='import'?'Import experiment':mode==='csv'?'Export metrics':'Export recording';$('filename-label').hidden=mode==='import';$('filename').value=run?`${run.name.replace(/[^a-z0-9_-]/gi,'_')}.${mode==='csv'?'csv':'murmuration'}`:'';$('file-action').textContent=mode==='import'?'Import selected recording':'Export file';$('file-dialog').showModal();await browse(folder);}
async function browse(path){await command('browse',{path});}
function renderFiles(result){folder=result.path;$('folder').value=folder;$('parent-folder').onclick=()=>browse(result.parent);$('files').replaceChildren();for(const entry of result.entries){const b=button(`${entry.directory?'▸':'·'} ${entry.name}`,()=>{if(entry.directory){selectedFile='';browse(entry.path);}else{selectedFile=entry.path;for(const child of $('files').children)child.classList.remove('selected');b.classList.add('selected');}});$('files').append(b);}}
$('import').onclick=()=>openFiles('import');$('go-folder').onclick=()=>browse($('folder').value);$('folder').onkeydown=e=>{if(e.key==='Enter'){e.preventDefault();browse($('folder').value);}};
$('file-action').onclick=async()=>{if(fileMode==='import'){if(!selectedFile){$('file-error').textContent='Select a .murmuration recording first.';return;}await command('import',{path:selectedFile});}else{const name=$('filename').value.trim();if(!name||/[\\/]/.test(name)||name==='.'||name==='..'){$('file-error').textContent='Enter a file name without folder separators.';return;}await command('export',{id:fileRun.id,path:`${folder}/${name}`,kind:fileMode==='csv'?'csv':'archive'});}};
function consume(key,value){
  if(key==='status'){if(generation!==value.generation){generation=value.generation;sequence=-1;view?.clear();second?.clear();}updateStatus(value);}
  else if(key==='config')setControls(value);
  else if(key==='frame'){if(value.generation!==generation||value.sequence<=sequence)return;sequence=value.sequence;view?.setFrame(value.frames[0],config,!status.paused);if(value.frames[1])ensureSecond().setFrame(value.frames[1],config,!status.paused);}
  else if(key==='library')renderLibrary(value);
  else if(key==='experiments')renderExperiments(value);
  else if(key==='metrics'){history=value;charts();}
  else if(key==='event'){if(value.type==='error'||value.type==='fatal'){notify(value.message);if($('file-dialog').open)$('file-error').textContent=value.message;if(value.type==='fatal'){$('connection').textContent='Worker stopped';ready=false;}}else if(value.type==='completed'){if(value.action==='browse'&&value.result)renderFiles(value.result);if(['import','export'].includes(value.action)){$('file-dialog').close();notify(value.action==='import'?'Experiment imported.':'Export saved.');}}}
}
function connect(){if(ready)return;ready=true;Pytonium.appState.registerForStateUpdates('studio-update',['studio'],true,true);window.addEventListener('studio-update',event=>{const {key,value}=event.detail;consume(key,value);});for(const key of ['config','status','library','experiments','metrics','frame']){const value=Pytonium.appState.getState('studio',key);if(value!==undefined&&value!==null)consume(key,value);}command('refresh');}
if(window.PytoniumReady)connect();else window.addEventListener('PytoniumReady',connect,{once:true});
setControls(defaults);
window.addEventListener('beforeunload',()=>{view?.dispose();second?.dispose();});
