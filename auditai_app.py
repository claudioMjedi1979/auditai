import streamlit as st
import pandas as pd
import requests

st.set_page_config(page_title="AuditAI - Dashboard", layout="wide")

st.title("📊 AuditAI - Monitoramento de Compliance com IA")

# --- Funções ---
API_BASE_URL = "http://localhost:8000"

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

# --- Menu de navegação ---
aba = st.sidebar.radio("Navegação", ["Relatório Completo", "Auditorias com Violações"])

# --- Tela: Relatório Completo com formulário e upload ---
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
    st.markdown("""
    Envie um arquivo `.csv` com os seguintes campos:

    - `cliente` (texto)
    - `valor_transacao` (número)
    - `data` (formato: `YYYY-MM-DD HH:MM:SS`)
    - `status` (Pendente, Aprovado, Rejeitado)
    - `justificativa` (opcional)

    **Exemplo de linha válida:**

    ```
    Empresa A,15000.0,2025-03-25 10:30:00,Pendente,Aguardando documentos
    ```
    """)

    arquivo_csv = st.file_uploader("📎 Escolha um arquivo CSV", type="csv")

    if arquivo_csv is not None:
        try:
            df_upload = pd.read_csv(arquivo_csv)
            inseridas = 0
            falhas = 0
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
                        if r.status_code == 200:
                            inseridas += 1
                        else:
                            falhas += 1
                    except:
                        falhas += 1
                st.success(f"✅ {inseridas} transações importadas com sucesso. ❌ {falhas} falharam.")
            else:
                st.error("❌ O CSV deve conter as colunas: cliente, valor_transacao, data, status, justificativa")
        except Exception as e:
            st.error(f"Erro ao processar o CSV: {str(e)}")

    st.subheader("📋 Todas as Transações")
    df = carregar_dados("/relatorio")
    if not df.empty:
        st.dataframe(df, use_container_width=True)
        st.download_button("⬇️ Baixar como CSV", df.to_csv(index=False), "relatorio_auditai.csv", "text/csv")

# --- Tela: Auditorias com Violações ---
elif aba == "Auditorias com Violações":
    st.subheader("🔍 Transações com Violações e Anomalias")
    df = carregar_dados("/auditoria")
    if "violacoes" in df.columns:
        st.dataframe(df, use_container_width=True)
    elif "violacoes" in df:
        df_violacoes = pd.DataFrame(df["violacoes"])
        st.dataframe(df_violacoes, use_container_width=True)
        st.download_button("⬇️ Baixar Violações", df_violacoes.to_csv(index=False), "violacoes_auditai.csv", "text/csv")
    else:
        st.warning("Nenhuma violação encontrada.")