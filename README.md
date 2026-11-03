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

`docs/` contém uma demonstração estática independente. O workflow `.github/workflows/pages.yml` publica somente essa pasta, sem banco de dados, servidor, documentos ou formulários de cadastro. Em Settings → Pages, selecione GitHub Actions como origem. O workflow executa em push para `main` e manualmente. GitHub Pages não executa `server.py`; o sistema de assinatura requer hospedagem de backend separada.
