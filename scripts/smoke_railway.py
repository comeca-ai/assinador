"""Valida imagem Docker local e persistência; remove somente os recursos temporários que cria."""
import json, os, secrets, subprocess, time
name='assinaja-check-'+secrets.token_hex(5)
volume=name+'-data'
env=os.environ.copy()
for key in ['DOCKER_HOST','DOCKER_CONTEXT','DOCKER_TLS','DOCKER_TLS_VERIFY','DOCKER_CERT_PATH']:env.pop(key,None)
def docker(*args,check=True):
 result=subprocess.run(['docker','--host=unix:///var/run/docker.sock',*args],env=env,check=False,capture_output=True,text=True)
 if check and result.returncode:
  print(result.stdout); print(result.stderr); result.check_returncode()
 return result
smoke='''import json,urllib.request,urllib.error,time,base64,os
assert os.getuid()==0 # docker exec usa root; o processo HTTP abaixo roda como UID 10001.
base='http://127.0.0.1:3000'
for _ in range(50):
 try:
  assert json.load(urllib.request.urlopen(base+'/healthz'))=={'status':'ok'}
  break
 except Exception:time.sleep(.1)
else:raise RuntimeError('Servidor não iniciou')
def call(path,body,cookie=None):
 headers={'Content-Type':'application/json'}
 if cookie:headers['Cookie']=cookie
 req=urllib.request.Request(base+path,data=json.dumps(body).encode(),headers=headers)
 with urllib.request.urlopen(req) as r:return json.load(r),r.headers.get('Set-Cookie','')
try:
 user,cookie=call('/api/login',{'email':'docker@example.com','password':'senha-do-teste-docker'})
 assert 'Secure' in cookie
 cookie=cookie.split(';')[0]
 req=urllib.request.Request(base+'/api/documents',headers={'Cookie':cookie})
 docs=json.load(urllib.request.urlopen(req));assert any(d['title']=='Persistência Docker' for d in docs)
 print('REINÍCIO: login e documento persistido confirmados')
except urllib.error.HTTPError as error:
 if error.code!=401:raise
 user,cookie=call('/api/register',{'name':'Teste Docker','email':'docker@example.com','password':'senha-do-teste-docker'})
 assert 'Secure' in cookie and 'HttpOnly' in cookie
 cookie=cookie.split(';')[0]
 doc,_=call('/api/documents',{'title':'Persistência Docker','recipient':'sign@example.com','pdf':base64.b64encode(b'%PDF-1.4\\n%%EOF').decode()},cookie)
 call('/api/sign/'+doc['token'],{'name':'Teste Docker','consent':True})
 print('INÍCIO: cadastro, cookie Secure, upload e aceite confirmados')
'''
try:
 docker('volume','create',volume)
 docker('run','-d','--name',name,'--mount','type=volume,source='+volume+',target=/data','-e','RAILWAY_ENVIRONMENT_ID=local-test','-e','RAILWAY_VOLUME_MOUNT_PATH=/data','assinaja-railway:local')
 time.sleep(1)
 result=docker('exec',name,'python3','-c',smoke);print(result.stdout.strip())
 # Verifica privilégios do processo HTTP PID 1, não os do comando docker exec.
 result=docker('exec',name,'python3','-c',"from pathlib import Path; s=Path('/proc/1/status').read_text(); assert 'Uid:\\t10001\\t10001\\t10001\\t10001' in s; print('Processo HTTP roda sem root (UID 10001).')")
 print(result.stdout.strip())
 docker('restart',name)
 print(docker('exec',name,'python3','-c',smoke).stdout.strip())
 rejected=docker('run','--rm','-e','RAILWAY_ENVIRONMENT_ID=local-test','assinaja-railway:local',check=False)
 assert rejected.returncode!=0 and 'Adicione um volume' in rejected.stderr
 print('Inicialização sem volume Railway foi recusada corretamente.')
finally:
 docker('rm','-f',name,check=False)
 docker('volume','rm',volume,check=False)
