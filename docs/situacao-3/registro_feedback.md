# Registro de feedback e correções

## 1. Teste exploratório interno — 15/11/2026

Teste feito pelo desenvolvedor, percorrendo os fluxos do cliente e do administrador num banco limpo.

| # | Funcionalidade | Problema encontrado | Severidade | Decisão | Status |
|---|---|---|---|---|---|
| 1 | Checkout (HU-006) | Conta sem endereço vinha com "Entregar no endereço" marcado e só recebia o erro **depois** de clicar em Finalizar. | Média | Corrigir | ✅ Corrigido — "Retirar na loja" vem marcado; ao escolher entrega aparece aviso com link para o Perfil e o botão Finalizar fica desabilitado. Teste: `test_checkout_without_address_defaults_to_pickup`. |
| 2 | Gerenciar usuários (HU-017) | Campo "Redefinir senha" exibia a nova senha em texto aberto na tela do admin. | Média (segurança) | Corrigir | ✅ Corrigido — campo do tipo senha + dica de requisitos. Teste: `test_reset_password_field_is_hidden`. |

## 2. Testes com usuários (Situação 3)

Formulários individuais em `formularios_testadores.pdf`. Preencher esta tabela com as respostas recebidas.

| # | Testador | Data | Problema / sugestão relatada | Decisão | Correção (commit) |
|---|---|---|---|---|---|
| 1 | Vinicius Santos | 15/11/2026 | Com conta sem endereço, a entrega vinha marcada e o erro só aparecia | Correção (Avisar antes e deixar como padrão) | Versão Oficial v1.1 |
| 2 | Norri Paixão | 15/11/2026 | Erro de endereço na finalização de pedido via Pix | Mostrar o aviso já na tela do checkout | Versão Oficial v1.1 |
| 3 | Getúlio Paixão | 15/11/2026 | Preço com valor em formato diferente do brasileiro '9.9 ao invés de 9,90 | Exibição no formato brasileiro | Versão Oficial v1.1 |
| 4 | Cristian Kasikawa | 15/11/2026 | Valor incorreto na aba Dashboard de pedidos | Abrir uma lista com os mesmos pedidos que compõem o valor | Versão Oficial v1.1 |
| 5 | Julie Kasikawa | 15/11/2026 | NA | NA | NA |
