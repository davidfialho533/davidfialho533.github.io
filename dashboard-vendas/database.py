import os
from functools import lru_cache
from pathlib import Path
from urllib.parse import quote_plus

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

load_dotenv(Path(__file__).parent / ".env")

DEFAULT_SALES_QUERY = """
SELECT
    nf.data_emissao                        AS data,
    (ni.quantidade * ni.valor_unitario)    AS valor,
    p.descricao                            AS produto,
    g.grupo                                AS categoria,
    ni.quantidade                          AS quantidade,
    c.nome                                 AS cliente,
    nf.numero_nf                           AS documento
FROM notas_fiscais nf
JOIN notas_fiscais_itens ni ON ni.id_nota_fiscal = nf.id
JOIN produtos p             ON p.id = ni.id_produto
JOIN grupos g               ON g.id = p.id_grupo
JOIN clientes c               ON c.id = nf.id_cliente
ORDER BY nf.data_emissao DESC
"""


def get_database_url() -> str:
    host = os.getenv("MYSQL_HOST", "localhost")
    port = os.getenv("MYSQL_PORT", "3306")
    user = quote_plus(os.getenv("MYSQL_USER", "root"))
    password = quote_plus(os.getenv("MYSQL_PASSWORD", ""))
    database = os.getenv("MYSQL_DATABASE", "projeto_login")

    return f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}"


@lru_cache(maxsize=1)
def get_engine() -> Engine:
    return create_engine(get_database_url(), pool_pre_ping=True)


def get_sales_query() -> str:
    custom_query = os.getenv("SALES_QUERY", "").strip()
    return custom_query or DEFAULT_SALES_QUERY


def load_sales_data() -> pd.DataFrame:
    query = get_sales_query()
    with get_engine().connect() as connection:
        df = pd.read_sql(text(query), connection)

    df["data"] = pd.to_datetime(df["data"], errors="coerce")
    df["valor"] = pd.to_numeric(df["valor"], errors="coerce")
    if "quantidade" in df.columns:
        df["quantidade"] = pd.to_numeric(df["quantidade"], errors="coerce")

    return df.dropna(subset=["data", "valor"])
