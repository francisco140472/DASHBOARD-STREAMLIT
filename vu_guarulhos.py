import streamlit as st
import pymssql
import pandas as pd
import plotly.express as px

# Configuração do SQL Server
server = '200.98.80.97'
database = 'E_XLS_JOTFORM'
username = 'sa'
password = 'SantoAndre2021'

def get_data():
    try:
        conn = pymssql.connect(server, username, password, database)
        query = """
        WITH Ocorrencias AS (
            SELECT [OCO_CAMPO], COUNT(*) AS TOTAL_OCORRENCIA
            FROM [E_XLS_JOTFORM].[dbo].[TAB_GUARULHOS_III]
            GROUP BY [OCO_CAMPO]
        )
        SELECT 
            (SELECT COUNT(*) FROM [E_XLS_JOTFORM].[dbo].[TAB_GUARULHOS_III]) AS TOTAL_CADASTRO,
            (SELECT COUNT(*) FROM [E_XLS_JOTFORM].[dbo].[TAB_GUARULHOS_III_CAIXA]) AS TOTAL_CAIXA,
            (SELECT COUNT(*) FROM [E_XLS_JOTFORM].[dbo].[TAB_GUARULHOS_III_LIGAGUA]) AS TOTAL_LIGACAO,
            O.OCO_CAMPO,
            O.TOTAL_OCORRENCIA
        FROM Ocorrencias O
        ORDER BY TOTAL_OCORRENCIA DESC
        """
        df = pd.read_sql(query, conn)
        conn.close()
        return df
    except Exception as e:
        st.error(f"Erro ao conectar ao banco de dados: {e}")
        return None

# Criando interface
st.set_page_config(page_title="Dashboard SQL Server", layout="wide")
st.title("Dashboard de Ocorrências")

data = get_data()
if data is not None:
    # Exibir métricas principais
    col1, col2, col3 = st.columns(3)
    col1.metric("Total de Cadastros", f"{data['TOTAL_CADASTRO'][0]:,}".replace(",", "."))
    col2.metric("Total Caixa UMA", f"{data['TOTAL_CAIXA'][0]:,}".replace(",", "."))
    col3.metric("Total Ligações", f"{data['TOTAL_LIGACAO'][0]:,}".replace(",", "."))
    
    # Criar gráfico de ocorrências
    fig = px.bar(data, x="OCO_CAMPO", y="TOTAL_OCORRENCIA", title="Ocorrências por Tipo", text_auto=True)
    st.plotly_chart(fig, use_container_width=True)
    
    # Exibir tabela de dados
    st.subheader("Tabela de Ocorrências")
    st.dataframe(data[['OCO_CAMPO', 'TOTAL_OCORRENCIA']])
else:
    st.warning("Não foi possível carregar os dados.")
