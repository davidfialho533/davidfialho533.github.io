import os
import random
from datetime import date, timedelta

import pymysql
from dotenv import load_dotenv

load_dotenv()

conn = pymysql.connect(
    host=os.getenv("MYSQL_HOST"),
    user=os.getenv("MYSQL_USER"),
    password=os.getenv("MYSQL_PASSWORD"),
    database=os.getenv("MYSQL_DATABASE"),
    port=int(os.getenv("MYSQL_PORT", 3306)),
)
cur = conn.cursor()

cur.execute("SELECT id FROM clientes")
cliente_ids = [r[0] for r in cur.fetchall()]

cur.execute("SELECT id, descricao FROM produtos WHERE ativo = 1")
produtos = cur.fetchall()

cur.execute("SELECT id FROM centro_de_custo LIMIT 1")
centro_custo_id = cur.fetchone()[0]

cur.execute("SELECT id FROM empresas LIMIT 1")
empresa_id = cur.fetchone()[0]

cur.execute("SELECT MAX(CAST(SUBSTRING(numero_nf, 4) AS UNSIGNED)) FROM notas_fiscais WHERE numero_nf LIKE 'PDV%'")
max_pdv = cur.fetchone()[0] or 0

year_start = date(2026, 1, 1)
year_end = date(2026, 6, 16)
total_days = (year_end - year_start).days

print(f"Clientes: {len(cliente_ids)}, Produtos: {len(produtos)}")
print(f"Centro custo: {centro_custo_id}, Empresa: {empresa_id}")
print(f"Inserindo 200 notas fiscais...")

inserted_nfs = 0
inserted_itens = 0

for i in range(200):
    nf_num = max_pdv + i + 1
    numero_nf = f"PDV{nf_num}"
    data_emissao = year_start + timedelta(days=random.randint(0, total_days))
    id_cliente = random.choice(cliente_ids)
    qtd_itens = random.randint(1, 3)

    cur.execute(
        """
        INSERT INTO notas_fiscais
            (numero_nf, serie_nf, data_emissao, id_cliente, id_centro_custo, id_empresa, observacao)
        VALUES (%s, '1', %s, %s, %s, %s, %s)
        """,
        (numero_nf, data_emissao, id_cliente, centro_custo_id, empresa_id, "Insert automatico dashboard"),
    )
    nf_id = cur.lastrowid
    inserted_nfs += 1

    produtos_nf = random.sample(produtos, min(qtd_itens, len(produtos)))
    for produto_id, _ in produtos_nf:
        quantidade = round(random.uniform(1, 20), 3)
        valor_unitario = round(random.uniform(0.5, 150.0), 4)
        cur.execute(
            """
            INSERT INTO notas_fiscais_itens
                (id_nota_fiscal, id_produto, quantidade, valor_unitario)
            VALUES (%s, %s, %s, %s)
            """,
            (nf_id, produto_id, quantidade, valor_unitario),
        )
        inserted_itens += 1

conn.commit()
conn.close()

print(f"Concluido: {inserted_nfs} notas fiscais, {inserted_itens} itens.")
