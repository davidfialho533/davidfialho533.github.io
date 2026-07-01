import datetime

import numpy as np
import pandas as pd
import streamlit as st
from matplotlib import pyplot as plt
from matplotlib.dates import DateFormatter
from sklearn.linear_model import LinearRegression

from database import load_sales_data

DATE_FORMAT = "%d/%m/%Y"
DATE_INPUT_FORMAT = "DD/MM/YYYY"
PERIOD_MIN = datetime.date(2000, 1, 1)
PERIOD_MAX = datetime.date(2099, 12, 31)

st.set_page_config(
    page_title="Dashboard de Vendas",
    page_icon="📊",
    layout="wide",
)

st.title("📊 Dashboard de Vendas")
st.caption("Análise de vendas conectada ao MySQL")


@st.cache_data(ttl=300)
def fetch_data():
    return load_sales_data()


def apply_filters(df: pd.DataFrame, start_date, end_date, categories, products, clients) -> pd.DataFrame:
    filtered = df[(df["data"].dt.date >= start_date) & (df["data"].dt.date <= end_date)]

    if categories and "categoria" in filtered.columns:
        filtered = filtered[filtered["categoria"].isin(categories)]

    if products and "produto" in filtered.columns:
        filtered = filtered[filtered["produto"].isin(products)]

    if clients and "cliente" in filtered.columns:
        filtered = filtered[filtered["cliente"].isin(clients)]

    return filtered


def parse_period_selection(period, default_start, default_end):
    if isinstance(period, tuple):
        if len(period) == 2:
            start, end = period
        elif len(period) == 1:
            start = end = period[0]
        else:
            start, end = default_start, default_end
    elif isinstance(period, datetime.date):
        start = end = period
    else:
        start, end = default_start, default_end

    if start > end:
        start, end = end, start

    return start, end


def render_kpis(df: pd.DataFrame) -> None:
    total_vendas = df["valor"].sum()
    qtd_pedidos = len(df)
    ticket_medio = df["valor"].mean() if qtd_pedidos else 0
    qtd_itens = df["quantidade"].sum() if "quantidade" in df.columns else qtd_pedidos

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Receita total", f"R$ {total_vendas:,.2f}")
    col2.metric("Pedidos", f"{qtd_pedidos:,}")
    col3.metric("Ticket médio", f"R$ {ticket_medio:,.2f}")
    col4.metric("Itens vendidos", f"{int(qtd_itens):,}")


def format_date_axis(ax) -> None:
    ax.xaxis.set_major_formatter(DateFormatter(DATE_FORMAT))
    ax.figure.autofmt_xdate()


def plot_sales_over_time(df: pd.DataFrame) -> None:
    daily = df.groupby(df["data"].dt.date)["valor"].sum().reset_index()
    daily.columns = ["data", "valor"]

    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(daily["data"], daily["valor"], marker="o", linewidth=2, color="#2563eb")
    ax.set_title("Receita por dia")
    ax.set_xlabel("Data (DD/MM/AAAA)")
    ax.set_ylabel("Valor (R$)")
    ax.grid(True, alpha=0.3)
    format_date_axis(ax)
    st.pyplot(fig)
    plt.close(fig)


def plot_top_products(df: pd.DataFrame) -> None:
    if "produto" not in df.columns:
        st.info("Coluna `produto` não encontrada nos dados.")
        return

    top = df.groupby("produto")["valor"].sum().sort_values(ascending=False).head(10)

    fig, ax = plt.subplots(figsize=(10, 5))
    top.plot(kind="barh", ax=ax, color="#16a34a")
    ax.set_title("Top 10 produtos por receita")
    ax.set_xlabel("Receita (R$)")
    ax.invert_yaxis()
    st.pyplot(fig)
    plt.close(fig)


def plot_top_clients(df: pd.DataFrame) -> None:
    if "cliente" not in df.columns:
        st.info("Coluna `cliente` não encontrada nos dados.")
        return

    top = df.groupby("cliente")["valor"].sum().sort_values(ascending=False).head(10)

    fig, ax = plt.subplots(figsize=(10, 5))
    top.plot(kind="barh", ax=ax, color="#9333ea")
    ax.set_title("Top 10 clientes por receita")
    ax.set_xlabel("Receita (R$)")
    ax.invert_yaxis()
    st.pyplot(fig)
    plt.close(fig)


