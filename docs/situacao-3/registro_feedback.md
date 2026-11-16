# Registro de feedback e correções

## 1. Teste exploratório interno — 15/11/2026

Teste feito pelo desenvolvedor (com apoio de IA), percorrendo os fluxos do cliente e do administrador num banco limpo.

| # | Funcionalidade | Problema encontrado | Severidade | Decisão | Status |
|---|---|---|---|---|---|
| 1 | Checkout (HU-006) | Conta sem endereço vinha com "Entregar no endereço" marcado e só recebia o erro **depois** de clicar em Finalizar. | Média | Corrigir | ✅ Corrigido — "Retirar na loja" vem marcado; ao escolher entrega aparece aviso com link para o Perfil e o botão Finalizar fica desabilitado. Teste: `test_checkout_without_address_defaults_to_pickup`. |
| 2 | Gerenciar usuários (HU-017) | Campo "Redefinir senha" exibia a nova senha em texto aberto na tela do admin. | Média (segurança) | Corrigir | ✅ Corrigido — campo do tipo senha + dica de requisitos. Teste: `test_reset_password_field_is_hidden`. |
| 3 | Editar produto (HU-015) | Preço exibido como "9.9" em vez de "9,90" no formulário. | Baixa | Corrigir | ✅ Corrigido — preço e taxa de entrega exibidos como "9,90". Teste: `test_product_form_shows_brazilian_price`. |
| 4 | Dashboard admin | Card "Vendas" abre só pedidos *entregues*, mas o valor soma também pedidos pagos e em andamento. | Baixa | Corrigir | ✅ Corrigido — o card abre a lista com exatamente os pedidos que somam o valor (pagos, em preparo, enviados e entregues). Teste: `test_sales_card_lists_same_orders_as_its_total`. |

## 2. Testes com usuários (Situação 3)

Formulários individuais em `formularios_testadores.pdf`. Preencher esta tabela com as respostas recebidas.

| # | Testador | Data | Problema / sugestão relatada | Decisão | Correção (commit) |
|---|---|---|---|---|---|
| 1 | Vinicius Santos | 15/11/2026 | | | |
| 2 | Norri Paixão | 15/11/2026 | | | |
| 3 | Getúlio Paixão | 15/11/2026 | | | |
| 4 | Cristian Kasikawa | 15/11/2026 | | | |
| 5 | Julie Kasikawa | 15/11/2026 | | | |
