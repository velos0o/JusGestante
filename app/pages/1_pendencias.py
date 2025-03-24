import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import sys
import os

# Adiciona o diretório principal ao path para importação
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from app.utils.bitrix_api import get_bitrix_data, load_connection_config
from app.components.metrics import MetricsDisplay

# Configuração da página
st.set_page_config(
    page_title="JusGestante - Pendências",
    page_icon="📋",
    layout="wide",
)

# Título da página
st.title("Pendências")
st.write("Visualização de pendências e datas marcadas do Bitrix24")

# Função para carregar os dados
@st.cache_data(ttl=3600)  # Cache por 1 hora
def load_data():
    try:
        # Verifica se há configuração de conexão
        config = load_connection_config()
        
        if not config or "urls" not in config:
            st.error("Configuração de conexão não encontrada. Configure a conexão na página principal.")
            return pd.DataFrame()
        
        # Carrega os dados do CRM Deal
        crm_deal_url = config["urls"]["crm_deal"]
        crm_deal_data = get_bitrix_data(crm_deal_url)
        
        # Carrega os dados do CRM Deal UF
        crm_deal_uf_url = config["urls"]["crm_deal_uf"]
        crm_deal_uf_data = get_bitrix_data(crm_deal_uf_url)
        
        # Filtra apenas os campos necessários do CRM Deal UF
        crm_deal_uf_filtered = crm_deal_uf_data[['DEAL_ID', 'UF_CRM_PENDENCIAS', 'UF_CRM_DATA_MARCADA']]
        
        # Merge dos dados com base no ID e DEAL_ID
        merged_data = pd.merge(
            crm_deal_data, 
            crm_deal_uf_filtered,
            left_on='ID',
            right_on='DEAL_ID',
            how='inner'
        )
        
        return merged_data
    except Exception as e:
        st.error(f"Erro ao carregar dados: {str(e)}")
        return pd.DataFrame()

# Carregar os dados
data = load_data()

if not data.empty:
    # Sidebar com filtros
    st.sidebar.header("Filtros")
    
    # Filtro de categoria
    category_options = ["Todos"]
    if 'CATEGORY_ID' in data.columns:
        category_options.extend(data['CATEGORY_ID'].unique().tolist())
    
    selected_category = st.sidebar.selectbox(
        "Categoria",
        options=category_options,
        format_func=lambda x: "COMERCIAL" if x == 0 else "TRÂMITES ADMINISTRATIVO" if x == 2 else str(x)
    )
    
    # Filtro de estágio para Category_id = 2
    if selected_category == 2:
        stage_options = ["Todos"]
        if 'STAGE_ID' in data.columns:
            stage_options.extend(data[data['CATEGORY_ID'] == 2]['STAGE_ID'].unique().tolist())
        
        selected_stage = st.sidebar.selectbox(
            "Estágio",
            options=stage_options,
            format_func=lambda x: "PENDENTE DOCUMENTOS" if x == "C2:PREPARATION" else str(x)
        )
    else:
        selected_stage = "Todos"
    
    # Aplicar filtros
    filtered_data = data.copy()
    
    if selected_category != "Todos":
        filtered_data = filtered_data[filtered_data['CATEGORY_ID'] == selected_category]
    
    if selected_stage != "Todos" and selected_category == 2:
        filtered_data = filtered_data[filtered_data['STAGE_ID'] == selected_stage]
    
    # Exibir métricas usando o componente
    st.header("Métricas")
    MetricsDisplay.pendencias_metrics(filtered_data, 'UF_CRM_PENDENCIAS', 'UF_CRM_DATA_MARCADA')
    
    # Exibir dados filtrados
    st.header("Dados Filtrados")
    
    # Selecionar colunas para exibição
    columns_to_show = ['ID', 'TITLE', 'CATEGORY_ID', 'STAGE_ID', 'UF_CRM_PENDENCIAS', 'UF_CRM_DATA_MARCADA']
    columns_to_show = [col for col in columns_to_show if col in filtered_data.columns]
    
    st.dataframe(filtered_data[columns_to_show], use_container_width=True)
    
    # Gráficos
    st.header("Gráficos")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Distribuição por Categoria")
        if 'CATEGORY_ID' in filtered_data.columns:
            category_counts = filtered_data['CATEGORY_ID'].value_counts().reset_index()
            category_counts.columns = ['Categoria', 'Quantidade']
            # Mapear os valores de categoria para nomes legíveis
            category_counts['Categoria'] = category_counts['Categoria'].map({
                0: "COMERCIAL", 
                2: "TRÂMITES ADMINISTRATIVO"
            })
            st.bar_chart(category_counts.set_index('Categoria'))
    
    with col2:
        st.subheader("Distribuição por Status de Pendência")
        pendencias_status = pd.DataFrame({
            'Status': ['Com Pendências', 'Sem Pendências'],
            'Quantidade': [
                filtered_data['UF_CRM_PENDENCIAS'].notna().sum(),
                filtered_data['UF_CRM_PENDENCIAS'].isna().sum()
            ]
        })
        st.bar_chart(pendencias_status.set_index('Status'))
else:
    st.warning("Não foi possível carregar os dados. Verifique a conexão com o Bitrix24.") 