def plot_category_share(df: pd.DataFrame) -> None:
    if "categoria" not in df.columns:
        st.info("Coluna `categoria` não encontrada nos dados.")
        return

    by_category = df.groupby("categoria")["valor"].sum()

    fig, ax = plt.subplots(figsize=(6, 6))
    ax.pie(by_category, labels=by_category.index, autopct="%1.1f%%", startangle=90)
    ax.set_title("Participação por categoria")
    st.pyplot(fig)
    plt.close(fig)


def plot_forecast(df: pd.DataFrame, days_ahead: int = 7) -> None:
    daily = df.groupby(df["data"].dt.date)["valor"].sum().reset_index()
    daily.columns = ["data", "valor"]
    daily["dia"] = np.arange(len(daily))

    if len(daily) < 3:
        st.warning("Dados insuficientes para previsão.")
        return

    model = LinearRegression()
    model.fit(daily[["dia"]], daily["valor"])

    future_days = np.arange(len(daily), len(daily) + days_ahead).reshape(-1, 1)
    forecast_values = model.predict(future_days)
    last_date = daily["data"].max()
    future_dates = pd.date_range(
        start=last_date + pd.Timedelta(days=1),
        periods=days_ahead,
        freq="D",
    )

    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(daily["data"], daily["valor"], label="Histórico", color="#2563eb")
    ax.plot(future_dates, forecast_values, label="Previsão (7 dias)", linestyle="--", color="#dc2626")
    ax.set_title("Previsão de receita (regressão linear)")
    ax.set_xlabel("Data (DD/MM/AAAA)")
    ax.set_ylabel("Valor (R$)")
    ax.legend()
    ax.grid(True, alpha=0.3)
    format_date_axis(ax)
    st.pyplot(fig)
    plt.close(fig)


def format_dataframe_dates(df: pd.DataFrame) -> pd.DataFrame:
    display = df.copy()
    display["data"] = display["data"].dt.strftime(DATE_FORMAT)
    return display


try:
    data = fetch_data()
except Exception as exc:
    st.error(f"Erro ao conectar ao MySQL: {exc}")
    st.info(
        "Configure o arquivo `.env` com as credenciais do banco. "
        "Use `.env.example` como referência."
    )
    st.stop()

if data.empty:
    st.warning("Nenhum registro de venda encontrado.")
    st.stop()

data_min = data["data"].min().date()
data_max = data["data"].max().date()

with st.sidebar:
    st.header("Filtros")

    st.subheader("Período")
    period = st.date_input(
        "Selecione o intervalo",
        value=(data_min, data_max),
        min_value=PERIOD_MIN,
        max_value=PERIOD_MAX,
        format=DATE_INPUT_FORMAT,
    )
    start, end = parse_period_selection(period, data_min, data_max)
    st.caption(f"De **{start.strftime(DATE_FORMAT)}** até **{end.strftime(DATE_FORMAT)}**")

    categories = []
    if "categoria" in data.columns:
        options = sorted(data["categoria"].dropna().unique())
        categories = st.multiselect("Categorias", options, default=options)

    products = []
    if "produto" in data.columns:
        options = sorted(data["produto"].dropna().unique())
        products = st.multiselect("Produtos", options)

    clients = []
    if "cliente" in data.columns:
        options = sorted(data["cliente"].dropna().unique())
        clients = st.multiselect("Clientes", options)

    if st.button("Atualizar dados"):
        st.cache_data.clear()
        st.rerun()

filtered = apply_filters(data, start, end, categories, products, clients)

if filtered.empty:
    st.warning("Nenhum dado para o período e filtros selecionados.")
    st.stop()

render_kpis(filtered)

tab_overview, tab_forecast, tab_data = st.tabs(["Visão geral", "Previsão", "Dados"])

with tab_overview:
    plot_sales_over_time(filtered)

    col_left, col_right = st.columns(2)
    with col_left:
        plot_top_products(filtered)
    with col_right:
        plot_category_share(filtered)

    plot_top_clients(filtered)

with tab_forecast:
    st.subheader("Previsão com scikit-learn")
    plot_forecast(filtered)

with tab_data:
    st.subheader("Registros filtrados")
    st.dataframe(
        format_dataframe_dates(filtered.sort_values("data", ascending=False)),
        use_container_width=True,
    )
