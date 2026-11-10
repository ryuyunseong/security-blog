import {test} from 'node:test';
import assert from 'node:assert/strict';
import {wrapDiagramText} from '../src/lib/diagram-text.mjs';

test('긴 호스트 이름은 마지막 글자를 고립시키지 않고 점 경계에서 나눈다',()=>{
  const hostname='other.example.invalid';
  const lines=wrapDiagramText(hostname,296/22);
  assert.deepEqual(lines,['other.example.','invalid']);
  assert.equal(lines.join(''),hostname);
  assert.deepEqual(wrapDiagramText(hostname,30),[hostname]);
  assert.deepEqual(wrapDiagramText('192.0.2.10',20),['192.0.2.10']);
});
