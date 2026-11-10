import { escapeXml as esc } from './core.mjs';
import { wrapDiagramText } from './diagram-text.mjs';
import { renderPermissionBits } from './comparison-details.mjs';

const types = ['table', 'file', 'actor', 'set', 'array', 'split', 'numberline', 'states', 'bytes', 'attachments'];
const icons = ['file', 'folder', 'person', 'host', 'cloud', 'key', 'database', 'process', 'character', 'block', 'link', 'pipe'];
const ink = '#193e2f', muted = '#536b60', line = '#7eaa93';
const rect = (x,y,w,h,fill='#fff',radius=10) => `<rect x="${x}" y="${y}" width="${w}" height="${h}" rx="${radius}" fill="${fill}" stroke="#cadbd1"/>`;
const path = (d,arrow=false) => `<path d="${d}" fill="none" stroke="${line}" stroke-width="2"${arrow?' marker-end="url(#arrow)"':''}/>`;
function text(x,y,value,width,size=20,key=false,anchor='start') {
  const lines=wrapDiagramText(String(value),width/size), step=Math.ceil(size*1.4);
  return {height:lines.length*step,svg:`<text x="${x}" y="${y+size}" font-size="${size}" fill="${key?ink:muted}" font-weight="${key?700:400}" text-anchor="${anchor}"${key?' data-role="key"':''}>`+lines.map((v,i)=>`<tspan x="${x}" dy="${i?step:0}">${esc(v)}</tspan>`).join('')+'</text>'};
}
function icon(kind,x,y) {
  const stroke=`fill="#e6f0e9" stroke="${line}" stroke-width="2"`;
  if(kind==='folder')return `<path d="M${x} ${y+8}v28h38V${y+8}H${x+20}l-8-8H${x}v8Z" ${stroke}/>`;
  if(kind==='character')return rect(x,y,38,34,'#e6f0e9',4)+`<path d="M${x+8} ${y+9}l7 7-7 7m14 0h8" stroke="${line}" stroke-width="2" fill="none"/>`;
  if(kind==='block')return [0,1,2].map(i=>rect(x,y+i*12,38,10,'#e6f0e9',2)).join('');
  if(kind==='link')return `<ellipse cx="${x+12}" cy="${y+20}" rx="12" ry="8" ${stroke}/><ellipse cx="${x+29}" cy="${y+20}" rx="12" ry="8" ${stroke}/>`;
  if(kind==='pipe')return rect(x,y+8,38,24,'#e6f0e9',4)+path(`M${x+5} ${y+20}h27`,true);
  if(kind==='file')return `<path d="M${x} ${y}h23l9 9v32H${x}Z M${x+23} ${y}v9h9" ${stroke}/>`;
  if(kind==='person')return `<circle cx="${x+18}" cy="${y+10}" r="10" ${stroke}/><path d="M${x} ${y+42}v-10q18-18 36 0v10Z" ${stroke}/>`;
  if(kind==='cloud')return `<path d="M${x+7} ${y+34}a10 10 0 0 1 0-20a14 14 0 0 1 27-2a11 11 0 0 1 3 22Z" ${stroke}/>`;
  if(kind==='key')return `<circle cx="${x+10}" cy="${y+13}" r="10" ${stroke}/><path d="M${x+20} ${y+13}h22v8m-10-8v8" stroke="${line}" stroke-width="3" fill="none"/>`;
  if(kind==='database')return `<path d="M${x} ${y+7}v29c0 10 36 10 36 0V${y+7}" ${stroke}/><ellipse cx="${x+18}" cy="${y+7}" rx="18" ry="7" ${stroke}/>`;
  if(kind==='process')return `<circle cx="${x+19}" cy="${y+21}" r="18" ${stroke}/><path d="M${x+14} ${y+11}l14 10-14 10Z" fill="${line}"/>`;
  return rect(x,y,38,36,'#e6f0e9',4)+`<path d="M${x+8} ${y+12}h22m-22 8h22m-22 8h12" stroke="${line}" stroke-width="2"/>`;
}
const validText = value => typeof value==='string' && value.trim() && value.length<=100;
function strings(values) { return Array.isArray(values) && values.length>0 && values.length<=12 && values.every(validText); }

