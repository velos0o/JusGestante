import requests
import pandas as pd
import streamlit as st
import json
import os

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
        st.session_state.bitrix_config = {
            "account_name": account_name,
            "token": token,
            "api_type": api_type,
            "urls": setup_bitrix_connection(account_name, token, api_type)
        }
        
        # Opcionalmente, salvar em arquivo para persistência (apenas para desenvolvimento)
        # Em produção, usar os secrets do Streamlit
        try:
            os.makedirs("app/data", exist_ok=True)
            with open("app/data/connection_config.json", "w") as f:
                # Não salvar o token em texto puro - apenas salvar referências
                config = {
                    "account_name": account_name,
                    "api_type": api_type
                    # Não salvar o token ou URLs que contenham o token
                }
                json.dump(config, f)
            return True
        except Exception as e:
            st.warning(f"Não foi possível salvar configuração: {str(e)}")
            return False
    except Exception as e:
        st.error(f"Erro ao salvar configuração: {str(e)}")
        return False

def load_connection_config():
    """
    Carrega as configurações de conexão, preferindo secrets do Streamlit
    
    Returns:
        dict: Configuração de conexão ou None se não encontrada
    """
    # Tenta carregar dos secrets do Streamlit primeiro
    try:
        if "api" in st.secrets and "bitrix_webhook" in st.secrets["api"]:
            # Configuração encontrada nos secrets
            config = {}
            if "banco_de_dados" in st.secrets:
                # Adicionar outras configurações relevantes
                pass
                
            # Configurar API do Bitrix
            webhook_url = st.secrets["api"]["bitrix_webhook"]
            if webhook_url:
                parts = webhook_url.split("/rest/")
                if len(parts) == 2:
                    account_name = parts[0].split("https://")[1].split(".bitrix24.com.br")[0]
                    token = parts[1].rstrip("/")
                    config = {
                        "account_name": account_name,
                        "token": token,
                        "api_type": "rest",
                        "urls": setup_bitrix_connection(account_name, token, "rest")
                    }
                    return config
    except Exception as e:
        st.warning(f"Não foi possível carregar secrets: {str(e)}")
    
    # Se não encontrou nos secrets ou houve um erro, carrega do session_state
    if "bitrix_config" in st.session_state:
        return st.session_state.bitrix_config
        
    # Como último recurso, tenta carregar do arquivo
    try:
        with open("app/data/connection_config.json", "r") as f:
            stored_config = json.load(f)
            
            # Se encontrou no arquivo mas não tem o token, precisa solicitar ao usuário
            return stored_config
    except:
        return None 