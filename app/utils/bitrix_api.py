import requests
import pandas as pd
import streamlit as st
import json
import os

# Detectar se estamos rodando no Streamlit Cloud
def is_streamlit_cloud():
    try:
        return os.environ.get('STREAMLIT_SHARING', '') != '' or os.environ.get('STREAMLIT_SERVER_URL', '').endswith('streamlit.app')
    except:
        return False

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

def setup_bitrix_connection(account_name, token, api_type="rest"):
    """
    Configura as informações de conexão com o Bitrix24
    
    Args:
        account_name (str): Nome da conta Bitrix24
        token (str): Token de acesso
        api_type (str): Tipo de API (rest ou biconnector)
        
    Returns:
        dict: Dicionário com as URLs configuradas
    """
    if api_type == "rest":
        base_url = f"https://{account_name}.bitrix24.com.br/rest/{token}"
        
        # Configurar URLs para diferentes endpoints da REST API
        urls = {
            "crm_deal": f"{base_url}/crm.deal.list",
            "crm_deal_fields": f"{base_url}/crm.deal.fields"
        }
    else:  # biconnector
        base_url = f"https://{account_name}.bitrix24.com.br/bitrix/tools/biconnector/pbi.php?token={token}"
        
        # Configurar URLs para diferentes tabelas do BI Connector
        urls = {
            "crm_deal": f"{base_url}&table=crm_deal",
            "crm_deal_uf": f"{base_url}&table=crm_deal_uf"
        }
    
    return urls

def save_connection_config(account_name, token, api_type="rest"):
    """
    Salva as configurações de conexão no session_state
    
    Args:
        account_name (str): Nome da conta Bitrix24
        token (str): Token de acesso
        api_type (str): Tipo de API (rest ou biconnector)
        
    Returns:
        bool: True se a configuração foi salva com sucesso
    """
    try:
        # Sempre salvar na sessão
        st.session_state.bitrix_config = {
            "account_name": account_name,
            "token": token,
            "api_type": api_type,
            "urls": setup_bitrix_connection(account_name, token, api_type)
        }
        
        # Apenas salvar em arquivo se não estiver no Streamlit Cloud
        if not is_streamlit_cloud():
            try:
                # Garantir que o diretório exista
                os.makedirs("app/data", exist_ok=True)
                
                with open("app/data/connection_config.json", "w") as f:
                    # Não salvar o token em texto puro - apenas salvar referências
                    config = {
                        "account_name": account_name,
                        "api_type": api_type
                        # Não salvar o token ou URLs que contenham o token
                    }
                    json.dump(config, f)
            except Exception as e:
                st.warning(f"Não foi possível salvar configuração em arquivo: {str(e)}")
                # Isso não é um problema crítico no Streamlit Cloud
        
        return True
    except Exception as e:
        st.error(f"Erro ao salvar configuração: {str(e)}")
        return False

def extract_biconnector_info(url):
    """
    Extrai informações de uma URL do BI Connector
    
    Args:
        url (str): URL do BI Connector
        
    Returns:
        tuple: (account_name, token) ou (None, None) se não for possível extrair
    """
    try:
        if "bitrix24.com.br/bitrix/tools/biconnector/pbi.php?token=" in url:
            account_name = url.split("https://")[1].split(".bitrix24.com.br")[0]
            token = url.split("token=")[1].split("&")[0] if "&" in url else url.split("token=")[1]
            return account_name, token
        return None, None
    except:
        return None, None

def extract_rest_info(url):
    """
    Extrai informações de uma URL REST webhook
    
    Args:
        url (str): URL do webhook REST
        
    Returns:
        tuple: (account_name, token) ou (None, None) se não for possível extrair
    """
    try:
        if "bitrix24.com.br/rest/" in url:
            parts = url.split("/rest/")
            if len(parts) == 2:
                account_name = parts[0].split("https://")[1].split(".bitrix24.com.br")[0]
                token = parts[1].rstrip("/")
                return account_name, token
        return None, None
    except:
        return None, None

def load_connection_config():
    """
    Carrega as configurações de conexão, preferindo secrets do Streamlit
    
    Returns:
        dict: Configuração de conexão ou None se não encontrada
    """
    # Tenta carregar dos secrets do Streamlit primeiro
    try:
        if "api" in st.secrets and "bitrix_webhook" in st.secrets["api"]:
            webhook_url = st.secrets["api"]["bitrix_webhook"]
            if webhook_url:
                # Primeiro tenta como BI Connector
                account_name, token = extract_biconnector_info(webhook_url)
                if account_name and token:
                    config = {
                        "account_name": account_name,
                        "token": token,
                        "api_type": "biconnector",
                        "urls": setup_bitrix_connection(account_name, token, "biconnector")
                    }
                    st.session_state.bitrix_config = config
                    return config
                
                # Se não for BI Connector, tenta como REST
                account_name, token = extract_rest_info(webhook_url)
                if account_name and token:
                    config = {
                        "account_name": account_name,
                        "token": token,
                        "api_type": "rest",
                        "urls": setup_bitrix_connection(account_name, token, "rest")
                    }
                    st.session_state.bitrix_config = config
                    return config
    except Exception as e:
        st.warning(f"Não foi possível carregar secrets: {str(e)}")
    
    # Se não encontrou nos secrets ou houve um erro, carrega do session_state
    if "bitrix_config" in st.session_state:
        return st.session_state.bitrix_config
    
    # Como último recurso, tenta carregar do arquivo (apenas em desenvolvimento)
    if not is_streamlit_cloud():
        try:
            # Verificar se o arquivo existe
            if os.path.exists("app/data/connection_config.json"):
                with open("app/data/connection_config.json", "r") as f:
                    stored_config = json.load(f)
                    # Se encontrou no arquivo mas não tem o token, precisa solicitar ao usuário
                    return stored_config
        except Exception as e:
            st.error(f"Erro ao carregar configuração local: {str(e)}")
    
    return None 