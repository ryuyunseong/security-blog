import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {validateScene,renderSceneDiagram} from '../src/lib/article-scenes.mjs';

const visuals=JSON.parse(await readFile(new URL('../src/data/article-visuals.json',import.meta.url),'utf8'));

test('도서 조건·정렬 그림은 같은 입력에서 나온 행만 남긴다',()=>{
  const panels=visuals['cs-study-01-database-sql'].scene.panels;
  const filtered=panels[0].rows.filter(([,price,stock])=>Number(stock)>0&&Number(price)>=20000).map(([id,price])=>[id,price]);
  assert.deepEqual(filtered,panels[1].rows);
  assert.deepEqual([...filtered].sort((a,b)=>Number(b[1])-Number(a[1])||Number(a[0])-Number(b[0])).slice(0,2),panels[2].rows);
});

test('서로 독립된 조건과 한 입력의 두 분류를 잘못된 직렬 처리로 그리지 않는다',()=>{
  const cors=visuals['cors-authentication-authorization'].scene;
  assert.equal(cors.layout,'compare');
  assert.deepEqual(cors.panels.map(p=>p.rows[0]),[['없음','200','반환'],['없음','401','없음']]);
  assert.equal(visuals['tls-version-and-identity'].scene.layout,'parallel');
  const tags=visuals['qualys-static-dynamic-tags'].scene;
  assert.equal(tags.layout,'fork');
  assert.deepEqual(tags.panels[2].values,tags.panels[0].rows.filter(([,os,env])=>os==='Linux'&&env==='prod').map(([id])=>id));
  assert.equal(visuals['u-17-startup-script-permissions'].scene.layout,'compare');
});

test('모바일 합류·분기는 각 원본 패널에서 실제 목적 패널로 연결한다',()=>{
  for(const [slug,edges] of [
    ['u-05-root-uid',[[0,2],[1,2]]],
    ['qualys-static-dynamic-tags',[[0,1],[0,2]]],
  ]) {
    const {svg}=renderSceneDiagram(visuals[slug],true);
    const panels=[...svg.matchAll(/<g data-panel="[^"]+"><rect x="([\d.]+)" y="([\d.]+)" width="([\d.]+)" height="([\d.]+)"/g)]
      .map(m=>m.slice(1).map(Number));
    const arrows=[...svg.matchAll(/<path d="([^"]+)"[^>]+marker-end="url\(#arrow\)"/g)].map(m=>m[1]);
    assert.equal(arrows.length,edges.length,slug);
    for(const [index,[from,to]] of edges.entries()) {
      const a=panels[from],b=panels[to];
      assert.equal(arrows[index],`M${a[0]} ${a[1]+a[3]/2}H16V${b[1]+b[3]/2}H30`,slug);
    }
  }
});

test('UID 공유와 그룹 차이, 바이트 비율은 원래 비교값과 일치한다',()=>{
  const uid=visuals['u-10-duplicate-uid'].scene;
  assert.equal(uid.layout,'merge');
  assert.equal(uid.panels[0].fields[0][1],uid.panels[1].fields[0][1]);
  assert.notEqual(uid.panels[0].fields[1][1],uid.panels[1].fields[1][1]);
  const gzip=visuals['gzip-output-limit'];
  assert.deepEqual(gzip.scene.panels[0].bars.map(([,n])=>n),[544,524288,65536]);
  const svg=renderSceneDiagram(gzip).svg;
  assert.ok(svg.includes(`width="${888*544/524288}"`));
  assert.ok(svg.includes(`width="${888*65536/524288}"`));
});

test('수집 부재와 미수집을 구별하고 특수 비트는 일반 rwx와 따로 표시한다',()=>{
  assert.deepEqual(visuals['u-29-hosts-lpd-permissions'].scene.panels.map(p=>p.status),['absent','unknown']);
  for(const mobile of [false,true]) {
    const svg=renderSceneDiagram(visuals['u-23-special-permission-bits'],mobile).svg;
    assert.ok(svg.includes('특수 비트: SUID'));
    const states=renderSceneDiagram(visuals['u-32-home-directory-existence'],mobile).svg;
    assert.ok(states.includes('자료 있음')&&states.includes('부재 근거')&&states.includes('미수집'));
  }
});

test('원소 삭제 전후와 상태 변경은 시작·조건·결과를 빠뜨리지 않는다',()=>{
  for(const p of visuals['cs-study-04-data-structures-complexity'].scene.panels) {
    assert.deepEqual(p.values,['0','1','2','3','4','5','6','7']);
    assert.deepEqual(p.after,['1','2','3','4','5','6','7']);
  }
  const transitions=visuals['qualys-detection-status-transitions'].scene.panels[0];
  const pairs=transitions.edges.map(([from,to])=>[transitions.nodes[from],transitions.nodes[to]]);
  assert.ok(pairs.some(([from,to])=>from==='New'&&to==='Fixed'));
  assert.ok(pairs.some(([from,to])=>from==='Re-Opened'&&to==='Fixed'));
  for(const mobile of [false,true]) {
    const {svg}=renderSceneDiagram(visuals['qualys-detection-status-transitions'],mobile);
    assert.equal((svg.match(/>Re-Opened<\/tspan>/g)??[]).length,3);
  }
  const sql=visuals['cs-study-01-database-sql'].scene;
  assert.match(sql.panels[1].title,/재고 > 0/);
  assert.match(sql.panels[1].title,/가격 >= 20000/);
});

test('설명 그림은 XML 입력을 이스케이프하고 잘못된 구조·좌표·모드를 거부한다',()=>{
  const item={...visuals['u-01-root-remote-login'],scene:{layout:'compare',panels:[{type:'actor',title:'<script & 문구>',fields:[['필드','"가상"']]}]}};
  const svg=renderSceneDiagram(item).svg;
  assert.ok(svg.includes('&lt;script &amp; 문구&gt;'));
  assert.ok(!/<script|onload=|foreignObject|href=/i.test(svg));
  const invalid=[
    {layout:'unknown',panels:item.scene.panels},
    {layout:'compare',panels:[{type:'actor',title:'대상',rows:[['사용하지 않는 필드']]}]},
    {layout:'compare',panels:[{type:'file',title:'대상',mode:'0899'}]},
    {layout:'compare',panels:[{type:'table',title:'자료',headers:['하나'],rows:[['둘','셋']]}]},
    {layout:'merge',panels:item.scene.panels},
    {layout:'compare',panels:[{type:'numberline',title:'축',minimum:3,maximum:0,lanes:[]}]},
    {layout:'compare',panels:[{type:'states',title:'전이',nodes:['A'],edges:[[0,1,'없는 대상']]}]},
    {layout:'compare',panels:[{type:'bytes',title:'양',bars:[['입력',-1],['출력',2]]}]},
    {layout:'compare',panels:[{type:'array',title:'삭제',values:['0','1'],movement:'head',after:['0']}]},
    {layout:'compare',panels:[{type:'array',title:'삭제',values:['0','1'],after:['1']}]},
  ];
  for(const scene of invalid)assert.throws(()=>validateScene(scene));
});
