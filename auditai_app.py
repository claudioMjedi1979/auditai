
import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import matplotlib.pyplot as plt

st.set_page_config(
    page_title="AuditAI - Dashboard",
    layout="wide",
    page_icon="📊"
)

# --- Logo e título ---
st.markdown(
    """
    <style>
        .main { background-color: #f5f7fa; }
        h1 { color: #1c3f5d; }
        .stButton>button {
            background-color: #1c3f5d;
            color: white;
        }
        .css-1aumxhk {
            background-color: #e4ebf5;
        }
    </style>
    <div style='display: flex; align-items: center;'>
        <img src='https://raw.githubusercontent.com/claudioMjedi1979/auditai-api/main/assets/logo_auditai.png' width='60' style='margin-right: 10px;'>
        <h1>AuditAI - Monitoramento de Compliance com IA</h1>
    </div>
    """,
    unsafe_allow_html=True
)

API_BASE_URL = "https://auditai-api.onrender.com"

@st.cache_data(show_spinner=False)
def carregar_dados(endpoint="/relatorio"):
    try:
        response = requests.get(API_BASE_URL + endpoint)
        if response.status_code == 200:
            return pd.DataFrame(response.json())
        else:
            st.error(f"Erro ao consultar API: {response.status_code}")
            return pd.DataFrame()
    except Exception as e:
        st.error(f"Erro de conexão: {str(e)}")
        return pd.DataFrame()

@st.cache_data(show_spinner=False)
def carregar_auditorias():
    try:
        response = requests.get(API_BASE_URL + "/auditoria")
        if response.status_code == 200:
            return response.json()["auditorias"]
        else:
            st.error(f"Erro ao consultar auditoria: {response.status_code}")
            return []
    except Exception as e:
        st.error(f"Erro de conexão: {str(e)}")
        return []

aba = st.sidebar.radio("Navegação", ["Relatório Completo", "Auditorias com Violações"])

if aba == "Relatório Completo":
    st.subheader("📝 Cadastrar Nova Transação")
    with st.form("form_transacao"):
        cliente = st.text_input("Cliente")
        valor_transacao = st.number_input("Valor da Transação (R$)", min_value=0.0, step=100.0)
        data = st.date_input("Data da Transação")
        hora = st.time_input("Hora")
        status = st.selectbox("Status", ["Pendente", "Aprovado", "Rejeitado"])
        justificativa = st.text_area("Justificativa (opcional)")

        enviado = st.form_submit_button("Salvar Transação")

        if enviado:
            payload = {
                "cliente": cliente,
                "valor_transacao": valor_transacao,
                "data": f"{data} {hora}",
                "status": status,
                "justificativa": justificativa
            }
            try:
                resposta = requests.post(f"{API_BASE_URL}/transacao", json=payload)
                if resposta.status_code == 200:
                    st.success("Transação registrada com sucesso!")
                else:
                    st.error(f"Erro: {resposta.json().get('detail', 'Erro ao registrar')}")
            except Exception as e:
                st.error(f"Erro de conexão: {str(e)}")

    st.divider()
    st.subheader("📤 Upload de Transações via CSV")
    arquivo_csv = st.file_uploader("📎 Escolha um arquivo CSV", type="csv")

    if arquivo_csv is not None:
        try:
            df_upload = pd.read_csv(arquivo_csv)
            inseridas, falhas = 0, 0
            if set(['cliente', 'valor_transacao', 'data', 'status', 'justificativa']).issubset(df_upload.columns):
                for _, row in df_upload.iterrows():
                    payload = {
                        "cliente": row['cliente'],
                        "valor_transacao": row['valor_transacao'],
                        "data": row['data'],
                        "status": row['status'],
                        "justificativa": row.get('justificativa', "")
                    }
                    try:
                        r = requests.post(f"{API_BASE_URL}/transacao", json=payload)
                        inseridas += r.status_code == 200
                        falhas += r.status_code != 200
                    except:
                        falhas += 1
                st.success(f"✅ {inseridas} transações importadas. ❌ {falhas} falharam.")
            else:
                st.error("CSV deve conter as colunas: cliente, valor_transacao, data, status, justificativa")
        except Exception as e:
            st.error(f"Erro ao processar o CSV: {str(e)}")

    st.subheader("📋 Todas as Transações")
    df = carregar_dados("/relatorio")
    if not df.empty:
        st.dataframe(df, use_container_width=True)
        st.download_button("⬇️ Baixar como CSV", df.to_csv(index=False), "relatorio_auditai.csv", "text/csv")

elif aba == "Auditorias com Violações":
    st.subheader("🔍 Transações com Violações de Compliance")
    dados = carregar_auditorias()
    if dados:
        for item in dados:
            with st.expander(f"Transação #{item['id']} - {item['cliente']}"):
                st.markdown(f"**Valor:** R$ {item['valor_transacao']:.2f}")
                st.markdown(f"**Data:** {item['data']}")
                st.markdown(f"**Status:** {item['status']}")
                st.markdown(f"**Justificativa:** {item['justificativa'] or 'Nenhuma'}")

                st.markdown("### 🛑 Violações Regulamentares")
                if "violacoes_compliance" in item and item["violacoes_compliance"]:
                    for violacao in item["violacoes_compliance"]:
                        st.warning(f"- **{violacao['descricao']}**")
                        st.markdown(f"  • Origem: {violacao['origem']}")
                        st.markdown(f"  • Ação: {violacao['acao_recomendada']}")
                        st.markdown(f"  • Base Legal: {violacao['base_legal']}")
                else:
                    st.success("Nenhuma violação encontrada.")
