"""Backup consistente do SQLite. O arquivo contém dados pessoais e PDFs."""
import argparse
import os
import sqlite3
from pathlib import Path


def backup(source, destination):
    source, destination = Path(source).resolve(), Path(destination).resolve()
    if not source.is_file():
        raise ValueError('Banco de origem não encontrado.')
    if source == destination:
        raise ValueError('Origem e destino devem ser diferentes.')
    # Não sobrescrever backups existentes, nem seguir links simbólicos.
    fd = os.open(destination, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    os.close(fd)
    try:
        with sqlite3.connect(source.as_uri() + '?mode=ro', uri=True) as src:
            with sqlite3.connect(destination) as dst:
                src.backup(dst)
                if dst.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
                    raise ValueError('A verificação de integridade do backup falhou.')
    except Exception:
        destination.unlink(missing_ok=True)
        raise
    return destination


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source')
    parser.add_argument('destination')
    args = parser.parse_args()
    backup(args.source, args.destination)
    print('Backup concluído e integridade verificada. Proteja o arquivo como dado confidencial.')
