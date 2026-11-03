import base64, http.cookiejar, json, os, socket, subprocess, sys, tempfile, time, unittest, urllib.request, urllib.error
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class Flow(unittest.TestCase):
 def test_document_lifecycle_and_access_control(self):
  with tempfile.TemporaryDirectory() as data:
   with socket.socket() as s: s.bind(('127.0.0.1',0)); port=s.getsockname()[1]
   p=subprocess.Popen([sys.executable,str(ROOT/'server.py')],env={**os.environ,'PORT':str(port),'ASSINAJA_DATA_DIR':data},stdout=subprocess.DEVNULL)
   try:
    base=f'http://127.0.0.1:{port}'
    owner=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
    stranger=urllib.request.build_opener()
    def call(client,path,body=None):
     req=urllib.request.Request(base+path,data=json.dumps(body).encode() if body is not None else None,headers={'Content-Type':'application/json'})
     with client.open(req) as r:return json.load(r)
    for _ in range(50):
     try:call(stranger,'/api/me');break
     except urllib.error.URLError:time.sleep(.1)
    self.assertIsNone(call(stranger,'/api/me'))
    call(owner,'/api/register',{'name':'Teste','email':'teste@example.com','password':'senha-teste-segura'})
    self.assertEqual(call(owner,'/api/me')['name'],'Teste')
    with self.assertRaises(urllib.error.HTTPError) as err:call(stranger,'/api/documents')
    self.assertEqual(err.exception.code,401)
    pdf=b'%PDF-1.4\n%%EOF'
    doc=call(owner,'/api/documents',{'title':'Contrato','recipient':'sign@example.com','pdf':base64.b64encode(pdf).decode()})
    self.assertEqual(len(call(owner,'/api/documents')),1)
    with self.assertRaises(urllib.error.HTTPError) as err:call(stranger,'/api/receipt/'+doc['id'])
    self.assertEqual(err.exception.code,404)
    token=doc['token']
    with self.assertRaises(urllib.error.HTTPError):call(stranger,'/api/sign/'+token,{'name':'Signatário','consent':False})
    call(stranger,'/api/sign/'+token,{'name':'Signatário','consent':True})
    with self.assertRaises(urllib.error.HTTPError) as err:call(stranger,'/api/sign/'+token,{'name':'Outro','consent':True})
    self.assertEqual(err.exception.code,409)
    receipt=call(owner,'/api/receipt/'+doc['id'])
    self.assertEqual(receipt['document']['signer'],'Signatário')
    self.assertEqual([e['action'] for e in receipt['events']],['created','signed'])
    call(owner,'/api/logout',{})
    self.assertIsNone(call(owner,'/api/me'))
    call(owner,'/api/login',{'email':'teste@example.com','password':'senha-teste-segura'})
    self.assertEqual(len(call(owner,'/api/documents')),1)
   finally:p.terminate();p.wait(timeout=5)
