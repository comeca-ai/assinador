# Preparação de Ads

Skill aplicada: OpenAI Ads Conversions Setup. Primeira instalação, superfície browser JavaScript e backend Python. Modo pretendido: Pixel, pendente de Pixel ID e verificação do snippet oficial. “asssinaja” foi interpretado provisoriamente como nome da marca, não como Pixel ID confirmado.

Nenhuma instrumentação existente. Nenhum SDK externo é carregado e nenhum dado de documentos, signatários ou contas é enviado a plataformas de anúncios. CAPI não foi solicitado/configurado; não há chave, envio server-side ou necessidade atual de deduplicação Pixel+CAPI.

A documentação pública e o site de referência foram bloqueados pela rede. A referência da skill confirma os nomes dos eventos e o SDK `https://bzrcdn.openai.com/sdk/oaiq.min.js`, mas a ativação fica pendente da consulta ao snippet oficial, Pixel ID e fluxo de consentimento. A política CSP atual bloqueia scripts externos por padrão; alterar apenas para os destinos documentados quando a integração for ativada.

Cobertura planejada:
- `page_viewed`: apenas landing pública, após consentimento. Nunca enviar URLs com tokens de assinatura.
- `registration_completed`: somente após `/api/register` confirmar sucesso; nunca no clique de cadastro.
- `contents_viewed`: opcional quando houver página real de planos/produtos.
- `lead_created`: sem formulário de lead ou integração de CRM, não aplicável no fluxo atual.
- `items_added`, `checkout_started`, `order_created`: sem carrinho, checkout ou pagamentos.
- `appointment_scheduled`: sem agendamento.
- `subscription_created`, `trial_started`: sem planos ou ativação real de teste.

Não medir aceite de documentos como compra ou cadastro. Não transmitir dados de signatários para Ads. Matching de usuário fica pendente de aprovação da base legal/consentimento e da normalização/hash documentados; nenhum dado pessoal será adicionado automaticamente. Opt-out e retirada de consentimento precisam impedir novos eventos. Não enfileirar eventos ocorridos antes da autorização para envio posterior.

A página tem título, descrição, layout responsivo, mensagem clara e CTA real para cadastro. Ainda faltam domínio canônico, páginas jurídicas, preço/oferta, confirmação da marca e termos comerciais antes de direcionar tráfego pago. OpenAI Ads não substitui Google Ads/Meta Ads; esses canais precisam de integrações específicas.

Antes de publicar, o anunciante deve revisar se a implementação satisfaz seus requisitos de privacidade, segurança, consentimento e tratamento de dados.
