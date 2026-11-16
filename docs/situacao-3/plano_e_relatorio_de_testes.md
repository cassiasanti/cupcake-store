# Situação 3 — Plano e relatório de testes

## Estratégia
| Nível | Ferramenta | O que cobre |
|---|---|---|
| **Unitário** (`tests/test_models.py`) | pytest | Regras de negócio de cada Model, isoladas da web: validações, cálculos, transições de status, estoque. |
| **Integração** (`tests/test_controllers.py`) | pytest + Flask test client | Rotas completas (Controller + Model + View + banco): fluxos de compra, permissões, mensagens de erro, CSRF. |
| **Validação com usuários** | Formulário (`formulario_teste_usuario.md`) | 5 colegas/profissionais testam a solução e reportam bugs e sugestões. |

Cada teste roda num banco SQLite temporário e novo, criado a partir de `schema.sql` com os dados de demonstração.

**Como executar:** `python -m pytest -v`

## Matriz de rastreabilidade (História → Testes)
| HU | Critério / regra verificada | Testes |
|---|---|---|
| 001 | E-mail válido e único; senha forte; confirmação | `TestUser::test_create_user_ok`, `test_weak_password_rejected`, `test_password_mismatch`, `test_email_unique_and_valid`, `test_register_flow`, `test_register_weak_password_shows_error` |
| 002 | Login, senha com hash, conta inativa bloqueada | `test_authenticate`, `test_password_is_hashed`, `test_inactive_user_cannot_login`, `test_login_logout` |
| 003 | Filtro por sabor, paginação, painel após login | `TestProduct::test_filter_by_flavor`, `test_pagination`, `test_public_pages`, `test_full_purchase_flow` |
| 004/005 | Pedido visível só para o dono; histórico de status | `test_other_user_cannot_see_order`, `test_user_cannot_see_others_order`, `test_confirm_pix` |
| 006 | Checkout baixa estoque, calcula total, exige endereço para entrega | `test_checkout_creates_order_and_lowers_stock`, `test_delivery_requires_address`, `test_empty_cart`, `test_cash_goes_to_preparation` |
| 007 | Forma de pagamento válida/ativa; Pix BR Code com CRC; confirmação | `test_invalid_payment`, `test_disabled_payment_method`, `test_pix_crc`, `test_pix_payload_is_ascii`, `test_confirm_pix` |
| 008 | Cancelar só antes do envio e dentro do prazo; estorna estoque | `test_cancel_returns_stock`, `test_cannot_cancel_after_dispatch`, `test_cancel_window_expired` |
| 009 | Atualizar perfil (CEP/telefone válidos) e senha | `test_update_profile_validation`, `test_change_password`, `test_profile_update` |
| 010–012 | Adicionar/somar/alterar/remover; limite de estoque; produto inativo | `TestCart::*`, `test_cart_errors_are_friendly` |
| 013 | Validação do produto antes de publicar | `TestProduct::test_validation`, `test_create_and_catalog`, `test_admin_product_crud` |
| 014 | Lista de pedidos com filtros | `test_admin_pages` |
| 015 | Alteração refletida e auditada; preço do carrinho atualizado | `test_update_is_audited_and_updates_cart_price` |
| 016 | Exclusão irreversível, sai do catálogo e dos carrinhos; confirmação | `test_delete_removes_from_catalog_and_carts`, `test_admin_product_crud` |
| 017 | Ativar/desativar, auditoria, admin não se desativa | `test_admin_cannot_deactivate_self`, `test_admin_stock_and_users` |
| 018 | Ao menos um pagamento ativo; chave Pix obrigatória; taxa ≥ 0 | `TestStoreConfig::*`, `test_admin_config` |
| 019 | Entrada/saída, saldo nunca negativo, histórico | `TestStock::*`, `test_admin_stock_and_users` |
| RNF | Rotas protegidas, acesso admin, CSRF, transições de status válidas | `test_protected_routes_redirect_to_login`, `test_client_cannot_access_admin`, `test_csrf_protection`, `test_invalid_status_transition`, `test_admin_order_status` |

## Resultado da última execução
**65 de 65 testes aprovados.**

