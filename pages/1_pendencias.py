import streamlit as st
import pandas as pd
import numpy as np
import requests
import json
import os
import traceback
from datetime import datetime

# Título da página
st.title("Pendências")
st.write("Visualização de pendências e datas marcadas do Bitrix24")

# Função para carregar configuração
def load_connection_config():
    try:
        with open("app/data/connection_config.json", "r") as f:
            return json.load(f)
    except Exception as e:
        st.error(f"Erro ao carregar configuração: {str(e)}")
        return None

# Função para obter dados do Bitrix
def get_bitrix_data(url):
    try:
        # Exibir URL para diagnóstico quando depuração estiver ativada
        if st.session_state.get('debug_mode', False):
            st.write(f"Requisitando URL: {url}")

        # Fazer a requisição
        response = requests.get(url)
        
        # Exibir informações de resposta para diagnóstico
        if st.session_state.get('debug_mode', False):
            st.write(f"Status code: {response.status_code}")
            
        if response.status_code == 200:
            try:
                # Para diagnóstico, mostrar os primeiros caracteres da resposta
                if st.session_state.get('debug_mode', False):
                    st.write("Primeiros 500 caracteres da resposta:")
                    st.code(response.text[:500])
                
                # Tentar processar como JSON
                data = response.json()
                
                # Se não for uma lista ou for uma resposta de erro
                if not isinstance(data, list) or (isinstance(data, dict) and "error" in data):
                    if st.session_state.get('debug_mode', False):
                        st.error("Formato de resposta inválido ou erro")
                        st.json(data)
                    return None
                
                # A primeira linha contém os nomes das colunas
                if len(data) > 0:
                    columns = data[0]
                    rows = data[1:]
                    
                    # Criar um dicionário de dados para o DataFrame
                    df_data = {col: [] for col in columns}
                    
                    # Preencher o dicionário com os dados das linhas
                    for row in rows:
                        for i, col in enumerate(columns):
                            if i < len(row):
                                df_data[col].append(row[i])
                            else:
                                df_data[col].append("")
                    
                    # Criar o DataFrame
                    df = pd.DataFrame(df_data)
                    
                    # Mostrar detalhes para diagnóstico
                    if st.session_state.get('debug_mode', False):
                        st.write(f"DataFrame criado com {len(df)} linhas e {len(columns)} colunas")
                        
                    return df
                else:
                    return pd.DataFrame()
            except Exception as e:
                st.error(f"Erro ao processar resposta: {str(e)}")
                st.error(traceback.format_exc())
                return None
        else:
            st.error(f"Erro na requisição: {response.status_code}")
            return None
    except Exception as e:
        st.error(f"Erro ao conectar com o Bitrix24: {str(e)}")
        st.error(traceback.format_exc())
        return None

# Função para gerar dados simulados
def generate_simulated_data(num_rows=100):
    df = pd.DataFrame({
        'ID': [str(i) for i in range(1, num_rows + 1)],
        'TITLE': [f"Negócio {i}" for i in range(1, num_rows + 1)],
        'CATEGORY_ID': [str(x) for x in np.random.choice([0, 2], size=num_rows)],
        'STAGE_ID': np.random.choice(['C2:PREPARATION', 'C2:NEW', 'C0:NEW'], size=num_rows),
        'UF_CRM_PENDENCIAS': np.random.choice(["", "Pendência documento", "Pendência pagamento", "Pendência contrato", "Pendência assinatura"], size=num_rows, p=[0.5, 0.15, 0.15, 0.1, 0.1]),
        'UF_CRM_DATA_MARCADA': np.random.choice(["", "2023-05-10 10:00", "2023-05-15 14:30", "2023-05-20 09:15"], size=num_rows, p=[0.7, 0.1, 0.1, 0.1])
    })
    return df

# Carregar configuração
config = load_connection_config()

# Inicializar variáveis de depuração
debug_mode = False  # Desativar depuração por padrão
st.session_state['debug_mode'] = debug_mode