export function validateScene(scene) {
  if(!scene || typeof scene!=='object' || Array.isArray(scene) || Object.keys(scene).some(k=>!['layout','panels'].includes(k))
    || !['sequence','compare','merge','fork','parallel'].includes(scene.layout) || !Array.isArray(scene.panels) || scene.panels.length<1 || scene.panels.length>3) throw new Error('설명 그림의 배치·패널 형식 오류');
  if(['merge','fork'].includes(scene.layout) && scene.panels.length!==3) throw new Error('합류·분기 그림에는 패널 셋이 필요하다');
  const specific={table:['headers','rows','rowIcons','selected'],file:['mode','status'],actor:[],set:['values','selected'],array:['values','selected','movement','after'],split:['parts'],numberline:['lanes','minimum','maximum'],states:['nodes','edges'],bytes:['bars'],attachments:['source','targets']};
  for(const p of scene.panels) {
    if(!p || typeof p!=='object' || Array.isArray(p) || !types.includes(p.type) || !validText(p.title))throw new Error('설명 그림의 패널 입력 오류');
    if(Object.keys(p).some(k=>!['type','title','icon','fields',...specific[p.type]].includes(k)))throw new Error('패널 종류에 맞지 않는 필드');
    if(p.icon!==undefined && !icons.includes(p.icon))throw new Error('지원하지 않는 설명 그림 아이콘');
    if(p.status!==undefined && (p.type!=='file'||!['present','absent','error','unknown'].includes(p.status)))throw new Error('그림의 파일 수집 상태 오류');
    if(p.fields!==undefined && (!Array.isArray(p.fields)||p.fields.length>5||p.fields.some(row=>!Array.isArray(row)||row.length!==2||!row.every(validText))))throw new Error('그림의 필드 형식 오류');
    if(p.type==='table' && (!strings(p.headers)||p.headers.length>4||!Array.isArray(p.rows)||!p.rows.length||p.rows.length>8||p.rows.some(row=>!Array.isArray(row)||row.length!==p.headers.length||!row.every(validText))))throw new Error('그림의 표 행·열 오류');
    if(p.rowIcons!==undefined&&(p.type!=='table'||!Array.isArray(p.rowIcons)||p.rowIcons.length!==p.rows.length||p.rowIcons.some(v=>!icons.includes(v))))throw new Error('종류 그림의 행별 아이콘 오류');
    if(p.mode!==undefined && (typeof p.mode!=='string'||!/^[0-7]{4}$/.test(p.mode)))throw new Error('그림의 4자리 권한 모드 오류');
    if(['array','set'].includes(p.type)&&!strings(p.values))throw new Error('그림의 원소 입력 오류');
    if(p.selected!==undefined && (!Array.isArray(p.selected)||p.selected.some(i=>!Number.isInteger(i)||i<0||i>=(p.type==='table'?p.rows.length:p.values?.length??0))))throw new Error('그림의 선택 인덱스 오류');
    if(p.movement!==undefined && (p.type!=='array'||!['shift','head'].includes(p.movement)||p.values.length<2))throw new Error('배열 이동 형식 오류');
    if(p.after!==undefined && (p.type!=='array'||!p.movement||!strings(p.after)||JSON.stringify(p.after)!==JSON.stringify(p.values.slice(1))))throw new Error('첫 원소 제거 전후의 배열 불일치');
    if(p.type==='split'&&(!Array.isArray(p.parts)||p.parts.length!==2||p.parts.some(row=>!Array.isArray(row)||row.length!==2||!row.every(validText))))throw new Error('그림의 분리 필드 오류');
    if(p.type==='numberline'&&(!Number.isInteger(p.minimum)||!Number.isInteger(p.maximum)||p.maximum<=p.minimum||p.maximum-p.minimum>16||!Array.isArray(p.lanes)||p.lanes.length!==2||p.lanes.some(row=>!Array.isArray(row)||row.length!==4||!validText(row[0])||!Number.isInteger(row[1])||!Number.isInteger(row[2])||row[1]<p.minimum||row[1]>p.maximum||row[2]<p.minimum||row[2]>p.maximum||!validText(row[3]))))throw new Error('수직선의 범위·좌표 오류');
    if(p.type==='states'&&(!strings(p.nodes)||p.nodes.length>5||!Array.isArray(p.edges)||p.edges.length>8||p.edges.some(e=>!Array.isArray(e)||e.length!==3||!Number.isInteger(e[0])||!Number.isInteger(e[1])||e[0]===e[1]||!p.nodes[e[0]]||!p.nodes[e[1]]||!validText(e[2]))))throw new Error('상태 전이의 정점·연결 오류');
    if(p.type==='bytes'&&(!Array.isArray(p.bars)||p.bars.length<2||p.bars.length>4||p.bars.some(row=>!Array.isArray(row)||row.length!==2||!validText(row[0])||!Number.isSafeInteger(row[1])||row[1]<0||row[1]>1e12)||p.bars.every(row=>row[1]===0)))throw new Error('바이트 막대의 이름·정수 범위 오류');
    if(p.type==='attachments'&&(!Array.isArray(p.source)||p.source.length!==2||!validText(p.source[0])||!icons.includes(p.source[1])||!Array.isArray(p.targets)||p.targets.length<2||p.targets.length>3||p.targets.some(t=>!Array.isArray(t)||t.length!==3||!validText(t[0])||!icons.includes(t[1])||!validText(t[2]))))throw new Error('목록 연결의 원본·대상 오류');
  }
}

