
import streamlit as st
import pandas as pd
import requests
import plotly.express as px

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

aba = st.sidebar.radio("Navegação", [
    "📋 Transações",
    "🚨 Auditoria",
    "📝 Feedback",
    "🛡️ Riscos & Controles",
    "📈 Matriz de Riscos",
    "🕵️ Monitoramento",
    "📑 Relatórios"
])

# Transações
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

# Auditoria
elif aba == "🚨 Auditoria":
    st.subheader("🔍 Transações com Violações de Compliance")
    resposta = carregar("/auditoria")
    if isinstance(resposta, dict) and "auditorias" in resposta:
        for item in resposta["auditorias"]:
            with st.expander(f"Transação #{item['id']} - {item['cliente']}"):
                st.markdown(f"**Data:** {item['data']}")
                st.markdown(f"**Valor:** R$ {item['valor_transacao']:.2f}")
                st.markdown(f"**Status:** {item['status']}")
                st.markdown(f"**Justificativa:** {item['justificativa'] or 'Nenhuma'}")
                for v in item.get("violacoes_compliance", []):
                    st.warning(f"- {v['descricao']}")
                    st.markdown(f"  - Origem: {v['origem']}")
                    st.markdown(f"  - Ação: {v['acao_recomendada']}")
    else:
        st.warning("Nenhuma auditoria disponível.")

# Feedback
elif aba == "📝 Feedback":
    st.subheader("📝 Feedback de Auditoria")
    resposta = carregar("/auditoria")
    auditorias = resposta.get("auditorias", []) if isinstance(resposta, dict) else []
    for audit in auditorias:
        with st.expander(f"Transação #{audit['id']} - Cliente: {audit['cliente']}"):
            st.markdown(f"**Data:** {audit['data']}")
            st.markdown(f"**Valor:** R$ {audit['valor_transacao']:.2f}")
            st.markdown(f"**Status:** {audit['status']}")
            st.markdown(f"**Justificativa:** {audit['justificativa'] or 'Nenhuma'}")
            if audit.get("violacoes_compliance"):
                for v in audit["violacoes_compliance"]:
                    st.warning(f"- {v['descricao']}")
            rotulo = st.selectbox("Classificação", ["violacao_confirmada", "falso_positivo", "nao_avaliado"], key=f"r_{audit['id']}")
            observacao = st.text_input("Observação", key=f"o_{audit['id']}")
            if st.button("Enviar Feedback", key=f"btn_{audit['id']}"):
                payload = {"id_transacao": audit["id"], "rotulo": rotulo, "observacao": observacao}
                try:
                    r = requests.post(f"{API_BASE_URL}/rotular_transacao", json=payload)
                    if r.status_code == 200:
                        st.success("Feedback enviado.")
                    else:
                        st.error("Erro ao enviar feedback.")
                except Exception as e:
                    st.error(f"Erro de conexão: {str(e)}")


