import streamlit as st
import pandas as pd
import requests
from io import BytesIO
import plotly.express as px
import pyodbc
import os
from dotenv import load_dotenv
from datetime import datetime

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

# Configuração do SQL Server (usando variáveis de ambiente)
server = os.getenv("SERVER")
database = os.getenv("DATABASE")
username = os.getenv("USERNAME")
password = os.getenv("PASSWORD")

# Função para buscar dados do JotForm via link direto para cadastro de esgoto
def get_jotform_data_esgoto():
    jotform_excel_url = "https://www.jotform.com/excel/250513248478056"  # Link para planilha de cadastro de esgoto
    try:
        response = requests.get(jotform_excel_url)
        if response.status_code == 200:
            excel_file = BytesIO(response.content)
            df = pd.read_excel(excel_file)
            return df
        else:
            st.error(f"Erro ao baixar o arquivo: {response.status_code}")
            return None
    except Exception as e:
        st.error(f"Erro ao carregar dados do JotForm: {e}")
        return None

# Função para buscar dados do JotForm via link direto para iniciativas
def get_jotform_data_ligacao():
    jotform_excel_url = "https://www.jotform.com/excel/250653960017051"  # Link para planilha de iniciativas
    try:
        response = requests.get(jotform_excel_url)
        if response.status_code == 200:
            excel_file = BytesIO(response.content)
            df = pd.read_excel(excel_file)
            return df
        else:
            st.error(f"Erro ao baixar o arquivo: {response.status_code}")
            return None
    except Exception as e:
        st.error(f"Erro ao carregar dados do JotForm: {e}")
        return None

# Função para buscar dados do SQL Server, tratando o caso quando não há filtro de data
@st.cache_data
def get_sql_data_totals(selected_date=None):
    try:
        # Se o filtro de data não foi selecionado, usa a data de hoje
        if selected_date is None:
            selected_date = datetime.today().date()

        conn = pyodbc.connect(
            f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}"
        )

        # Consultas SQL para totais e ocorrências
        query_totals = f"""
        SELECT 
            (SELECT COUNT(*) FROM [E_XLS_JOTFORM].[dbo].[TAB_GUARULHOS_III] WHERE CAST([XDATE] AS DATE) = '{selected_date}') AS TOTAL_CADASTRO,
            (SELECT COUNT(*) FROM [E_XLS_JOTFORM].[dbo].[TAB_GUARULHOS_III_CAIXA] WHERE CAST([XDATE] AS DATE) = '{selected_date}') AS TOTAL_CAIXA,
            (SELECT COUNT(*) FROM [E_XLS_JOTFORM].[dbo].[TAB_GUARULHOS_III_LIGAGUA] WHERE CAST([XDATE] AS DATE) = '{selected_date}') AS TOTAL_LIGACAO,
            (SELECT COUNT(*) FROM [E_XLS_JOTFORM].[dbo].[TAB_GUARULHOS_III]) AS TOTAL_GERAL_CADASTRO,
            (SELECT COUNT(*) FROM [E_XLS_JOTFORM].[dbo].[TAB_GUARULHOS_III_CAIXA]) AS TOTAL_GERAL_CAIXA,
            (SELECT COUNT(*) FROM [E_XLS_JOTFORM].[dbo].[TAB_GUARULHOS_III_LIGAGUA]) AS TOTAL_GERAL_LIGACAO
        """
        
        query_ocorrencias = f"""
        WITH Ocorrencias AS (
            SELECT [OCO_CAMPO], COUNT(*) AS TOTAL_OCORRENCIA
            FROM [E_XLS_JOTFORM].[dbo].[TAB_GUARULHOS_III]
            WHERE CAST([XDATE] AS DATE) = '{selected_date}'
            GROUP BY [OCO_CAMPO]
        )
        SELECT 
            O.OCO_CAMPO,
            O.TOTAL_OCORRENCIA,
            (SELECT COUNT(*) FROM [E_XLS_JOTFORM].[dbo].[TAB_GUARULHOS_III]
             WHERE CAST([XDATE] AS DATE) = '{selected_date}') AS TOTAL_REGISTROS_DIA
        FROM Ocorrencias O
        ORDER BY TOTAL_OCORRENCIA DESC
        """

        # Executar as consultas SQL
        totals_df = pd.read_sql(query_totals, conn)
        ocorrencias_df = pd.read_sql(query_ocorrencias, conn)
        
        conn.close()
        return totals_df, ocorrencias_df
    except Exception as e:
        st.error(f"Erro ao conectar ao banco de dados: {e}")
        return None, None

