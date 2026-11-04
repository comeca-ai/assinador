"""Smoke test destrutivo somente em emulador local, com conta/documento fictícios."""
import base64, concurrent.futures, hashlib, http.cookiejar, json, secrets, urllib.request, urllib.error
BASE='http://127.0.0.1:8787'
owner=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
public=urllib.request.build_opener()
def call(client,path,body=None):
    req=urllib.request.Request(BASE+path,data=json.dumps(body).encode() if body is not None else None,headers={'Content-Type':'application/json'})
    try:
        with client.open(req,timeout=15) as response: return response.status,json.load(response)
    except urllib.error.HTTPError as error: return error.code,json.load(error)
assert call(public,'/healthz')==(200,{'status':'ok'})
email=secrets.token_hex(8)+'@example.com'
assert call(owner,'/api/register',{'name':'Teste Worker','email':email,'password':'senha-longa-para-testes'})[0]==200
assert call(owner,'/api/me')[1]['name']=='Teste Worker'
assert call(public,'/api/documents')[0]==401
pdf=b'%PDF-1.4\n%%EOF'
status,document=call(owner,'/api/documents',{'title':'Teste Cloudflare','recipient':'sign@example.com','pdf':base64.b64encode(pdf).decode()})
assert status==201,document
token=document['token']
with public.open(BASE+'/api/sign/'+token+'/pdf') as response: assert response.read()==pdf
assert call(public,'/api/receipt/'+document['id'])[0]==404
assert call(public,'/api/sign/'+token,{'name':'Teste Signatário','consent':False})[0]==400
with concurrent.futures.ThreadPoolExecutor(2) as pool:
    futures=[pool.submit(call,urllib.request.build_opener(),'/api/sign/'+token,{'name':'Teste Signatário','consent':True}) for _ in range(2)]
    results=sorted(f.result()[0] for f in futures)
assert results==[200,409],results
status,receipt=call(owner,'/api/receipt/'+document['id'])
assert status==200 and receipt['document']['sha256']==hashlib.sha256(pdf).hexdigest()
assert [e['action'] for e in receipt['events']]==['created','signed'],receipt
assert call(owner,'/api/logout',{})[0]==200
assert call(owner,'/api/me')[1] is None
assert call(owner,'/api/login',{'email':email,'password':'senha-longa-para-testes'})[0]==200
assert any(d['id']==document['id'] for d in call(owner,'/api/documents')[1])
print('Workers/D1/R2 local: cadastro, sessão, PDF privado, aceite concorrente único, comprovante, logout e login aprovados.')
