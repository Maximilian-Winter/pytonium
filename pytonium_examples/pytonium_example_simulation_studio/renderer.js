/* Babylon only renders Python snapshots. No simulation runs in the browser. */
const B = window.BABYLON;
const color = hex => B.Color3.FromHexString(hex);
const vec = a => new B.Vector3(...a);

export class Viewport {
  constructor(canvas, onSelect) {
    this.canvas = canvas;
    this.engine = new B.Engine(canvas, true, {preserveDrawingBuffer: true, stencil: true});
    this.scene = new B.Scene(this.engine);
    this.scene.clearColor = new B.Color4(20/255,45/255,64/255,1);
    this.camera = new B.ArcRotateCamera('camera', -.9, 1.16, 150, B.Vector3.Zero(), this.scene);
    this.camera.attachControl(canvas, true);
    this.camera.lowerRadiusLimit = 25; this.camera.upperRadiusLimit = 250;
    this.camera.wheelPrecision = 8;
    this.camera.keysUp = [38]; this.camera.keysDown = [40]; this.camera.keysLeft = [37]; this.camera.keysRight = [39];
    if (matchMedia('(prefers-reduced-motion: reduce)').matches) this.camera.inertia = 0;
    new B.HemisphericLight('sky', new B.Vector3(0,1,0), this.scene).intensity = 1.05;
    const light = new B.DirectionalLight('sun', new B.Vector3(-1,-2,1), this.scene); light.intensity = .5;
    const lines = [];
    for (let x=-40;x<=40;x+=10) {lines.push([new B.Vector3(x,-40,-40),new B.Vector3(x,-40,40)]);lines.push([new B.Vector3(-40,-40,x),new B.Vector3(40,-40,x)]);}
    for (const x of [-40,40]) for (const z of [-40,40]) lines.push([new B.Vector3(x,-40,z),new B.Vector3(x,40,z)]);
    this.grid = B.MeshBuilder.CreateLineSystem('world', {lines}, this.scene); this.grid.color=color('#365467'); this.grid.isPickable=false;
    this.material = new B.StandardMaterial('copper', this.scene); this.material.diffuseColor=color('#C78158'); this.material.specularColor=color('#365467');
    this.source = B.MeshBuilder.CreateCylinder('birds', {height:1.6,diameterTop:0,diameterBottom:.65,tessellation:3}, this.scene);
    this.source.material=this.material; this.source.thinInstanceEnablePicking=true; this.source.alwaysSelectAsActiveMesh=true;
    this.obstacle = B.MeshBuilder.CreateSphere('obstacle',{diameter:18,segments:24},this.scene);
    const stone = new B.StandardMaterial('stone',this.scene);stone.diffuseColor=color('#365467');stone.alpha=.5;stone.wireframe=true;this.obstacle.material=stone;this.obstacle.isPickable=false;this.obstacle.setEnabled(false);
    this.ring=B.MeshBuilder.CreateSphere('neighborhood',{diameter:2,segments:20},this.scene);
    const glass=new B.StandardMaterial('neighborhood glass',this.scene);glass.diffuseColor=color('#8dc5d8');glass.alpha=.055;glass.backFaceCulling=false;this.ring.material=glass;this.ring.isPickable=false;this.ring.setEnabled(false);
    this.selected=-1;this.overlays=false;this.trails=false;this.trailPoints=[];this.arrows=[];this.previous=null;this.current=null;this.received=0;this.count=0;
    this.scene.onPointerObservable.add(info=>{if(info.type===B.PointerEventTypes.POINTERPICK && info.pickInfo?.hit && info.pickInfo.pickedMesh===this.source){this.selected=info.pickInfo.thinInstanceIndex;onSelect(this.selected);}});
    this.engine.runRenderLoop(()=>{if(!canvas.closest('[hidden]')){this.draw();this.scene.render();}});
    this.resizeObserver=new ResizeObserver(()=>this.engine.resize());this.resizeObserver.observe(canvas);
  }
  resetCamera(){this.camera.alpha=-.9;this.camera.beta=1.16;this.camera.radius=150;this.camera.target=B.Vector3.Zero();}
  sync(other){this.camera.alpha=other.camera.alpha;this.camera.beta=other.camera.beta;this.camera.radius=other.camera.radius;this.camera.target.copyFrom(other.camera.target);}
  clear(){this.previous=null;this.current=null;this.trailPoints=[];this.trail?.dispose();this.trail=null;this.ring.setEnabled(false);for(const arrow of this.arrows)arrow.dispose();this.arrows=[];}
  setFrame(frame, config, interpolate=true){
    if(!this.current || frame.positions.length!==this.count || frame.time<this.current.time){this.clear();}
    this.previous=interpolate?this.current:null;this.current=frame;this.config=frame.config||config;this.received=performance.now();
    if(this.count!==frame.positions.length){this.count=frame.positions.length;this.matrices=new Float32Array(this.count*16);this.colors=new Float32Array(this.count*4);this.source.thinInstanceSetBuffer('matrix',this.matrices,16,false);this.source.thinInstanceSetBuffer('color',this.colors,4,false);}
    this.obstacle.setEnabled(!!this.config.obstacle);
    if(this.trails && this.selected>=0 && frame.positions[this.selected]){this.trailPoints.push(vec(frame.positions[this.selected]));if(this.trailPoints.length>100)this.trailPoints.shift();}
  }
  draw(){
    if(!this.current)return;
    const alpha=this.previous?Math.min(1,(performance.now()-this.received)/50):1;
    const selected=this.current.positions[this.selected];
    const up=B.Axis.Y;
    for(let i=0;i<this.count;i++){
      const target=this.current.positions[i],old=this.previous?.positions[i]||target;
      const p=new B.Vector3(old[0]+(target[0]-old[0])*alpha,old[1]+(target[1]-old[1])*alpha,old[2]+(target[2]-old[2])*alpha);
      const velocity=vec(this.current.velocities[i]);velocity.normalize();
      const axis=B.Vector3.Cross(up,velocity);const dot=Math.max(-1,Math.min(1,B.Vector3.Dot(up,velocity)));
      const q=axis.lengthSquared()>1e-8?B.Quaternion.RotationAxis(axis.normalize(),Math.acos(dot)):B.Quaternion.RotationAxis(B.Axis.X,dot<0?Math.PI:0);
      B.Matrix.Compose(new B.Vector3(1,1,1),q,p).copyToArray(this.matrices,i*16);
      const nearby=this.overlays && selected && target.reduce((s,x,j)=>s+(x-selected[j])**2,0)<this.config.radius**2;
      const c=i===this.selected?[1.5,1.5,1.5,1]:nearby?[.7,1.5,1.8,1]:[1,1,1,1];this.colors.set(c,i*4);
    }
    this.source.thinInstanceBufferUpdated('matrix');this.source.thinInstanceBufferUpdated('color');
    this.ring.setEnabled(!!(this.overlays&&selected));
    if(this.overlays&&selected){this.ring.position.copyFrom(vec(selected));this.ring.scaling.setAll(this.config.radius);}
    // Updating debug geometry once per snapshot keeps the normal render loop lean.
    if(this.debugFrame!==this.current || this.debugOverlays!==this.overlays || this.debugTrails!==this.trails){
      this.debugFrame=this.current;this.debugOverlays=this.overlays;this.debugTrails=this.trails;
      for(const a of this.arrows)a.dispose();this.arrows=[];
      if(this.overlays&&selected){
        const vectors=this.current.selection?.vectors||this.estimateVectors();
        vectors.forEach((v,i)=>{const start=vec(selected),end=start.add(vec(v).scale(.7));const d=end.subtract(start);const side=B.Vector3.Cross(d,B.Axis.Y).normalize().scale(.6);const back=end.subtract(d.scale(.2));const a=B.MeshBuilder.CreateLineSystem('force',{lines:[[start,end],[end,back.add(side)],[end,back.subtract(side)]]},this.scene);a.color=color(['#e9a57b','#8dc5d8','#d6d49a'][i]);a.isPickable=false;this.arrows.push(a);});
      }
      this.trail?.dispose();this.trail=null;
      if(this.trails&&this.trailPoints.length>1){this.trail=B.MeshBuilder.CreateLines('trail',{points:this.trailPoints},this.scene);this.trail.color=color('#c78158');this.trail.isPickable=false;}
    }
  }
  estimateVectors(){
    // Replay overlay is a geometric explanation; replay positions remain recorded data.
    const p=this.current.positions[this.selected],v=this.current.velocities[this.selected],s=[0,0,0],a=[0,0,0],c=[0,0,0];let n=0;
    this.current.positions.forEach((q,i)=>{const d=q.map((x,j)=>x-p[j]),d2=d.reduce((x,y)=>x+y*y,0);if(i!==this.selected&&d2<this.config.radius**2){n++;for(let j=0;j<3;j++){s[j]-=d[j]/Math.max(d2,.01)*12;a[j]+=this.current.velocities[i][j];c[j]+=d[j];}}});
    const cap=x=>{const scale=Math.min(1,12/(Math.hypot(...x)||1));return x.map(y=>y*scale);};
    return [cap(s),cap(a.map((x,j)=>n?x/n-v[j]:0)),cap(c.map(x=>n?x/n*.6:0))];
  }
  dispose(){this.resizeObserver.disconnect();this.scene.dispose();this.engine.dispose();}
}