# Riscos & Controles
elif aba == "🛡️ Riscos & Controles":
    st.subheader("Cadastro de Riscos")
    with st.form("form_risco"):
        titulo = st.text_input("Título do risco")
        descricao = st.text_area("Descrição")
        categoria = st.selectbox("Categoria", ["Financeiro", "Operacional", "Legal", "Tecnologia"])
        probabilidade = st.selectbox("Probabilidade", ["Baixa", "Média", "Alta"])
        impacto = st.selectbox("Impacto", ["Baixo", "Médio", "Alto"])
        status = st.selectbox("Status", ["Aberto", "Mitigado", "Encerrado"])
        enviar = st.form_submit_button("Cadastrar Risco")
        if enviar:
            payload = {
                "titulo": titulo,
                "descricao": descricao,
                "categoria": categoria,
                "probabilidade": probabilidade,
                "impacto": impacto,
                "status": status
            }
            r = requests.post(f"{API_BASE_URL}/risco", json=payload)
            if r.status_code == 200:
                st.success("✅ Risco cadastrado com sucesso!")

    
    st.subheader("📤 Upload de Riscos via CSV")
    st.markdown("Envie um `.csv` com colunas: `titulo`, `descricao`, `categoria`, `probabilidade`, `impacto`, `status`")
    arquivo_risco = st.file_uploader("Escolha um arquivo CSV de riscos", type="csv", key="upload_riscos")

    if arquivo_risco:
        df_riscos = pd.read_csv(arquivo_risco)
        inseridos, erros = 0, 0
        for _, row in df_riscos.iterrows():
            payload = {
                "titulo": row["titulo"],
                "descricao": row["descricao"],
                "categoria": row["categoria"],
                "probabilidade": row["probabilidade"],
                "impacto": row["impacto"],
                "status": row["status"]
            }
            try:
                r = requests.post(f"{API_BASE_URL}/risco", json=payload)
                if r.status_code == 200:
                    inseridos += 1
                else:
                    erros += 1
            except:
                erros += 1
        st.success(f"{inseridos} riscos inseridos com sucesso. {erros} erros.")


    st.divider()
    st.subheader("Cadastro de Controles")
    riscos = carregar("/riscos")
    opcoes = {r["id"]: r["titulo"] for r in riscos} if isinstance(riscos, list) else {}
    if opcoes:
        with st.form("form_controle"):
            id_risco = st.selectbox("Risco Relacionado", list(opcoes.keys()), format_func=lambda x: opcoes[x])
            nome = st.text_input("Nome do controle")
            tipo = st.selectbox("Tipo", ["Preventivo", "Detectivo", "Corretivo"])
            descricao = st.text_area("Descrição")
            eficacia = st.selectbox("Eficácia", ["Alta", "Média", "Baixa"])
            responsavel = st.text_input("Responsável")
            enviar = st.form_submit_button("Cadastrar Controle")
            if enviar:
                payload = {
                    "id_risco": id_risco,
                    "nome": nome,
                    "tipo": tipo,
                    "descricao": descricao,
                    "eficacia": eficacia,
                    "responsavel": responsavel
                }
                r = requests.post(f"{API_BASE_URL}/controle", json=payload)
                if r.status_code == 200:
                    st.success("✅ Controle cadastrado!")
    

# Matriz de Riscos
elif aba == "📈 Matriz de Riscos":
    st.subheader("📈 Matriz de Riscos - ISO 31000")
    riscos = carregar("/riscos")
    if not riscos:
        st.info("Nenhum risco encontrado.")
    else:
        df = pd.DataFrame(riscos)
        prob_map = {"Baixa": 1, "Média": 2, "Alta": 3}
        imp_map = {"Baixo": 1, "Médio": 2, "Alto": 3}
        df["x_probabilidade"] = df["probabilidade"].map(prob_map)
        df["y_impacto"] = df["impacto"].map(imp_map)
        df["cor"] = df.apply(lambda r: "red" if r["x_probabilidade"] >= 3 and r["y_impacto"] >= 3
                             else "orange" if r["x_probabilidade"] >= 2 and r["y_impacto"] >= 2
                             else "green", axis=1)
        fig = px.scatter(df, x="x_probabilidade", y="y_impacto", text="titulo", color="cor",
                         color_discrete_map={"red": "red", "orange": "orange", "green": "green"},
                         labels={"x_probabilidade": "Probabilidade", "y_impacto": "Impacto"},
                         title="Mapa de Riscos (Probabilidade x Impacto)")
        fig.update_traces(marker=dict(size=15))
        fig.update_layout(xaxis=dict(dtick=1), yaxis=dict(dtick=1))
        st.plotly_chart(fig, use_container_width=True)

# Monitoramento
elif aba == "🕵️ Monitoramento":
    st.subheader("🕵️ Monitoramento Contínuo")
    st.markdown("🔧 Em breve: monitoramento de regras em tempo real e dashboard de alertas.")

# Relatórios
elif aba == "📑 Relatórios":
    st.subheader("📑 Relatórios de Conformidade")
    st.markdown("🔧 Em breve: geração de relatórios aderentes às normas ISO 31000 e 37301.")
