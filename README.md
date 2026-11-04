# AssinaJá

Base funcional de desenvolvimento para aceite eletrônico de documentos. Python 3.12+, SQLite e frontend sem dependências externas. Interface própria; o site Dattasign não pôde ser consultado devido à política de rede.

## Executar

```sh
cd /workspace/assinador
python3 server.py
```

Porta padrão: 3000, escuta somente em loopback. `PORT`, `HOST`, `ASSINAJA_DATA_DIR` e `ASSINAJA_SECURE_COOKIES=1` configuram o runtime. Não habilite exposição pública sem as medidas abaixo. O diretório `.local/` contém banco, PDFs e dados pessoais; é ignorado pelo Git e deve ser protegido e incluído na política de retenção/backups.

## Fluxo disponível

Cadastro, login com senha scrypt, sessão HttpOnly de 24 horas, upload de PDF até 10 MB, listagem privada por usuário, link aleatório para um signatário, leitura do original, aceite expresso e nome, prevenção de segundo aceite, hash SHA-256 do original, histórico de criação/aceite e comprovante JSON para o proprietário. Compartilhamento do link é manual. O IP registrado é o peer TCP; não se confia em cabeçalhos de proxy arbitrários.

## Limites de produção

Não há verificação de e-mail/identidade, envio de e-mail, recuperação de senha, limites por IP, MFA, revogação/expiração de links, múltiplos signatários, posicionamento de assinatura no PDF, certificado ICP-Brasil, carimbo de tempo independente ou trilha de auditoria imutável. Um portador do link pode consultar e aceitar o documento. O comprovante é evidência local de aceite e não uma assinatura criptográfica do PDF. A validade jurídica depende do contexto e das evidências; nenhuma certificação é alegada.

Antes de produção: revisão de segurança e LGPD, termos/política de privacidade, autenticação/verificação dos signatários, rate limiting no proxy, HTTPS e cookies Secure, scanner/validação de PDFs, logs operacionais sem tokens, armazenamento/backups protegidos, retenção/exclusão de dados, monitoramento e escolha do provedor de assinatura/certificados, e-mail e eventual cobrança. O servidor HTTP padrão do Python é destinado a desenvolvimento. O ambiente tem `noindex` para não indexar documentos/protótipo.

## Validação

```sh
python3 -m unittest discover -s tests -v
```

## Anúncios

Veja `ADS.md`. Nenhuma campanha ou rastreamento está ativo.

## GitHub Pages

`docs/` contém a demonstração estática. A publicação ativa usa a branch `gh-pages`, pasta `/ (root)`, em Settings → Pages → Deploy from a branch. O workflow alternativo está disponível somente para execução manual e não é necessário para esse modo. Alterações em `docs/` precisam ser enviadas também à branch `gh-pages`. GitHub Pages não executa `server.py`; o sistema de assinatura requer hospedagem separada.

## Preparação para hospedagem do sistema

O servidor deve servir a interface e a API na mesma origem HTTPS; assim não é necessário expor cookies entre GitHub Pages e outro domínio. A demonstração do Pages pode posteriormente apontar para esse endereço. Não foi escolhido nem contratado um provedor.

Requisitos: Python 3.12+, um único serviço com volume persistente local para SQLite, HTTPS no proxy, cookies Secure e armazenamento/backup protegidos. Evite disco efêmero e múltiplas réplicas com bancos locais independentes. Não publique o servidor HTTP de desenvolvimento diretamente; é necessário preparar o runtime e o proxy compatíveis com o provedor escolhido.

Variáveis não secretas: `ASSINAJA_DATA_DIR` deve apontar para o volume; `ASSINAJA_SECURE_COOKIES=1` em HTTPS. O proxy deve preservar o Host público para as verificações de origem. A rota `/healthz` verifica acesso ao banco e retorna `{"status":"ok"}`. Ela não certifica durabilidade de disco ou prontidão para produção.

### Backup e recuperação

```sh
python3 scripts/backup.py .local/assinaja.sqlite3 /caminho-protegido/backup-UNICO.sqlite3
```

O utilitário usa o mecanismo de backup do SQLite, verifica integridade e não sobrescreve arquivos existentes. O backup inclui PDFs, dados pessoais e sessões; nunca o coloque em `docs/`, no Git ou em pasta pública. Copie-o para armazenamento protegido externo ao servidor, com retenção definida. Para restaurar, pare o serviço, preserve o banco atual, valide o backup e copie-o para `ASSINAJA_DATA_DIR/assinaja.sqlite3` com acesso restrito antes de reiniciar. Não há automação de backup externo ou restauração de produção configurada.

## Cloudflare

A versão Workers + D1 + R2 está em `cloudflare/`, com configuração Wrangler e testes locais. Consulte [CLOUDFLARE.md](CLOUDFLARE.md) para arquitetura, validação, limites e sequência de implantação. O backend Python continua disponível como alternativa local. Nenhum recurso remoto foi criado.
