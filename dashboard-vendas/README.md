# Dashboard de Vendas

Dashboard interativo em Python conectado a um banco MySQL existente.

## Stack

- **Streamlit** — interface web
- **Pandas** — manipulação dos dados
- **Matplotlib** — gráficos
- **scikit-learn** — previsão de receita
- **SQLAlchemy + PyMySQL** — conexão com MySQL

## Pré-requisitos

- Python 3.11+
- MySQL com dados de vendas
- [Poetry](https://python-poetry.org/) (ou use o `.venv` já criado)

## Instalação

```powershell
cd dashboard-vendas
copy .env.example .env
# Edite .env com host, usuário, senha e banco do MySQL
python -m poetry install
```

## Executar

```powershell
python -m poetry run streamlit run app.py
```

Ou, com o venv ativo:

```powershell
.\.venv\Scripts\Activate.ps1
streamlit run app.py
```

## Estrutura do banco (`projeto_login`)

O dashboard usa as tabelas de notas fiscais do seu sistema:

- `notas_fiscais` — cabeçalho da venda (data, cliente, número NF)
- `notas_fiscais_itens` — itens vendidos (produto, quantidade, valor unitário)
- `produtos` — descrição do produto
- `grupos` — categoria do produto
- `clientes` — nome do cliente

Query padrão (pode sobrescrever com `SALES_QUERY` no `.env`):

```sql
SELECT
    nf.data_emissao AS data,
    (ni.quantidade * ni.valor_unitario) AS valor,
    p.descricao AS produto,
    g.grupo AS categoria,
    ni.quantidade AS quantidade,
    c.nome AS cliente
FROM notas_fiscais nf
JOIN notas_fiscais_itens ni ON ni.id_nota_fiscal = nf.id
JOIN produtos p ON p.id = ni.id_produto
JOIN grupos g ON g.id = p.id_grupo
JOIN clientes c ON c.id = nf.id_cliente
```

## Funcionalidades

- KPIs: receita total, pedidos, ticket médio e itens vendidos
- Gráfico de receita por dia
- Top 10 produtos e participação por categoria
- Previsão de receita (regressão linear)
- Filtros por período, categoria e produto
