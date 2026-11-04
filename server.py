import base64, hashlib, hmac, json, os, secrets, sqlite3, time
from pathlib import Path
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from http.cookies import SimpleCookie
from urllib.parse import urlparse

ROOT = Path(__file__).parent
DATA = Path(os.getenv('ASSINAJA_DATA_DIR', str(ROOT / '.local')))
DATA.mkdir(parents=True, exist_ok=True)
os.chmod(DATA, 0o700)
DB = DATA / 'assinaja.sqlite3'
def db():
    c = sqlite3.connect(DB); c.row_factory = sqlite3.Row; return c
with db() as c:
    c.executescript('''CREATE TABLE IF NOT EXISTS users(id TEXT PRIMARY KEY,email TEXT UNIQUE,name TEXT,password TEXT);
CREATE TABLE IF NOT EXISTS sessions(id TEXT PRIMARY KEY,user_id TEXT,expires INTEGER);
CREATE TABLE IF NOT EXISTS documents(id TEXT PRIMARY KEY,owner TEXT,title TEXT,filename TEXT,pdf BLOB,sha256 TEXT,recipient TEXT,token TEXT UNIQUE,created INTEGER,signed INTEGER,signer TEXT,ip TEXT,user_agent TEXT);
CREATE TABLE IF NOT EXISTS audit(id INTEGER PRIMARY KEY,document_id TEXT,action TEXT,created INTEGER,detail TEXT);''')
def password(value, salt=None):
    salt = salt or secrets.token_hex(16)
    return salt + ':' + hashlib.scrypt(value.encode(),salt=salt.encode(),n=16384,r=8,p=1).hex()
def record(c, doc, action, detail=''):
    c.execute('INSERT INTO audit(document_id,action,created,detail) VALUES(?,?,?,?)',(doc,action,int(time.time()),detail))
