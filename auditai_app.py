
import streamlit as st
import pandas as pd
import requests

API_BASE_URL = "https://auditai-api.onrender.com"
st.set_page_config(page_title="AuditAI", layout="wide")

st.title("📊 AuditAI - Sistema de Auditoria com IA")

@st.cache_data(show_spinner=False)
def carregar(endpoint):
    try:
        r = requests.get(f"{API_BASE_URL}{endpoint}")
        if r.status_code == 200:
            return r.json()
        else:
            st.error(f"Erro ao consultar {endpoint}: {r.status_code}")
            return {}
    except Exception as e:
        st.error(f"Erro de conexão: {str(e)}")
        return {}

aba = st.sidebar.radio("Navegação", ["📋 Transações", "🚨 Auditoria", "📝 Feedback"])

if aba == "📋 Transações":
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
                r = requests.post(f"{API_BASE_URL}/transacao", json=payload)
                if r.status_code == 200:
                    st.success("Transação registrada com sucesso!")
                else:
                    st.error(f"Erro: {r.json().get('detail')}")
            except Exception as e:
                st.error(f"Erro de conexão: {str(e)}")

    st.subheader("📤 Upload de Transações via CSV")
    st.markdown("Envie um `.csv` com colunas: `cliente`, `valor_transacao`, `data`, `status`, `justificativa`")
    arquivo = st.file_uploader("Escolha um arquivo", type="csv")
    if arquivo:
        df = pd.read_csv(arquivo)
        inseridas, falhas = 0, 0
        for _, row in df.iterrows():
            payload = {
                "cliente": row["cliente"],
                "valor_transacao": row["valor_transacao"],
                "data": row["data"],
                "status": row["status"],
                "justificativa": row.get("justificativa", "")
            }
            try:
                r = requests.post(f"{API_BASE_URL}/transacao", json=payload)
                if r.status_code == 200:
                    inseridas += 1
                else:
                    falhas += 1
            except:
                falhas += 1
        st.success(f"{inseridas} transações inseridas, {falhas} com erro.")

    st.subheader("📊 Relatório Completo")
    dados = carregar("/relatorio")
    if dados:
        df = pd.DataFrame(dados)
        st.dataframe(df, use_container_width=True)
        st.download_button("⬇️ Baixar como CSV", df.to_csv(index=False), "relatorio_auditai.csv", "text/csv")

elif aba == "🚨 Auditoria":
    st.subheader("🔍 Transações com Violações de Compliance")
    dados = carregar("/auditoria").get("auditorias", [])
    if dados:
        for item in dados:
            with st.expander(f"Transação #{item['id']} - {item['cliente']}"):
                st.markdown(f"**Data:** {item['data']}")
                st.markdown(f"**Valor:** R$ {item['valor_transacao']:.2f}")
                st.markdown(f"**Status:** {item['status']}")
                st.markdown(f"**Justificativa:** {item['justificativa'] or 'Nenhuma'}")
                st.markdown("### 🛑 Violações")
                for v in item.get("violacoes_compliance", []):
                    st.warning(f"- {v['descricao']}")
                    st.markdown(f"  • Origem: {v['origem']}  \n  • Ação: {v['acao_recomendada']}")

elif aba == "📝 Feedback":
    st.subheader("📝 Feedback de Auditoria")
    dados = carregar("/auditoria").get("auditorias", [])
    if not dados:
        st.warning("Nenhuma auditoria carregada.")
    for audit in dados:
        with st.expander(f"Transação #{audit['id']} - Cliente: {audit['cliente']}"):
            st.markdown(f"**Data:** {audit['data']}")
            st.markdown(f"**Valor:** R$ {audit['valor_transacao']:.2f}")
            st.markdown(f"**Status:** {audit['status']}")
            st.markdown(f"**Justificativa:** {audit['justificativa'] or 'Nenhuma'}")

            if audit["violacoes_compliance"]:
                st.markdown("### Violações:")
                for violacao in audit["violacoes_compliance"]:
                    st.warning(f"- {violacao['descricao']}")
                    st.markdown(f"  • Origem: {violacao['origem']}  \n  • Ação: {violacao['acao_recomendada']}")

            st.markdown("### 📌 Enviar Feedback")
            col1, col2 = st.columns(2)
            with col1:
                rotulo = st.selectbox("Classificação", ["violacao_confirmada", "falso_positivo", "nao_avaliado"], key=f"rotulo_{audit['id']}")
            with col2:
                obs = st.text_input("Observação", key=f"obs_{audit['id']}")
            if st.button("Enviar Feedback", key=f"btn_{audit['id']}"):
                payload = {
                    "id_transacao": audit["id"],
                    "rotulo": rotulo,
                    "observacao": obs
                }
                try:
                    r = requests.post(f"{API_BASE_URL}/rotular_transacao", json=payload)
                    if r.status_code == 200:
                        st.success("Feedback enviado com sucesso!")
                    else:
                        st.error(f"Erro ao enviar: {r.text}")
                except Exception as e:
                    st.error(f"Erro de conexão: {str(e)}")