# Opção para mostrar detalhes de depuração (escondida no final da sidebar)
with st.sidebar:
    st.sidebar.markdown("---")
    debug_mode = st.checkbox("Mostrar informações de depuração", value=False)
    st.session_state['debug_mode'] = debug_mode
    use_simulated_data = st.checkbox("Usar dados simulados", value=False)

if not config:
    st.error("Configuração não encontrada. Configure a conexão na página principal.")
    # Mostrar dados simulados mesmo sem configuração
    data = generate_simulated_data(50)
    st.info("Exibindo dados simulados para visualização")
    is_simulated = True
else:
    # Carregar os dados
    if use_simulated_data:
        data = generate_simulated_data(100)
        is_simulated = True
    else:
        try:
            with st.spinner("Carregando dados do Bitrix24..."):
                # Carregar dados do CRM Deal
                crm_deal_url = config["urls"]["crm_deal"]
                data = get_bitrix_data(crm_deal_url)
                
                if data is None or data.empty:
                    st.error("Não foi possível obter dados do CRM Deal")
                    data = generate_simulated_data(50)
                    is_simulated = True
                else:
                    is_simulated = False
                    
                    # Adicionar colunas simuladas para pendências e data marcada
                    if not 'UF_CRM_PENDENCIAS' in data.columns:
                        data['UF_CRM_PENDENCIAS'] = ""
                        if debug_mode:
                            st.warning("A coluna UF_CRM_PENDENCIAS não está disponível nos dados. Usando coluna vazia.")
                    
                    if not 'UF_CRM_DATA_MARCADA' in data.columns:
                        data['UF_CRM_DATA_MARCADA'] = ""
                        if debug_mode:
                            st.warning("A coluna UF_CRM_DATA_MARCADA não está disponível nos dados. Usando coluna vazia.")
        except Exception as e:
            if debug_mode:
                st.error(f"Erro ao carregar dados: {str(e)}")
                st.error(traceback.format_exc())
            data = generate_simulated_data(50)
            is_simulated = True