class Handler(BaseHTTPRequestHandler):
    def log_message(self,*args): pass  # URLs de assinatura contêm tokens privados.
    def send(self, status, body, kind='application/json', cookie=None):
        if kind == 'application/json': body = json.dumps(body,ensure_ascii=False).encode()
        elif isinstance(body,str): body=body.encode()
        self.send_response(status)
        self.send_header('Content-Type',kind); self.send_header('Content-Length',str(len(body)))
        self.send_header('Cache-Control','no-store'); self.send_header('X-Content-Type-Options','nosniff')
        self.send_header('Referrer-Policy','no-referrer'); self.send_header('X-Frame-Options','SAMEORIGIN')
        self.send_header('Content-Security-Policy',"default-src 'self'; script-src 'self'; style-src 'self'; frame-src 'self'; object-src 'none'; base-uri 'self'; form-action 'self'")
        if cookie: self.send_header('Set-Cookie',cookie)
        self.end_headers(); self.wfile.write(body)
    def user(self,c):
        cookie=SimpleCookie(); cookie.load(self.headers.get('Cookie',''))
        sid=cookie.get('session')
        if not sid: return None
        return c.execute('SELECT users.id,email,name FROM users JOIN sessions ON users.id=sessions.user_id WHERE sessions.id=? AND expires>?',(sid.value,int(time.time()))).fetchone()
    def do_GET(self):
        path=urlparse(self.path).path
        with db() as c:
            user=self.user(c)
            if path=='/healthz':
                c.execute('SELECT 1').fetchone()
                return self.send(200,{'status':'ok'})
            if path=='/api/me': return self.send(200,dict(user) if user else None)
            if path=='/api/documents':
                if not user: return self.send(401,{'error':'Entre na sua conta.'})
                rows=c.execute('SELECT id,title,recipient,created,signed,token,sha256 FROM documents WHERE owner=? ORDER BY created DESC',(user['id'],)).fetchall()
                return self.send(200,[dict(r) for r in rows])
            if path.startswith('/api/sign/'):
                parts=path.split('/'); token=parts[3]
                d=c.execute('SELECT * FROM documents WHERE token=?',(token,)).fetchone()
                if not d: return self.send(404,{'error':'Link inválido.'})
                if len(parts)==5 and parts[4]=='pdf': return self.send(200,bytes(d['pdf']),'application/pdf')
                return self.send(200,{k:d[k] for k in ['id','title','recipient','sha256','created','signed','signer']})
            if path.startswith('/api/receipt/'):
                d=c.execute('SELECT * FROM documents WHERE id=?',(path.split('/')[-1],)).fetchone()
                if not user or not d or d['owner']!=user['id']: return self.send(404,{'error':'Documento não encontrado.'})
                events=[dict(r) for r in c.execute('SELECT action,created,detail FROM audit WHERE document_id=? ORDER BY id',(d['id'],))]
                return self.send(200,{'document':{k:d[k] for k in ['id','title','sha256','recipient','created','signed','signer','ip','user_agent']},'events':events,'method':'Aceite eletrônico por link. Não utiliza certificado ICP-Brasil. O PDF original é preservado; este registro não insere assinatura criptográfica no PDF.'})
        files={'/':'index.html','/app.js':'app.js','/styles.css':'styles.css'}
        name=files.get(path,'index.html' if path.startswith('/assinar/') else None)
        if not name: return self.send(404,{'error':'Não encontrado.'})
        kinds={'html':'text/html; charset=utf-8','js':'text/javascript; charset=utf-8','css':'text/css; charset=utf-8'}
        return self.send(200,(ROOT/'public'/name).read_bytes(),kinds[name.split('.')[-1]])
    def do_POST(self):
        origin=self.headers.get('Origin')
        if origin and urlparse(origin).netloc!=self.headers.get('Host'): return self.send(403,{'error':'Origem não permitida.'})
        if self.headers.get('Content-Type','').split(';')[0]!='application/json': return self.send(415,{'error':'Use JSON.'})
        try:
            size=int(self.headers.get('Content-Length','0'))
            if size<=0: return self.send(400,{'error':'Corpo JSON obrigatório.'})
            if size>15_000_000: return self.send(413,{'error':'PDF deve ter até 10 MB.'})
            data=json.loads(self.rfile.read(size)); path=urlparse(self.path).path
            if not isinstance(data,dict): return self.send(400,{'error':'Envie um objeto JSON.'})
            with db() as c:
                user=self.user(c)
                if path in ['/api/register','/api/login']:
                    email=str(data.get('email','')).strip().lower(); pw=str(data.get('password',''))
                    if '@' not in email or len(email)>254 or len(pw)<12 or len(pw)>256: return self.send(400,{'error':'Informe e-mail válido e senha entre 12 e 256 caracteres.'})
                    if path=='/api/register':
                        uid=secrets.token_hex(16); name=str(data.get('name','')).strip()[:100]
                        if not name: return self.send(400,{'error':'Informe seu nome.'})
                        try: c.execute('INSERT INTO users VALUES(?,?,?,?)',(uid,email,name,password(pw)))
                        except sqlite3.IntegrityError: return self.send(409,{'error':'Não foi possível cadastrar este e-mail.'})
                    else:
                        u=c.execute('SELECT * FROM users WHERE email=?',(email,)).fetchone()
                        encoded=password(pw,u['password'].split(':')[0] if u else 'invalid')
                        if not u or not hmac.compare_digest(encoded,u['password']): return self.send(401,{'error':'E-mail ou senha incorretos.'})
                        uid=u['id']
                    sid=secrets.token_urlsafe(32); c.execute('INSERT INTO sessions VALUES(?,?,?)',(sid,uid,int(time.time())+86400))
                    secure='; Secure' if os.getenv('ASSINAJA_SECURE_COOKIES')=='1' else ''
                    c.commit()
                    return self.send(200,{'ok':True},cookie=f'session={sid}; HttpOnly; SameSite=Strict; Path=/; Max-Age=86400{secure}')
                if path=='/api/logout':
                    cookie=SimpleCookie(); cookie.load(self.headers.get('Cookie',''))
                    if cookie.get('session'): c.execute('DELETE FROM sessions WHERE id=?',(cookie['session'].value,))
                    c.commit()
                    return self.send(200,{'ok':True},cookie='session=; HttpOnly; SameSite=Strict; Path=/; Max-Age=0')
                if path=='/api/documents':
                    if not user: return self.send(401,{'error':'Entre na sua conta.'})
                    title=str(data.get('title','')).strip()[:150]; recipient=str(data.get('recipient','')).strip().lower()
                    if not title or '@' not in recipient or len(recipient)>254: return self.send(400,{'error':'Informe título e e-mail do signatário.'})
                    pdf=base64.b64decode(data.get('pdf',''),validate=True)
                    if not pdf.startswith(b'%PDF-') or len(pdf)>10_000_000: return self.send(400,{'error':'Envie um PDF de até 10 MB.'})
                    did=secrets.token_hex(16); token=secrets.token_urlsafe(32)
                    c.execute('INSERT INTO documents(id,owner,title,filename,pdf,sha256,recipient,token,created) VALUES(?,?,?,?,?,?,?,?,?)',(did,user['id'],title,'documento.pdf',pdf,hashlib.sha256(pdf).hexdigest(),recipient,token,int(time.time())))
                    record(c,did,'created'); c.commit(); return self.send(201,{'id':did,'token':token})
                if path.startswith('/api/sign/'):
                    token=path.split('/')[-1]; name=str(data.get('name','')).strip()[:150]
                    if data.get('consent') is not True or len(name)<3: return self.send(400,{'error':'Informe seu nome e aceite os termos.'})
                    c.execute('BEGIN IMMEDIATE')
                    d=c.execute('SELECT * FROM documents WHERE token=?',(token,)).fetchone()
                    if not d: return self.send(404,{'error':'Link inválido.'})
                    if d['signed']: return self.send(409,{'error':'Documento já assinado.'})
                    c.execute('UPDATE documents SET signed=?,signer=?,ip=?,user_agent=? WHERE id=?',(int(time.time()),name,self.client_address[0],self.headers.get('User-Agent','')[:500],d['id']))
                    record(c,d['id'],'signed','Aceite expresso e nome informado pelo portador do link; identidade não verificada.')
                    c.commit()
                    return self.send(200,{'ok':True})
                return self.send(404,{'error':'Não encontrado.'})
        except (ValueError,TypeError,KeyError): return self.send(400,{'error':'Dados inválidos.'})
if __name__=='__main__':
    port=int(os.getenv('PORT','3000'))
    print(f'AssinaJá na porta {port}',flush=True)
    ThreadingHTTPServer((os.getenv('HOST','127.0.0.1'),port),Handler).serve_forever()
