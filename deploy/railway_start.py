"""Inicialização com disco persistente e processo sem privilégios."""
import os
from pathlib import Path
import runpy


def prepare_data():
    data = Path(os.environ.get('ASSINAJA_DATA_DIR', '/data/assinaja')).resolve()
    if os.environ.get('RAILWAY_ENVIRONMENT_ID'):
        mount = os.environ.get('RAILWAY_VOLUME_MOUNT_PATH')
        if not mount:
            raise RuntimeError('Adicione um volume Railway em /data antes de iniciar. Banco em disco efêmero não é permitido.')
        root = Path(mount).resolve()
        if data == root or root not in data.parents:
            raise RuntimeError('ASSINAJA_DATA_DIR deve ser uma subpasta do volume persistente.')
    data.mkdir(parents=True, exist_ok=True)
    os.chmod(data, 0o700)
    if os.getuid() == 0:
        uid = gid = 10001
        os.chown(data, uid, gid)
        # Não percorrer nem alterar conteúdo arbitrário do volume.
        for name in ['assinaja.sqlite3', 'assinaja.sqlite3-wal', 'assinaja.sqlite3-shm', 'assinaja.sqlite3-journal']:
            file = data / name
            if file.is_symlink():
                raise RuntimeError('Link simbólico inesperado na pasta do banco.')
            if file.exists():
                os.chown(file, uid, gid)
                os.chmod(file, 0o600)
        os.setgroups([])
        os.setgid(gid)
        os.setuid(uid)
    os.umask(0o077)
    os.environ['ASSINAJA_DATA_DIR'] = str(data)

if __name__ == '__main__':
    prepare_data()
    runpy.run_path(str(Path(__file__).resolve().parents[1] / 'server.py'), run_name='__main__')