# Configuração da página
st.set_page_config(page_title="DASHBOARD GUARULHOS - VU III", layout="wide")

# Título
st.title("📊 DASHBOARD GUARULHOS - VU III")

# Painel Lateral com Filtros e Texto explicativo
with st.sidebar:
    st.header("Dash de Painel Lateral")
    
    # Texto explicativo
    st.write("Aqui você pode filtrar os dados por data e limpar o filtro caso necessário.")
    
    # Filtro de data
    selected_date = st.date_input("Selecione a data", datetime.today().date())
    
    # Botão para limpar o filtro
    clear_filter = st.button("Limpar Filtro", key="clear_filter")

    # Se o botão de limpar for pressionado, a data será redefinida para hoje
    if clear_filter:
        selected_date = datetime.today().date()

# Obter dados do JotForm e SQL Server
jotform_data_esgoto = get_jotform_data_esgoto()
jotform_data_ligacao = get_jotform_data_ligacao()
totals_data, ocorrencias_data = get_sql_data_totals(selected_date)

# Exibir os dados, se disponíveis
if totals_data is not None and ocorrencias_data is not None:
    if totals_data['TOTAL_CADASTRO'][0] == 0 and totals_data['TOTAL_CAIXA'][0] == 0 and totals_data['TOTAL_LIGACAO'][0] == 0:
        st.warning("📉 Não há dados para a data selecionada. Verifique o filtro.")
    else:
        col1, col2, col3 = st.columns(3)
        col1.metric("📋 Total de Cadastros", f"{totals_data['TOTAL_CADASTRO'][0]:,}".replace(",", "."))
        col2.metric("📦 Total Caixa UMA", f"{totals_data['TOTAL_CAIXA'][0]:,}".replace(",", "."))
        col3.metric("🔗 Total Ligações", f"{totals_data['TOTAL_LIGACAO'][0]:,}".replace(",", "."))

        st.subheader(f"📅 Total de Registros de Execução de Hoje: {ocorrencias_data['TOTAL_REGISTROS_DIA'][0]:,}".replace(",", "."))

        # Cards do Total Geral
        st.subheader("📊 Totais Gerais")
        col4, col5, col6 = st.columns(3)
        col4.metric("📋 Total Geral de Cadastros", f"{totals_data['TOTAL_GERAL_CADASTRO'][0]:,}".replace(",", "."))
        col5.metric("📦 Total Geral Caixa UMA", f"{totals_data['TOTAL_GERAL_CAIXA'][0]:,}".replace(",", "."))
        col6.metric("🔗 Total Geral Ligações", f"{totals_data['TOTAL_GERAL_LIGACAO'][0]:,}".replace(",", "."))

        # Gráfico de Ocorrências
        fig2 = px.bar(
            data_frame=ocorrencias_data,
            x="OCO_CAMPO",
            y="TOTAL_OCORRENCIA",
            title="🔴 Total de Ocorrências por Tipo",
            text_auto=True,
            color="TOTAL_OCORRENCIA",
            color_continuous_scale="viridis",
        )
        st.plotly_chart(fig2, use_container_width=True)

        # Tabela de Ocorrências
        st.subheader("📋 Tabela de Ocorrências")
        st.dataframe(ocorrencias_data[['OCO_CAMPO', 'TOTAL_OCORRENCIA']])

# Exibir dados do JotForm
if jotform_data_esgoto is not None:
    total_jotform_cadastros_esgoto = len(jotform_data_esgoto)
    st.subheader(f"📊 Total de Cadastros de Esgoto: {total_jotform_cadastros_esgoto:,}".replace(",", "."))

if jotform_data_ligacao is not None:
    total_jotform_cadastros_iniciativas = len(jotform_data_ligacao)
    st.subheader(f"📊 Total de Iniciativas: {total_jotform_cadastros_iniciativas:,}".replace(",", "."))

else:
    st.warning("⚠️ Não foi possível carregar os dados de JotForm ou SQL.")
