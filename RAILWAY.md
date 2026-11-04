# AssinaJá na Railway

Implantação preparada para piloto com dados fictícios. Nenhum projeto, plano, volume ou domínio Railway foi criado nesta sessão. Não há credenciais Railway disponíveis. A documentação online foi bloqueada pela rede; railway.toml precisa ser confirmado pelo próprio deploy. A imagem não instala dependências nem usa GitHub Actions.

## Publicar pelo painel, sem compartilhar token

1. No painel Railway, crie um projeto → Deploy from GitHub repo → `comeca-ai/assinador`, branch `main`.
2. Antes de testar cadastro, adicione ao serviço um **volume persistente montado em `/data`**. Sem volume, o entrypoint recusa iniciar no ambiente Railway para evitar perda silenciosa de documentos. Mantenha uma única réplica.
3. O Dockerfile configura `HOST=0.0.0.0`, `ASSINAJA_DATA_DIR=/data/assinaja` e `ASSINAJA_SECURE_COOKIES=1`; o servidor usa `PORT` fornecido pela plataforma. Não selecione o projeto Node/Workers: o backend escolhido é Python via Dockerfile.
4. Em Networking, gere um domínio público HTTPS e execute/reexecute o deploy. O entrypoint utiliza root apenas para preparar a subpasta da aplicação e depois roda como UID 10001. Não altera outras pastas do volume.
5. Confira os logs de startup e a resposta `/healthz`. Abra a URL gerada para testar cadastro, upload de PDF fictício, link de aceite e comprovante.
6. Reinicie o serviço e confirme que os documentos de teste ainda existem. Apenas depois de confirmar o domínio real e a persistência, apontar a demonstração GitHub Pages para ele.

A conta Railway pode exigir créditos/plano/cadastro de pagamento; verificar no painel. Não foi presumida hospedagem gratuita nem autorizado aumento de plano.

## Limites do piloto

Esta opção usa o servidor HTTP Python existente, destinado a desenvolvimento/piloto, não a produção aberta. Ainda faltam runtime/reverse proxy endurecidos, rate limiting/antiabuso, verificação de identidade/e-mail, recuperação de senha, política de retenção e LGPD, validação/varredura de PDFs, backups externos e monitoramento. O volume não substitui backup. O IP do comprovante continua sendo o peer TCP do proxy, não uma identidade verificada de cliente. Não confie em cabeçalhos de IP sem confirmar o contrato do provedor.

O registro é aceite eletrônico por link, sem ICP-Brasil nem assinatura criptográfica no PDF. Portadores do link conseguem ler e aceitar. Não envie documentos reais confidenciais antes de concluir as revisões descritas no README. Ads não está ativo. Banco Python e D1 da alternativa Cloudflare não são intercambiáveis automaticamente.

## Operação

Schema inicial criado automaticamente sem apagar dados existentes. Não excluir o volume para corrigir deploy. Dados em `/data/assinaja/assinaja.sqlite3`; cópias devem usar `scripts/backup.py` a partir de ambiente autorizado com acesso ao disco, conforme README. Fazer backup antes de qualquer migração. Rollback do código não restaura dados.

## Evidência local

Imagem construída com sucesso. Verificados no contêiner: cadastro, cookie Secure/HttpOnly, upload e aceite, processo HTTP UID 10001, login e documento preservados após reinício com volume e rejeição de inicialização Railway sem volume. Os recursos Docker temporários foram removidos. O teste pode ser repetido com `docker build -t assinaja-railway:local .` e `python3 scripts/smoke_railway.py` em ambiente autorizado com Docker local. Esse resultado não comprova deploy nem persistência remota na Railway.
