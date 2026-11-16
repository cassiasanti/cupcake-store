# Situação 1 — Revisão do planejamento (Kaizen)

Revisão dos artefatos do PIT I (Cassia Santi) antes da implementação. O escopo — loja virtual da **Cupcake Store** com área do cliente e área administrativa — foi mantido; abaixo, o que foi ajustado e por quê.

## 1. Escopo
- Mantidas as 19 histórias de usuário e a ordem do backlog priorizado.
- **ID duplicado corrigido:** "Gerenciar estoque" aparecia como **ID 018** na história e como **019** no backlog. Padronizado como **HU-019**.
- **CA#2 da HU-003** (filtro por sabor) pertence à vitrine, não ao painel: implementado na tela **Loja** com chips de sabor.
- **HU-001 CA#4** (login com Google/telefone/Facebook): mantido no backlog como evolução — exige credenciais OAuth de produção. Os botões aparecem desabilitados na tela de login.
- **HU-007** (pagamento): o PIT previa Pix e dinheiro (`payment_pix_is_active`, `payment_cash_is_active`). O Pix gera BR Code e QR Code reais; a confirmação bancária é simulada.

## 2. Modelo de dados (diagrama de classes → projeto físico)

| Mudança | Motivo |
|---|---|
| `profiles.user_id` (FK, UNIQUE) | O diagrama mostrava a associação 1:1 users–profiles sem a chave. |
| `products.flavor` | Necessário para o filtro por sabor (HU-003 CA#2). |
| Nova tabela `order_items` | Guarda nome e preço **no momento da compra**; mudar o preço depois não altera pedidos antigos. |
| Nova tabela `order_status_history` | Linha do tempo do pedido (HU-004) e RN "status atualizado automaticamente" (HU-007). |
| Nova tabela `audit_logs` | Rastreabilidade exigida em HU-015 RN#1 e HU-017 CA#3. |
| `stocks.note` | Observação da movimentação (ex.: "Venda – pedido #12"). |
| `store_configs.cancel_window_minutes` | "Prazo estabelecido" para cancelamento (HU-008 CA#1) configurável pelo admin. |
| `store_configs.store_name`, `opening_hours` | Caso de uso #C18 cita nome e horário de funcionamento. |
| Removido `orders.delivery_detail_d` | Redundante: `order_delivery_details.order_id` já faz o vínculo (e o nome tinha erro de digitação). |
| `CHECK` em status, tipo de movimento, preço > 0, estoque ≥ 0 | Domínio do atributo garantido no próprio banco. |
| `sqlite_master` / `sqlite_sequence` | São tabelas internas do SQLite; não fazem parte do modelo. |

O modelo lógico está **normalizado (3FN)**. As únicas redundâncias são intencionais: `order_items` e `order_delivery_details` registram o histórico como estava na hora da compra, e `products.current_stock` é um saldo mantido de forma atômica junto com `stocks`.

## 3. IHC
- O layout seguiu os **mockups** do PIT: navbar com Home/Carrinho/Pedidos/Perfil, cards de produto com borda, checkout em formato de nota, admin com menu lateral cinza e cards coloridos no dashboard.
- **Melhorias aplicadas:**
  - confirmação visual ao adicionar ao carrinho, sem recarregar a página (HU-011 CA#3);
  - medidor de força de senha;
  - confirmação digitando o nome do produto antes de excluir (HU-016 RNF);
  - movimentações de estoque em verde/vermelho (HU-019 RNF);
  - linha do tempo do pedido;
  - máscaras de CEP e telefone;
  - layout responsivo para celular (HU-003 RNF).
- **Mensagens de erro:** todas as regras de negócio retornam mensagens claras em português (ex.: "Só temos 4 unidade(s) de 'Café com Chocolate' em estoque."). Também há páginas próprias para os erros 400, 403, 404, 413 e 500.

## 4. Diagrama de classes revisado
Ver [`diagrama_classes.puml`](diagrama_classes.puml) (PlantUML).
