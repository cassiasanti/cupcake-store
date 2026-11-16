# Manual de uso — Cupcake Store

## Instalação
1. Instale o **Python 3.10+**.
2. Na pasta do projeto, rode `pip install -r requirements.txt`.
3. Rode `python run.py` e abra **http://127.0.0.1:5000**.

## Cliente

| Tarefa | Como fazer |
|---|---|
| Criar conta | **Criar conta** → nome, sobrenome, e-mail e senha forte (8+ caracteres, maiúscula, minúscula, número e símbolo). |
| Entrar | **Entrar** → e-mail e senha. |
| Escolher cupcakes | Na **Loja**, filtre por sabor (Chocolate, Baunilha…) ou busque pelo nome. Clique na foto para ver detalhes e ingredientes. |
| Adicionar ao carrinho | **Adicionar ao carrinho** — aparece uma confirmação e o contador do menu é atualizado. |
| Revisar o carrinho | **Carrinho** → altere a quantidade com − / + ou remova itens pela lixeira. |
| Finalizar | **Finalizar compra** → escolha **Pix** ou **Dinheiro** e **Entregar** ou **Retirar na loja** → **Finalizar**. |
| Pagar com Pix | Na página do pedido, escaneie o QR Code ou copie o código. Neste protótipo, clique em **Já paguei** para simular a confirmação do banco. |
| Acompanhar | **Pedidos** → **Detalhes**: mostra a linha do tempo do pedido. |
| Cancelar | Na página do pedido, **Cancelar pedido** (disponível até o envio e dentro do prazo da loja). |
| Atualizar dados | **Perfil** → *Detalhes do perfil* (endereço e telefone) ou *Detalhes da conta* (e-mail e senha). |

## Administrador
Entre com uma conta de administrador; o botão **Dashboard** aparece no menu.

| Tela | Funções |
|---|---|
| Dashboard | Totais de pedidos, vendas, usuários e produtos; pedidos recentes; vendas dos últimos 7 dias; produtos com estoque baixo. |
| Pedidos | Filtrar por status, cliente ou período e ordenar. Abrir o pedido para avançar o status (Pago → Em preparo → Saiu p/ entrega → Entregue) ou cancelar. |
| Usuários | Buscar e filtrar; adicionar usuário; editar dados; ativar ou desativar conta; dar ou remover acesso de admin; redefinir senha. Todas as ações ficam registradas na auditoria. |
| Produtos | Adicionar (com foto e estoque inicial), editar (com histórico de alterações) e excluir. A exclusão pede para digitar o nome do produto e não pode ser desfeita. |
| Estoque › Gerenciar | Escolher o produto, Entrada ou Saída, quantidade e observação. |
| Estoque › Movimentações | Histórico em verde (entradas) e vermelho (saídas), com filtros e saldo. |
| Configurar loja | **Endereço** (dados da loja física), **Pagamento** (Pix com chave e/ou dinheiro), **Entrega** (taxa, ativar/desativar, prazo de cancelamento). |
