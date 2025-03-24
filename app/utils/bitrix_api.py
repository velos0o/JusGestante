import requests
import pandas as pd
import streamlit as st
import json

def get_bitrix_data(url):
    """
    Função para buscar dados da API do Bitrix24
    
    Args:
        url (str): URL completa para a API do Bitrix24
        
    Returns:
        pandas.DataFrame: DataFrame com os dados retornados pela API
    """
    try:
        # Fazer a requisição à API
        response = requests.get(url)
        
        # Verificar se a requisição foi bem-sucedida
        if response.status_code == 200:
            # Converter para DataFrame
            data = pd.DataFrame(response.json())
            return data
        else:
            st.error(f"Erro na requisição: {response.status_code}")
            return pd.DataFrame()
    except Exception as e:
        st.error(f"Erro ao conectar com o Bitrix24: {str(e)}")
        return pd.DataFrame()

def setup_bitrix_connection(account_name, token):
    """
    Configura as informações de conexão com o Bitrix24
    
    Args:
        account_name (str): Nome da conta Bitrix24
        token (str): Token de acesso ao BI Connector
        
    Returns:
        dict: Dicionário com as URLs configuradas
    """
    base_url = f"https://{account_name}.bitrix24.com.br/bitrix/tools/biconnector/pbi.php?token={token}"
    
    # Configurar URLs para diferentes tabelas
    urls = {
        "crm_deal": f"{base_url}&table=crm_deal",
        "crm_deal_uf": f"{base_url}&table=crm_deal_uf"
    }
    
    return urls

def save_connection_config(account_name, token):
    """
    Salva as configurações de conexão no session_state
    
    Args:
        account_name (str): Nome da conta Bitrix24
        token (str): Token de acesso ao BI Connector
    """
    st.session_state.bitrix_config = {
        "account_name": account_name,
        "token": token,
        "urls": setup_bitrix_connection(account_name, token)
    }
    
    # Opcionalmente, salvar em arquivo (cuidado com segurança)
    try:
        with open("app/data/connection_config.json", "w") as f:
            # Não salvar o token em texto puro - em produção, usar criptografia
            config = {
                "account_name": account_name,
                "urls": setup_bitrix_connection(account_name, token)
            }
            json.dump(config, f)
    except Exception as e:
        st.warning(f"Não foi possível salvar configuração: {str(e)}")

def load_connection_config():
    """
    Carrega as configurações de conexão do arquivo
    
    Returns:
        dict: Configuração de conexão ou None se não encontrada
    """
    try:
        with open("app/data/connection_config.json", "r") as f:
            return json.load(f)
    except:
        return None 