# Sistema Distribuído de Transações

Este projeto é um sistema distribuído composto por três camadas: Banco, Seletor e Validador. Cada camada desempenha um papel específico na gestão e validação de transações de ativos entre clientes.


## Descrição das Camadas

### Banco

- **Função:** Distribui transações e informações das contas atreladas para a camada Seletor.
- **Rotas:**
  - `/trans` - Gerencia as transações de ativos entre clientes.
  - `/hora` - Fornece o horário atual do sistema para sincronização.

### Seletor

- **Função:** Cadastra e verifica a viabilidade dos validadores, seleciona validadores para receber transações ativas e gerencia o consenso das validações.
- **Rotas:**
  - `/seletor` - Cadastro de validadores.
  - `/seletor/select` - Seleção de validadores para transações.

### Validador

- **Função:** Valida transações recebidas do Seletor seguindo as regras do ecossistema.
- **Rotas:**
  - `/validador` - Validação de transações.

## Regras de Validação

- O remetente deve ter saldo suficiente para a transação, incluindo taxas.
- O horário da transação deve ser menor ou igual ao horário atual do sistema e maior que o horário da última transação.
- Limite de 100 transações por minuto para cada remetente.
- Validadores devem retornar uma chave única para confirmar a transação.
- Status da Transação:
  - 1 = Concluída com Sucesso
  - 2 = Não aprovada (erro)
  - 0 = Não executada

## Regras de Seleção

- O Seletor deve escolher pelo menos três validadores para concluir a transação.
- O consenso é gerado com mais de 50% de aprovação ou reprovação.
- O percentual de escolha de validadores é dinâmico, baseado na quantidade de moedas disponibilizadas.
- Validadores com comportamentos inconsistentes ou mal-intencionados são sinalizados e eventualmente removidos da rede.

## Requisitos

- Sistema deve funcionar como um Web Service.
- Algoritmo pertinente para eleição dos validadores.
- Funcionalidade de inserção e remoção de validadores.
- Armazenamento de todos os passos da eleição.
- Diferenciação entre validação bem-sucedida e mal-sucedida.
- Sincronização de tempo entre o sistema Seletor e Validador.
- Desenvolvimento de regras de validação no Validador.
- Identificação de validadores falhos.
- Interligação entre todas as camadas do sistema.
- Tolerância a falhas no Seletor e no Validador.

## Como Executar

### Banco

1. Navegue até o diretório `banco`.
2. Execute o servidor:
    ```bash
    python app.py
    ```

### Seletor

1. Navegue até o diretório `seletor`.
2. Execute o servidor:
    ```bash
    python app.py
    ```

### Validador

1. Navegue até o diretório `validador`.
2. Execute o servidor:
    ```bash
    python app.py
    ```

## Sincronização

Para sincronizar o horário entre o sistema Seletor e o Validador, utilize a rota `/hora` fornecida pela camada Banco.

## Contribuições

Contribuições são bem-vindas! Sinta-se à vontade para abrir issues e pull requests.

## Licença

Este projeto é licenciado sob a [MIT License](LICENSE).



