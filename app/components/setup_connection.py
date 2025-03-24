import streamlit as st
import sys
import os

# Adiciona o diretório principal ao path para importação
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from app.utils.bitrix_api import save_connection_config, load_connection_config

def show_connection_setup():
    """
    Exibe um formulário para configuração da conexão com o Bitrix24
    """
    st.header("Configuração da Conexão com Bitrix24")
    
    # Verificar se já existe configuração salva
    config = load_connection_config()
    
    with st.form("setup_connection"):
        if config and "account_name" in config:
            account_name = st.text_input("Nome da Conta Bitrix24", value=config["account_name"])
        else:
            account_name = st.text_input("Nome da Conta Bitrix24", placeholder="exemplo")
        
        token = st.text_input("Token do BI Connector", type="password", help="O token de acesso ao BI Connector do Bitrix24")
        
        submitted = st.form_submit_button("Salvar Configuração")
        
        if submitted:
            if account_name and token:
                save_connection_config(account_name, token)
                st.success("Configuração salva com sucesso!")
                st.rerun()
            else:
                st.error("Preencha todos os campos para salvar a configuração.") 