# Verificar se data existe e não está vazio
if data is not None and not data.empty:
    # FILTRO DE FUNIL (CATEGORY_ID)
    st.write("### Filtro de Funil")
    
    # Configurar colunas para filtros
    filter_col1, filter_col2 = st.columns(2)
    
    with filter_col1:
        # Filtro de categoria
        category_options = ["Todos"]
        if 'CATEGORY_ID' in data.columns:
            category_values = data['CATEGORY_ID'].dropna().unique()
            category_options.extend(sorted([str(v) for v in category_values if pd.notna(v) and str(v).strip() != ""]))
        
        selected_category = st.selectbox(
            "Categoria",
            options=category_options,
            format_func=lambda x: "COMERCIAL" if x == "0" else "TRÂMITES ADMINISTRATIVO" if x == "2" else str(x)
        )
    
    with filter_col2:
        # Filtro de estágio
        if selected_category == "2" and 'STAGE_ID' in data.columns:
            stage_options = ["Todos"]
            
            # Filtrar por categoria
            data_cat = data[data['CATEGORY_ID'].astype(str) == "2"]
            stage_values = data_cat['STAGE_ID'].dropna().unique()
            stage_options.extend(sorted([str(v) for v in stage_values if pd.notna(v) and str(v).strip() != ""]))
            
            selected_stage = st.selectbox(
                "Estágio",
                options=stage_options,
                format_func=lambda x: "PENDENTE DOCUMENTOS" if x == "C2:PREPARATION" else str(x)
            )
        else:
            selected_stage = "Todos"
    
    # Aplicar filtros
    filtered_data = data.copy()
    
    if selected_category != "Todos" and 'CATEGORY_ID' in filtered_data.columns:
        # Converter para string para comparação
        filtered_data['CATEGORY_ID'] = filtered_data['CATEGORY_ID'].astype(str)
        filtered_data = filtered_data[filtered_data['CATEGORY_ID'] == selected_category]
    
    if selected_stage != "Todos" and selected_category == "2" and 'STAGE_ID' in filtered_data.columns:
        filtered_data = filtered_data[filtered_data['STAGE_ID'] == selected_stage]
    
    # Exibir contagem total de pendências
    st.markdown("---")
    
    # Indicador grande de total de pendências
    pendencias_count = 0
    if 'UF_CRM_PENDENCIAS' in filtered_data.columns:
        pendencias_count = filtered_data['UF_CRM_PENDENCIAS'].astype(str).apply(lambda x: x.strip() != "").sum()
    
    st.metric("Total de Pendências", pendencias_count)
    
    # Exibir tipos de pendências
    st.markdown("---")
    st.write("### Tipos de Pendências")
    
    if 'UF_CRM_PENDENCIAS' in filtered_data.columns:
        # Obter tipos únicos de pendências
        tipos_pendencias = filtered_data[filtered_data['UF_CRM_PENDENCIAS'].astype(str).apply(lambda x: x.strip() != "")]['UF_CRM_PENDENCIAS'].value_counts()
        
        if not tipos_pendencias.empty:
            # Criar dataframe para exibição
            tipos_df = pd.DataFrame({
                'Tipo de Pendência': tipos_pendencias.index,
                'Quantidade': tipos_pendencias.values
            })
            st.dataframe(tipos_df, use_container_width=True)
        else:
            st.info("Não foram encontradas pendências.")
    
    # Tabela simplificada de pendências
    st.markdown("---")
    st.write("### Pendências Detalhadas")
    
    # Filtrar apenas registros com pendências
    pendencias_df = filtered_data[filtered_data['UF_CRM_PENDENCIAS'].astype(str).apply(lambda x: x.strip() != "")].copy()
    
    if not pendencias_df.empty:
        # Selecionar apenas as colunas ID, Pendência e Data Marcada
        display_cols = []
        
        # Adicionar coluna ID (pode ser TITLE se ID não existir)
        if 'ID' in pendencias_df.columns:
            display_cols.append('ID')
        elif 'TITLE' in pendencias_df.columns:
            display_cols.append('TITLE')
        
        # Adicionar nome da etapa, se disponível
        if 'STAGE_ID' in pendencias_df.columns:
            display_cols.append('STAGE_ID')
            
        # Adicionar colunas de pendências
        if 'UF_CRM_PENDENCIAS' in pendencias_df.columns:
            display_cols.append('UF_CRM_PENDENCIAS')
        if 'UF_CRM_DATA_MARCADA' in pendencias_df.columns:
            display_cols.append('UF_CRM_DATA_MARCADA')
            
        # Renomear colunas para melhor legibilidade
        pendencias_display = pendencias_df[display_cols].copy()
        column_names = {
            'ID': 'ID',
            'TITLE': 'Título',
            'STAGE_ID': 'Etapa',
            'UF_CRM_PENDENCIAS': 'Pendência',
            'UF_CRM_DATA_MARCADA': 'Hora Marcada'
        }
        pendencias_display = pendencias_display.rename(columns={col: column_names.get(col, col) for col in display_cols})
        
        # Exibir a tabela com as pendências
        st.dataframe(pendencias_display, use_container_width=True)
    else:
        st.info("Não foram encontradas pendências nesta seleção.")
        
    # Mostrar aviso se estiver usando dados simulados
    if is_simulated:
        st.sidebar.warning("⚠️ Os dados exibidos são simulados e não refletem informações reais do Bitrix24")
        
else:
    st.warning("Não foi possível carregar dados. Verifique a conexão com o Bitrix24.")
    
    # Adicionar um botão para reconfiguração rápida
    if st.button("Ir para configuração"):
        if os.path.exists("app/data/connection_config.json"):
            os.remove("app/data/connection_config.json")
            st.rerun() 