export function sceneLabels(scene) {
  return scene.panels.flatMap(p=>[p.title,...(p.headers??[]),...(p.rows??[]).flat(),...(p.fields??[]).flat(),...(p.values??[]),...(p.after??[]),...(p.parts??[]).flat(),...(p.mode?[p.mode]:[]),...(p.lanes??[]).flatMap(row=>[row[0],String(row[1]),String(row[2]),row[3]]),...(p.nodes??[]),...(p.edges??[]).map(row=>row[2]),...(p.bars??[]).flatMap(row=>[row[0],String(row[1])]),...(p.source?[p.source[0]]:[]),...(p.targets??[]).flatMap(t=>[t[0],t[2]])]);
}

function panel(p,x,y,w,mobile) {
  let content='',offset=16;
  const glyph=p.icon??(p.type==='file'?'file':undefined);
  if(glyph)content+=icon(glyph,x+16,y+16);
  if(p.status==='absent')content+=`<path d="M${x+16} ${y+18}l34 34m0-34-34 34" stroke="#956c30" stroke-width="3"/>`;
  if(['unknown','error'].includes(p.status))content+=`<circle cx="${x+33}" cy="${y+37}" r="17" fill="#f8e9b8" stroke="#956c30"/>`+text(x+33,y+21,p.status==='unknown'?'?':'!',30,24,true,'middle').svg;
  const fileHeading=p.type==='file';
  if(fileHeading)offset+=54;
  const heading=text(x+16+(glyph&&!fileHeading?54:0),y+offset,p.title,w-32-(glyph&&!fileHeading?54:0),!mobile&&fileHeading?20:22,true);
  content+=heading.svg;offset+=Math.max(heading.height,glyph&&!fileHeading?42:0)+16;
  if(p.status) {
    const names={present:'자료 있음',absent:'부재 근거',error:'조회 오류',unknown:'미수집'};
    const status=text(x+16,y+offset,names[p.status],w-32,22,true);
    content+=rect(x+12,y+offset-3,w-24,status.height+14,p.status==='present'?'#d5e8dc':'#f8e9b8');
    content+=status.svg;offset+=status.height+26;
  }
  if(p.type==='table') {
    const columns=p.headers.length,cellWidth=(w-24)/columns;
    const splitWord=(value,size)=>value.split(/\s+/).some(word=>wrapDiagramText(word,(cellWidth-16)/size).length>1);
    const stacked=p.headers.some(v=>splitWord(v,22))||p.rows.flat().some(v=>splitWord(v,20));
    if(stacked) {
      p.rows.forEach((row,rowIndex)=>{
        let details='',rowOffset=10;
        row.forEach((value,i)=>{const field=text(x+24,y+offset+rowOffset,`${p.headers[i]}: ${value}`,w-48,i?20:22,i===0);details+=field.svg;rowOffset+=field.height+5;});
        content+=rect(x+12,y+offset,w-24,rowOffset+8,p.selected?.includes(rowIndex)?'#d5e8dc':'#fff')+details;offset+=rowOffset+18;
      });
    } else for(const [rowIndex,row] of [p.headers,...p.rows].entries()) {
      const hasIcon=rowIndex>0&&p.rowIcons;
      const cells=row.map((v,i)=>text(x+20+i*cellWidth+(hasIcon&&!i?48:0),y+offset+8,v,cellWidth-16-(hasIcon&&!i?48:0),rowIndex===0?22:20,rowIndex===0));
      const h=Math.max(hasIcon?40:0,...cells.map(c=>c.height))+16;
      content+=rect(x+12,y+offset,w-24,h,rowIndex===0?'#e6f0e9':p.selected?.includes(rowIndex-1)?'#d5e8dc':'#fff',0);
      if(hasIcon)content+=icon(p.rowIcons[rowIndex-1],x+20,y+offset+8);
      cells.forEach((c,i)=>{if(i)content+=path(`M${x+12+i*cellWidth} ${y+offset}v${h}`);content+=c.svg;});
      offset+=h;
    }
    offset+=8;
  } else if(p.type==='array') {
    const cell=(w-32)/p.values.length;
    if(p.after){content+=text(x+16,y+offset,'삭제 전',w-32).svg;offset+=36;}
    const beforeY=y+offset;
    p.values.forEach((value,i)=>{
      content+=rect(x+16+i*cell,y+offset,cell,44,p.selected?.includes(i)?'#d5e8dc':'#fff',0);
      content+=text(x+16+(i+0.5)*cell,y+offset+7,value,cell-8,22,true,'middle').svg;
    });
    offset+=44;
    if(p.after) {
      content+=path(`M${x+20} ${beforeY+5}l${cell-8} 34`);
      offset+=48;
      const afterY=y+offset,shift=p.movement==='head'?1:0;
      p.after.forEach((value,i)=>{
        const left=x+16+(i+shift)*cell;
        content+=rect(left,afterY,cell,44,'#fff',0)+text(left+cell/2,afterY+7,value,cell-8,22,true,'middle').svg;
        if(p.movement==='shift')content+=path(`M${x+16+(i+1.5)*cell} ${beforeY+49}L${left+cell/2} ${afterY-6}`,true);
      });
      if(p.movement==='head')content+=path(`M${x+16+cell/2} ${beforeY+49}V${afterY+22}H${x+16+cell-5}`,true);
      offset+=54;
      const label=text(x+16,y+offset,p.movement==='shift'?'남은 원소를 앞 칸으로':'다음 원소에서 꺼내기',w-32);content+=label.svg;offset+=label.height+8;
    } else if(p.movement) {
      if(p.movement==='shift')for(let i=1;i<p.values.length;i++)content+=path(`M${x+16+(i+0.5)*cell} ${y+offset+12}v16h${-cell+8}`,true);
      else content+=path(`M${x+16+cell/2} ${y+offset+12}v16h${cell-8}`,true);
      offset+=46;
    }
  } else if(p.type==='set') {
    let cx=16;
    for(const [i,value] of p.values.entries()) {
      const width=Math.min(w-32,Math.max(90,value.length*14+24));
      if(cx+width>w-16){cx=16;offset+=60;}
      content+=rect(x+cx,y+offset,width,48,p.selected?.includes(i)?'#d5e8dc':'#fff',24)+text(x+cx+width/2,y+offset+9,value,width-20,22,true,'middle').svg;
      cx+=width+10;
    }
    offset+=64;
  } else if(p.type==='split') {
    p.parts.forEach((part,i)=>{
      const left=x+16+i*(w-32)/2, width=(w-32)/2;
      content+=rect(left,y+offset,width,100,i?'#e6f0e9':'#fff',0);
      content+=text(left+width/2,y+offset+10,part[0],width-16,20,false,'middle').svg;
      content+=text(left+width/2,y+offset+52,part[1],width-16,26,true,'middle').svg;
    });offset+=116;
  } else if(p.type==='numberline') {
    const start=x+34,span=w-68,px=n=>start+(n-p.minimum)*span/(p.maximum-p.minimum);
    for(const lane of p.lanes) {
      const h=text(x+16,y+offset,lane[0],w-32,22,true);content+=h.svg;offset+=h.height+18;
      content+=path(`M${start} ${y+offset}h${span}`);
      for(let n=p.minimum;n<=p.maximum;n++)content+=path(`M${px(n)} ${y+offset-5}v10`)+text(px(n),y+offset+10,String(n),90,20,false,'middle').svg;
      if(lane[1]!==lane[2])content+=path(`M${px(lane[1])} ${y+offset+58}H${px(lane[2])}`,true);
      content+=`<circle cx="${px(lane[2])}" cy="${y+offset+58}" r="5" fill="${ink}"/>`;
      content+=text(x+16,y+offset+80,lane[3],w-32).svg;offset+=130;
    }
  } else if(p.type==='attachments') {
    const sourceWidth=mobile?w-48:Math.min(270,w*0.38),sourceX=x+24;
    const sourceY=y+offset+(mobile?0:110);
    const sourceLabel=text(sourceX+sourceWidth/2,sourceY+62,p.source[0],sourceWidth-24,22,true,'middle');
    const sourceHeight=Math.max(112,sourceLabel.height+78);
    content+=rect(sourceX,sourceY,sourceWidth,sourceHeight,'#e6f0e9')+icon(p.source[1],sourceX+sourceWidth/2-18,sourceY+12)+sourceLabel.svg;
    let targetY=y+offset+(mobile?sourceHeight+52:0),targetX=mobile?x+48:x+w*0.51,targetWidth=mobile?w-64:w*0.49-16;
    for(const t of p.targets) {
      const title=text(targetX+62,targetY+12,t[0],targetWidth-78,22,true),role=text(targetX+16,targetY+28+title.height,t[2],targetWidth-32);
      const h=title.height+role.height+52;
      content+=rect(targetX,targetY,targetWidth,h)+icon(t[1],targetX+16,targetY+12)+title.svg+role.svg;
      const sx=mobile?sourceX:sourceX+sourceWidth,sy=sourceY+sourceHeight/2,tx=targetX-6,ty=targetY+h/2,lx=mobile?x+12:(sx+tx)/2;
      content+=path(`M${sx} ${sy}H${lx}V${ty}H${tx}`,true);targetY+=h+24;
    }
    offset=targetY-y;
  } else if(p.type==='bytes') {
    const maximum=Math.max(...p.bars.map(row=>row[1])),span=w-40;
    for(const [name,value] of p.bars) {
      const heading=text(x+16,y+offset,name,w-32,22,true);content+=heading.svg;offset+=heading.height+8;
      content+=rect(x+20,y+offset,span,24,'#f1f6f2',0);
      if(value)content+=rect(x+20,y+offset,span*value/maximum,24,'#9abfa9',0);
      offset+=32;const amount=text(x+16,y+offset,`${value} 바이트`,w-32);content+=amount.svg;offset+=amount.height+24;
    }
    const scale=text(x+16,y+offset,`같은 축: 0 ~ ${maximum} 바이트`,w-32);content+=scale.svg;offset+=scale.height+8;
  } else if(p.type==='states') {
    const pillWidth=(w-52)/2;
    for(const [from,to,label] of p.edges) {
      const left=x+16,right=x+w-16-pillWidth;
      const a=text(left+pillWidth/2,y+offset+10,p.nodes[from],pillWidth-8,22,true,'middle');
      const b=text(right+pillWidth/2,y+offset+10,p.nodes[to],pillWidth-8,22,true,'middle');
      const h=Math.max(a.height,b.height)+20;
      content+=rect(left,y+offset,pillWidth,h,'#e6f0e9',12)+rect(right,y+offset,pillWidth,h,'#e6f0e9',12)+a.svg+b.svg;
      content+=path(`M${left+pillWidth+2} ${y+offset+h/2}H${right-3}`,true);
      offset+=h+8;
      const condition=text(x+16,y+offset,label,w-32);content+=condition.svg;offset+=condition.height+24;
    }
  }
  if(p.mode) {
    const mode=text(x+16,y+offset,`mode ${p.mode}`,w-32,22,true);content+=mode.svg;offset+=mode.height+8;
    const bits=renderPermissionBits(p.mode,{x:x+16,y:y+offset,width:w-32});content+=bits.svg;offset+=bits.height+8;
    const special=[['SUID',0o4000],['SGID',0o2000],['Sticky',0o1000]].filter(([,bit])=>Number.parseInt(p.mode,8)&bit).map(([name])=>name);
    if(special.length){const s=text(x+16,y+offset,`특수 비트: ${special.join(' / ')}`,w-32);content+=s.svg;offset+=s.height+8;}
    const legend=text(x+16,y+offset,p.icon==='folder'?'r 읽기, w 쓰기, x 탐색, - 없음':'r 읽기, w 쓰기, x 실행, - 없음',w-32);content+=legend.svg;offset+=legend.height+8;
  }
  for(const [key,value] of p.fields??[]) {
    const k=text(x+16,y+offset,key,w-32,20);content+=k.svg;offset+=k.height+3;
    const v=text(x+16,y+offset,value,w-32,mobile?22:20,true);content+=v.svg;offset+=v.height+14;
  }
  const height=offset+10;
  return {height,svg:`<g data-panel="${p.type}">`+rect(x,y,w,height,'#fff')+content+'</g>'};
}

