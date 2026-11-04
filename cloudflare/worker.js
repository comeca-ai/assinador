const encoder = new TextEncoder();
const now = () => Math.floor(Date.now() / 1000);
const hex = bytes => [...new Uint8Array(bytes)].map(b => b.toString(16).padStart(2, '0')).join('');
const random = () => hex(crypto.getRandomValues(new Uint8Array(32)));
const sha = async value => hex(await crypto.subtle.digest('SHA-256', typeof value === 'string' ? encoder.encode(value) : value));
const headers = {
  'Cache-Control': 'no-store', 'X-Content-Type-Options': 'nosniff',
  'Referrer-Policy': 'no-referrer', 'X-Frame-Options': 'SAMEORIGIN',
  'Content-Security-Policy': "default-src 'self'; script-src 'self'; style-src 'self'; frame-src 'self'; object-src 'none'; base-uri 'self'; form-action 'self'"
};
function json(value, status = 200, extra = {}) {
  return new Response(JSON.stringify(value), { status, headers: { ...headers, 'Content-Type': 'application/json; charset=utf-8', ...extra } });
}
class Invalid extends Error { constructor(message, status = 400) { super(message); this.status = status; } }
export async function hashPassword(value, salt = random()) {
  const key = await crypto.subtle.importKey('raw', encoder.encode(value), 'PBKDF2', false, ['deriveBits']);
  const bits = await crypto.subtle.deriveBits({ name: 'PBKDF2', salt: encoder.encode(salt), iterations: 100000, hash: 'SHA-256' }, key, 256);
  return `pbkdf2-sha256:100000:${salt}:${hex(bits)}`;
}
export function equal(a, b) { let difference = a.length ^ b.length; for (let i = 0; i < Math.max(a.length, b.length); i++) difference |= (a.charCodeAt(i) || 0) ^ (b.charCodeAt(i) || 0); return difference === 0; }
export async function readBody(request) {
  if (request.headers.get('Content-Type')?.split(';')[0] !== 'application/json') throw new Invalid('Use JSON.', 415);
  if (Number(request.headers.get('Content-Length')) > 14000000) throw new Invalid('PDF deve ter até 10 MB.', 413);
  if (!request.body) throw new Invalid('Corpo JSON obrigatório.');
  const reader = request.body.getReader(); const chunks = []; let length = 0;
  while (true) { const { done, value } = await reader.read(); if (done) break; length += value.byteLength; if (length > 14000000) { await reader.cancel(); throw new Invalid('PDF deve ter até 10 MB.', 413); } chunks.push(value); }
  const bytes = new Uint8Array(length); let offset = 0; for (const chunk of chunks) { bytes.set(chunk, offset); offset += chunk.length; }
  let data; try { data = JSON.parse(new TextDecoder().decode(bytes)); } catch { throw new Invalid('JSON inválido.'); }
  if (!data || typeof data !== 'object' || Array.isArray(data)) throw new Invalid('Envie um objeto JSON.');
  return data;
}
const text = (value, max = 150) => typeof value === 'string' ? value.trim().slice(0, max) : '';
async function user(request, env) {
  const sid = request.headers.get('Cookie')?.split(';').map(s => s.trim()).find(s => s.startsWith('session='))?.slice(8);
  if (!sid || !/^[a-f0-9]{64}$/.test(sid)) return null;
  return env.DB.prepare('SELECT users.id,email,name FROM users JOIN sessions ON users.id=sessions.user_id WHERE sessions.id=? AND expires>?').bind(await sha(sid), now()).first();
}
const event = (env, id, action, detail = '') => env.DB.prepare('INSERT INTO audit(document_id,action,created,detail) VALUES(?,?,?,?)').bind(id, action, now(), detail);
async function get(request, env, url) {
  if (url.pathname === '/healthz') { await env.DB.prepare('SELECT 1').first(); return json({ status: 'ok' }); }
  if (url.pathname === '/api/me') return json(await user(request, env));
  if (url.pathname === '/api/documents') {
    const account = await user(request, env); if (!account) throw new Invalid('Entre na sua conta.', 401);
    return json((await env.DB.prepare('SELECT id,title,recipient,created,signed,token,sha256 FROM documents WHERE owner=? ORDER BY created DESC').bind(account.id).all()).results);
  }
  const sign = url.pathname.match(/^\/api\/sign\/([a-f0-9]{64})(\/pdf)?$/);
  if (sign) {
    const doc = await env.DB.prepare('SELECT * FROM documents WHERE token=?').bind(sign[1]).first();
    if (!doc) throw new Invalid('Link inválido.', 404);
    if (sign[2]) { const pdf = await env.DOCUMENTS.get(doc.object_key); if (!pdf) throw new Invalid('Arquivo indisponível.', 404); return new Response(pdf.body, { headers: { ...headers, 'Content-Type': 'application/pdf' } }); }
    return json(Object.fromEntries(['id','title','recipient','sha256','created','signed','signer'].map(k => [k, doc[k]])));
  }
  const receipt = url.pathname.match(/^\/api\/receipt\/([a-f0-9]{64})$/);
  if (receipt) {
    const account = await user(request, env); if (!account) throw new Invalid('Documento não encontrado.', 404);
    const doc = await env.DB.prepare('SELECT id,title,sha256,recipient,created,signed,signer,ip,user_agent FROM documents WHERE id=? AND owner=?').bind(receipt[1], account.id).first();
    if (!doc) throw new Invalid('Documento não encontrado.', 404);
    const events = (await env.DB.prepare('SELECT action,created,detail FROM audit WHERE document_id=? ORDER BY id').bind(doc.id).all()).results;
    return json({ document: doc, events, method: 'Aceite eletrônico por link, sem identidade verificada e sem assinatura criptográfica no PDF.' });
  }
  if (url.pathname.startsWith('/api/')) throw new Invalid('Não encontrado.', 404);
  const assetUrl = new URL(request.url);
  if (/^\/assinar\/[a-f0-9]{64}$/.test(url.pathname)) assetUrl.pathname = '/';
  const response = await env.ASSETS.fetch(new Request(assetUrl, request));
  const safe = new Response(response.body, response); for (const [k,v] of Object.entries(headers)) safe.headers.set(k,v);
  return safe;
}
async function post(request, env, url) {
  if (request.headers.get('Origin') && request.headers.get('Origin') !== url.origin) throw new Invalid('Origem não permitida.', 403);
  if (request.headers.get('Sec-Fetch-Site') === 'cross-site') throw new Invalid('Origem não permitida.', 403);
  const data = await readBody(request);
  if (['/api/register','/api/login'].includes(url.pathname)) {
    const email = text(data.email, 255).toLowerCase(); const pw = typeof data.password === 'string' ? data.password : '';
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email) || email.length > 254 || pw.length < 12 || pw.length > 256) throw new Invalid('Informe e-mail válido e senha entre 12 e 256 caracteres.');
    let uid;
    if (url.pathname === '/api/register') {
      const name = text(data.name, 100); if (!name) throw new Invalid('Informe seu nome.');
      uid = random(); const encoded = await hashPassword(pw);
      const result = await env.DB.prepare('INSERT OR IGNORE INTO users VALUES(?,?,?,?)').bind(uid,email,name,encoded).run();
      if (!result.meta.changes) throw new Invalid('Não foi possível cadastrar este e-mail.', 409);
    } else {
      const account = await env.DB.prepare('SELECT id,password FROM users WHERE email=?').bind(email).first();
      const encoded = await hashPassword(pw, account?.password.split(':')[2] || 'invalid');
      if (!account || !equal(account.password, encoded)) throw new Invalid('E-mail ou senha incorretos.', 401);
      uid = account.id;
    }
    const sid = random();
    await env.DB.batch([env.DB.prepare('DELETE FROM sessions WHERE expires<?').bind(now()), env.DB.prepare('INSERT INTO sessions VALUES(?,?,?)').bind(await sha(sid),uid,now()+86400)]);
    const secure = url.protocol === 'https:' ? '; Secure' : '';
    return json({ ok: true },200,{ 'Set-Cookie': `session=${sid}; HttpOnly; SameSite=Strict; Path=/; Max-Age=86400${secure}` });
  }
  if (url.pathname === '/api/logout') {
    const sid = request.headers.get('Cookie')?.split(';').map(s => s.trim()).find(s => s.startsWith('session='))?.slice(8);
    if (sid) await env.DB.prepare('DELETE FROM sessions WHERE id=?').bind(await sha(sid)).run();
    return json({ok:true},200,{'Set-Cookie':'session=; HttpOnly; SameSite=Strict; Path=/; Max-Age=0'});
  }
  if (url.pathname === '/api/documents') {
    const account = await user(request, env); if (!account) throw new Invalid('Entre na sua conta.',401);
    const title = text(data.title); const recipient = text(data.recipient,255).toLowerCase();
    if (!title || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(recipient) || recipient.length > 254) throw new Invalid('Informe título e e-mail do signatário.');
    let pdf; try { if (typeof data.pdf !== 'string') throw Error(); const binary = atob(data.pdf); if (binary.length > 10000000 || !binary.startsWith('%PDF-')) throw Error(); pdf = Uint8Array.from(binary,c=>c.charCodeAt(0)); } catch { throw new Invalid('Envie um PDF de até 10 MB.'); }
    const id = random(), token = random(), objectKey = `documents/${id}.pdf`;
    await env.DOCUMENTS.put(objectKey,pdf,{httpMetadata:{contentType:'application/pdf'}});
    try { await env.DB.batch([env.DB.prepare('INSERT INTO documents(id,owner,title,object_key,sha256,recipient,token,created) VALUES(?,?,?,?,?,?,?,?)').bind(id,account.id,title,objectKey,await sha(pdf),recipient,token,now()),event(env,id,'created')]); }
    catch(error) { await env.DOCUMENTS.delete(objectKey); throw error; }
    return json({id,token},201);
  }
  const sign = url.pathname.match(/^\/api\/sign\/([a-f0-9]{64})$/);
  if (sign) {
    const name = text(data.name); if (name.length < 3 || data.consent !== true) throw new Invalid('Informe seu nome e aceite os termos.');
    const doc = await env.DB.prepare('SELECT id,signed FROM documents WHERE token=?').bind(sign[1]).first();
    if (!doc) throw new Invalid('Link inválido.',404);
    const detail = 'Aceite expresso pelo portador do link; identidade não verificada.';
    // O segundo comando registra evento somente se o UPDATE anterior alterou uma linha.
    const results = await env.DB.batch([
      env.DB.prepare('UPDATE documents SET signed=?,signer=?,ip=?,user_agent=? WHERE id=? AND signed IS NULL').bind(now(),name,request.headers.get('CF-Connecting-IP')||'',(request.headers.get('User-Agent')||'').slice(0,500),doc.id),
      env.DB.prepare('INSERT INTO audit(document_id,action,created,detail) SELECT ?,?,?,? WHERE changes()=1').bind(doc.id,'signed',now(),detail)
    ]);
    if (!results[0].meta.changes) throw new Invalid('Documento já assinado.',409);
    return json({ok:true});
  }
  throw new Invalid('Não encontrado.',404);
}
export default {
  async fetch(request, env) {
    try {
      const url = new URL(request.url);
      if (request.method === 'GET') return await get(request, env, url);
      if (request.method === 'POST') return await post(request, env, url);
      return json({error:'Método não permitido.'},405,{Allow:'GET, POST'});
    } catch(error) {
      if (error instanceof Invalid) return json({error:error.message},error.status);
      // Nunca registrar corpo, URLs com tokens, credenciais ou dados pessoais.
      return json({error:'Serviço temporariamente indisponível.'},503);
    }
  }
};
