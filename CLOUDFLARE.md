# Implantação Cloudflare — versão inicial

Estado: implementação e validação local concluídas; nenhuma conta remota, recurso, domínio ou implantação Cloudflare foi acessado/criado. A documentação online foi bloqueada pela rede. Configuração e bindings foram validados pelo schema e dry-run do Wrangler 4.157.0 instalado no projeto; isso não confirma permissões, disponibilidade, limites ou preços na conta.

## Arquitetura

Worker `assinaja` serve `public/` e `/api/*` na mesma origem. D1 `DB` guarda contas, hashes de sessões, documentos e auditoria. Bucket R2 privado `DOCUMENTS` guarda PDFs; não habilitar r2.dev público. O código autentica a leitura por link aleatório. Portadores do link podem ler e aceitar; identidade não é verificada. Hash de senha PBKDF2-SHA256 com salt individual e 100 mil iterações; sessões armazenadas como hash, cookies HttpOnly/SameSite, Secure em HTTPS. D1 batch torna a alteração de aceite e seu evento atômicos. Dados em SQLite Python não são migrados automaticamente e hashes scrypt não são compatíveis com este runtime.

## Testes reproduzíveis

```sh
npm ci
npm run test:cloudflare
npm run check:cloudflare
npx wrangler d1 migrations apply DB --local
npm run dev:cloudflare
# Em outro terminal, com wrangler dev na porta 8787:
python3 scripts/smoke_cloudflare.py
```

O smoke test só acessa loopback e cria dados fictícios locais. Testa D1/R2 reais emulados, incluindo duas requisições concorrentes de aceite: uma deve retornar 200 e a outra 409, com um único evento. O Wrangler apresentou aviso de ausência de Request.cf por restrição de rede, usando defaults locais; o campo IP real da Cloudflare não foi validado remotamente.

## Pré-requisitos externos

Conta Cloudflare correta identificada, acesso autorizado pelo Wrangler e R2 habilitado. Nenhum plano pago foi contratado. Verificar franquias, limites de CPU/PBKDF2, armazenamento e cobrança atuais na conta antes de publicar. Não criar recursos em uma conta escolhida implicitamente.

Para automação, configure `CLOUDFLARE_API_TOKEN` de forma segura no ambiente, limitado à conta e às operações necessárias em Workers, D1 e R2, e `CLOUDFLARE_ACCOUNT_ID` como variável não secreta. Não cole tokens no chat, no Git ou em arquivos públicos. A presença da variável não comprova autorização: validar `wrangler whoami` e a operação necessária. Se houver múltiplas contas, confirmar o account ID antes de criar recursos.

## Sequência remota (ainda não executada)

1. Validar conta/autorização e recursos existentes para evitar duplicatas.
2. Criar ou selecionar um banco D1 exclusivo: `npx wrangler d1 create assinaja`. Substituir o ID zerado de `wrangler.jsonc` pelo database_id real, preservando bindings. O ID zerado serve apenas ao teste local; nunca publicar assim.
3. Criar ou selecionar bucket R2 privado: `npx wrangler r2 bucket create assinaja-documentos`. Não ativar acesso público.
4. Revisar e aplicar migração inicial: `npx wrangler d1 migrations apply DB --remote`. Não aplicar migração inicial a banco existente de outro projeto. Preservar/exportar dados existentes antes de mudanças.
5. `npx wrangler deploy`, mantendo frontend e API na mesma origem. Não há dependência de créditos GitHub Actions.
6. Confirmar URL real retornada, HTTPS, `/healthz`, assets e fluxo autorizado de teste com dados fictícios. Verificar cookies Secure e indisponibilidade do PDF para URLs incorretas. Não publicar uma URL presumida como confirmação.
7. Somente após validação, adicionar à demonstração GitHub Pages um link para o endereço real do sistema. Não alterar o link público antes.

## Operação e riscos pendentes

Antes de abrir cadastros públicos: proteção antiabuso/rate limiting e limites por conta, verificação de identidade/e-mail, recuperação de acesso, política LGPD/termos e retenção, varredura de PDFs, backups coordenados de D1 e R2 e exercício de recuperação. Não é assinatura criptográfica, ICP-Brasil nem PDF assinado. Não há envio de e-mail, cobrança ou Ads ativo.

O endpoint `/healthz` verifica D1, não a durabilidade nem todas as operações R2. Rollback do Worker não reverte migrações nem arquivos no R2. Registro de auditoria está no banco e não é imutável. Falha entre upload R2 e gravação D1 pode produzir objeto órfão se o cleanup falhar; uma reconciliação operacional permanece pendente. Credenciais/conta, recursos remotos, custos e domínio não foram validados.