export function renderSceneDiagram(item,mobile=false) {
  const scene=item.scene;validateScene(scene);
  const width=mobile?360:960,count=scene.panels.length,panels=[];
  let content='',height;
  if(mobile) {
    let y=16;
    const inset=['merge','fork'].includes(scene.layout)?36:16,panelWidth=width-inset-16;
    scene.panels.forEach(p=>{const rendered=panel(p,inset,y,panelWidth,true);panels.push({x:inset,y,w:panelWidth,h:rendered.height});content+=rendered.svg;y+=rendered.height+(scene.layout==='compare'||scene.layout==='parallel'?24:48);});
    height=y;
  } else if(scene.layout==='merge'||scene.layout==='fork') {
    const sources=scene.layout==='merge'?[0,1]:[1,2],target=scene.layout==='merge'?2:0;
    const sourceX=scene.layout==='merge'?16:534,targetX=scene.layout==='merge'?534:16;
    let y=16;
    sources.forEach(i=>{const rendered=panel(scene.panels[i],sourceX,y,410,false);panels[i]={x:sourceX,y,w:410,h:rendered.height};content+=rendered.svg;y+=rendered.height+24;});
    const result=panel(scene.panels[target],targetX,16,410,false);panels[target]={x:targetX,y:16,w:410,h:result.height};content+=result.svg;height=Math.max(y,result.height+32);
  } else {
    const gap=32,w=(width-32-gap*(count-1))/count;
    scene.panels.forEach((p,i)=>{const x=16+i*(w+gap),rendered=panel(p,x,16,w,false);panels.push({x,y:16,w,h:rendered.height});content+=rendered.svg;});
    height=Math.max(...panels.map(p=>p.h))+32;
  }
  const edges=scene.layout==='sequence'?panels.slice(1).map((_,i)=>[i,i+1]):scene.layout==='merge'?[[0,2],[1,2]]:scene.layout==='fork'?[[0,1],[0,2]]:[];
  for(const [from,to] of edges) {
    const a=panels[from],b=panels[to];
    if(mobile&&['merge','fork'].includes(scene.layout))content+=path(`M${a.x} ${a.y+a.h/2}H16V${b.y+b.h/2}H30`,true);
    else if(mobile)content+=path(`M${a.x+a.w/2} ${a.y+a.h+5}V${b.y-8}`,true);
    else {const mid=(a.x+a.w+b.x)/2;content+=path(`M${a.x+a.w+3} ${a.y+a.h/2}H${mid}V${b.y+b.h/2}H${b.x-6}`,true);}
  }
  height=Math.max(height,260);
  const svg=`<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}" viewBox="0 0 ${width} ${height}" data-diagram-kind="${item.kind}" data-explanation="structured"${mobile?' data-layout="mobile"':''} role="img" aria-labelledby="title desc"><title id="title">${esc(item.title)}</title><desc id="desc">${esc(`${item.caption} ${item.note}`)}</desc><defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse"><path d="M0 0L10 5L0 10Z" fill="${line}"/></marker></defs><rect width="${width}" height="${height}" fill="#f1f6f2"/><g font-family="'Malgun Gothic','Noto Sans KR',sans-serif">${content}</g></svg>`;
  return {svg,width,height,viewBox:`0 0 ${width} ${height}`,y:0};
}
