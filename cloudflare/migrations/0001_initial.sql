CREATE TABLE users(id TEXT PRIMARY KEY,email TEXT UNIQUE NOT NULL,name TEXT NOT NULL,password TEXT NOT NULL);
CREATE TABLE sessions(id TEXT PRIMARY KEY,user_id TEXT NOT NULL REFERENCES users(id),expires INTEGER NOT NULL);
CREATE INDEX sessions_expiry ON sessions(expires);
CREATE TABLE documents(id TEXT PRIMARY KEY,owner TEXT NOT NULL REFERENCES users(id),title TEXT NOT NULL,object_key TEXT NOT NULL,sha256 TEXT NOT NULL,recipient TEXT NOT NULL,token TEXT UNIQUE NOT NULL,created INTEGER NOT NULL,signed INTEGER,signer TEXT,ip TEXT,user_agent TEXT);
CREATE INDEX documents_owner ON documents(owner,created);
CREATE TABLE audit(id INTEGER PRIMARY KEY AUTOINCREMENT,document_id TEXT NOT NULL REFERENCES documents(id),action TEXT NOT NULL,created INTEGER NOT NULL,detail TEXT NOT NULL DEFAULT '');
CREATE INDEX audit_document ON audit(document_id,id);
