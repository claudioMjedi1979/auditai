import streamlit as st
import pandas as pd
import requests
import matplotlib.pyplot as plt

st.set_page_config(page_title="AuditAI - Dashboard", layout="wide")

st.title("📊 AuditAI - Monitoramento de Compliance com IA")

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

@st.cache_data(show_spinner=False)
def carregar_feedbacks():
    try:
        response = requests.get(f"{API_BASE_URL}/feedbacks")
        if response.status_code == 200:
            return pd.DataFrame(response.json()["feedbacks"])
        else:
            st.error("Erro ao carregar feedbacks")
            return pd.DataFrame()
    except Exception as e:
        st.error(f"Erro ao conectar com a API: {e}")
        return pd.DataFrame()

aba = st.sidebar.radio("Navegação", ["Relatório Completo", "Auditorias com Violações", "📊 Relatório de Auditoria Manual"])

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

elif aba == "📊 Relatório de Auditoria Manual":
    st.subheader("📋 Rótulos Aplicados por Cliente e Mês")
    df_fb = carregar_feedbacks()

    if not df_fb.empty:
        df_fb["data_registro"] = pd.to_datetime(df_fb["data_registro"])
        df_fb["mes"] = df_fb["data_registro"].dt.to_period("M").astype(str)

        st.write("### Tabela de Feedbacks Registrados")
        st.dataframe(df_fb[["id_transacao", "cliente", "rotulo", "observacao", "data_registro"]], use_container_width=True)

        st.markdown("---")
        st.write("### Gráfico de Rótulos por Cliente")
        resumo = df_fb.groupby(["cliente", "rotulo"]).size().unstack(fill_value=0)
        fig, ax = plt.subplots(figsize=(10, 5))
        resumo.plot(kind="bar", stacked=True, ax=ax)
        ax.set_ylabel("Total de Feedbacks")
        ax.set_xlabel("Cliente")
        ax.set_title("Feedbacks por Cliente e Tipo de Rótulo")
        st.pyplot(fig)

        st.markdown("---")
        st.write("### Rótulos por Mês")
        resumo_mes = df_fb.groupby(["mes", "rotulo"]).size().unstack(fill_value=0)
        fig2, ax2 = plt.subplots(figsize=(10, 4))
        resumo_mes.plot(kind="bar", ax=ax2)
        ax2.set_title("Distribuição de Rótulos por Mês")
        st.pyplot(fig2)

    else:
        st.info("Nenhum feedback registrado ainda.")
