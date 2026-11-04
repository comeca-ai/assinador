import { test } from 'node:test';
import assert from 'node:assert/strict';
import worker, { equal, hashPassword, readBody } from '../cloudflare/worker.js';
test('password derivation validates the salt and does not store plaintext', async () => {
 const stored = await hashPassword('uma-senha-longa');
 assert.equal(await hashPassword('uma-senha-longa',stored.split(':')[2]),stored);
 assert.notEqual(await hashPassword('outra-senha-longa',stored.split(':')[2]),stored);
 assert.equal(equal(stored,stored),true); assert.equal(equal(stored,stored+'x'),false);
});
test('cross-origin mutations rejected before reading or accessing storage',async()=>{
 const r=await worker.fetch(new Request('https://assinaja.example/api/register',{method:'POST',headers:{Origin:'https://evil.example','Content-Type':'application/json'},body:'{}'}),{});
 assert.equal(r.status,403);
});
test('invalid body rejected without a runtime exception',async()=>{
 for(const body of ['null','[]','false','{']) await assert.rejects(()=>readBody(new Request('https://example.test',{method:'POST',headers:{'Content-Type':'application/json'},body})));
});