| Teste | Resultado |
|---|---|
| test_controllers.py::test_public_pages | ✅ Passou |
| test_controllers.py::test_register_flow | ✅ Passou |
| test_controllers.py::test_register_weak_password_shows_error | ✅ Passou |
| test_controllers.py::test_login_logout | ✅ Passou |
| test_controllers.py::test_protected_routes_redirect_to_login | ✅ Passou |
| test_controllers.py::test_client_cannot_access_admin | ✅ Passou |
| test_controllers.py::test_full_purchase_flow | ✅ Passou |
| test_controllers.py::test_cart_errors_are_friendly | ✅ Passou |
| test_controllers.py::test_user_cannot_see_others_order | ✅ Passou |
| test_controllers.py::test_profile_update | ✅ Passou |
| test_controllers.py::test_admin_pages | ✅ Passou |
| test_controllers.py::test_admin_product_crud | ✅ Passou |
| test_controllers.py::test_admin_stock_and_users | ✅ Passou |
| test_controllers.py::test_admin_config | ✅ Passou |
| test_controllers.py::test_admin_order_status | ✅ Passou |
| test_controllers.py::test_csrf_protection | ✅ Passou |
| test_models.py::TestUser::test_create_user_ok | ✅ Passou |
| test_models.py::TestUser::test_weak_password_rejected[curta1!] | ✅ Passou |
| test_models.py::TestUser::test_weak_password_rejected[semnumero!A] | ✅ Passou |
| test_models.py::TestUser::test_weak_password_rejected[SEMMINUSC1!] | ✅ Passou |
| test_models.py::TestUser::test_weak_password_rejected[semmaiusc1!] | ✅ Passou |
| test_models.py::TestUser::test_weak_password_rejected[SemEspecial1] | ✅ Passou |
| test_models.py::TestUser::test_password_mismatch | ✅ Passou |
| test_models.py::TestUser::test_email_unique_and_valid | ✅ Passou |
| test_models.py::TestUser::test_password_is_hashed | ✅ Passou |
| test_models.py::TestUser::test_authenticate | ✅ Passou |
| test_models.py::TestUser::test_inactive_user_cannot_login | ✅ Passou |
| test_models.py::TestUser::test_admin_cannot_deactivate_self | ✅ Passou |
| test_models.py::TestUser::test_update_profile_validation | ✅ Passou |
| test_models.py::TestUser::test_change_password | ✅ Passou |
| test_models.py::TestProduct::test_create_and_catalog | ✅ Passou |
| test_models.py::TestProduct::test_validation[name-ab] | ✅ Passou |
| test_models.py::TestProduct::test_validation[description-curta] | ✅ Passou |
| test_models.py::TestProduct::test_validation[price-0] | ✅ Passou |
| test_models.py::TestProduct::test_validation[price-abc] | ✅ Passou |
| test_models.py::TestProduct::test_validation[flavor-Pizza] | ✅ Passou |
| test_models.py::TestProduct::test_update_is_audited_and_updates_cart_price | ✅ Passou |
| test_models.py::TestProduct::test_delete_removes_from_catalog_and_carts | ✅ Passou |
| test_models.py::TestProduct::test_filter_by_flavor | ✅ Passou |
| test_models.py::TestProduct::test_pagination | ✅ Passou |
| test_models.py::TestStock::test_entrada_e_saida | ✅ Passou |
| test_models.py::TestStock::test_saida_maior_que_estoque | ✅ Passou |
| test_models.py::TestStock::test_quantidade_invalida[0] | ✅ Passou |
| test_models.py::TestStock::test_quantidade_invalida[-1] | ✅ Passou |
| test_models.py::TestStock::test_quantidade_invalida[x] | ✅ Passou |
| test_models.py::TestCart::test_add_update_remove | ✅ Passou |
| test_models.py::TestCart::test_cannot_exceed_stock | ✅ Passou |
| test_models.py::TestCart::test_inactive_product | ✅ Passou |
| test_models.py::TestOrder::test_checkout_creates_order_and_lowers_stock | ✅ Passou |
| test_models.py::TestOrder::test_pix_crc | ✅ Passou |
| test_models.py::TestOrder::test_cash_goes_to_preparation | ✅ Passou |
| test_models.py::TestOrder::test_empty_cart | ✅ Passou |
| test_models.py::TestOrder::test_invalid_payment | ✅ Passou |
| test_models.py::TestOrder::test_disabled_payment_method | ✅ Passou |
| test_models.py::TestOrder::test_delivery_requires_address | ✅ Passou |
| test_models.py::TestOrder::test_confirm_pix | ✅ Passou |
| test_models.py::TestOrder::test_cancel_returns_stock | ✅ Passou |
| test_models.py::TestOrder::test_cannot_cancel_after_dispatch | ✅ Passou |
| test_models.py::TestOrder::test_cancel_window_expired | ✅ Passou |
| test_models.py::TestOrder::test_invalid_status_transition | ✅ Passou |
| test_models.py::TestOrder::test_other_user_cannot_see_order | ✅ Passou |
| test_models.py::TestStoreConfig::test_payment_requires_one_method | ✅ Passou |
| test_models.py::TestStoreConfig::test_pix_requires_key | ✅ Passou |
| test_models.py::TestStoreConfig::test_delivery_update | ✅ Passou |
| test_models.py::test_pix_payload_is_ascii | ✅ Passou |

## Testes manuais de interface (verificação)
Telas conferidas em navegador real (Chromium 1366×860 e celular 390×844): login, loja, filtro, detalhe, carrinho, checkout, pedido com QR Code Pix, painel, dashboard, pedidos, estoque, movimentações, produtos, edição de produto, usuários, configurações e diálogo de confirmação de exclusão. As capturas estão em `docs/situacao-2/telas/`.

| Defeito encontrado | Correção |
|---|---|
| Ícones gigantes no bloco Pix (o seletor CSS pegava todos os SVGs) | Seletor restrito ao QR Code (`.pix-box > svg`). |
| Acentos no payload Pix ("SÃO PAULO") quebram o padrão EMV | Normalização para ASCII + teste `test_pix_payload_is_ascii`. |
| Horários exibidos com 3 h de diferença conforme o fuso da máquina | Datas gravadas sempre em UTC e convertidas na exibição. |
| Filtro de movimentações gerava erro sem produto selecionado | `args.get('product_id')` no template + teste `test_admin_pages`. |
