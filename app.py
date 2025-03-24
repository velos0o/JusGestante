import streamlit as st
import json
import os
import requests
from app.utils.bitrix_api import load_connection_config, save_connection_config

# Configuração da página
st.set_page_config(
    page_title="JusGestante",
    page_icon="👩‍⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Título principal
st.title("JusGestante - Painel de Gestão")

# Verificar se há configuração de conexão
config = load_connection_config()

if not config:
    # Se não houver configuração, mostrar formulário
    st.write("### Configuração da Conexão com Bitrix24")
    st.write("Para usar este aplicativo, é necessário configurar a conexão com o Bitrix24.")
    
    # Adicionar seleção de tipo de API
    api_type = st.radio(
        "Tipo de API",
        ["REST API (Recomendado)", "BI Connector"],
        index=0,
        help="Selecione o tipo de API para conectar ao Bitrix24."
    )
    
    # Converter seleção para valor interno
    api_type_value = "rest" if api_type == "REST API (Recomendado)" else "biconnector"
    
    # Exibir informações específicas baseadas no tipo de API
    if api_type_value == "rest":
        st.info("""
        A REST API é a forma recomendada de conectar ao Bitrix24.
        Você precisa de um webhook token que pode ser criado em:
        
        **Configurações** > **Aplicativos** > **Outros** > **Webhooks**
        """)
    else:
        st.info("""
        O BI Connector é uma forma alternativa de conectar ao Bitrix24.
        Você precisa de um token do BI Connector que pode ser obtido em:
        
        **CRM** > **Análises** > **Conectores BI** > **Power BI**
        """)
    
    with st.form("setup_connection"):
        account_name = st.text_input("Nome da Conta Bitrix24", value="b24-lffzg9")
        
        # Label adequado ao tipo de API
        token_label = "Token do Webhook" if api_type_value == "rest" else "Token do BI Connector"
        
        # Usar valor padrão do secrets se disponível
        default_token = ""
        try:
            if api_type_value == "rest" and "api" in st.secrets and "bitrix_webhook" in st.secrets["api"]:
                webhook_url = st.secrets["api"]["bitrix_webhook"]
                if webhook_url:
                    parts = webhook_url.split("/rest/")
                    if len(parts) == 2:
                        default_token = parts[1].rstrip("/")
        except:
            pass
            
        token = st.text_input(token_label, type="password", value=default_token)
        
        submitted = st.form_submit_button("Salvar Configuração")
        
        if submitted:
            if account_name and token:
                if save_connection_config(account_name, token, api_type_value):
                    # Testar conexão antes de prosseguir
                    try:
                        test_url = ""
                        if api_type_value == "rest":
                            test_url = f"https://{account_name}.bitrix24.com.br/rest/{token}/profile"
                        else:
                            test_url = f"https://{account_name}.bitrix24.com.br/bitrix/tools/biconnector/pbi.php?token={token}&table=b_user"
                        
                        response = requests.get(test_url)
                        if response.status_code == 200:
                            st.success("Conexão testada com sucesso!")
                            st.success("Configuração salva!")
                            st.rerun()
                        else:
                            st.error(f"Erro ao testar conexão (HTTP {response.status_code}). Verifique suas credenciais.")
                            st.error(response.text)
                    except Exception as e:
                        st.error(f"Erro ao testar conexão: {str(e)}")
                        st.warning("Configuração salva, mas a conexão não pôde ser testada.")
                        st.rerun()
            else:
                st.error("Preencha todos os campos para salvar a configuração.")
else:
    # Descrição do aplicativo
    st.write("""
    ## Bem-vindo ao painel de gestão JusGestante!
    
    Este painel permite visualizar e gerenciar informações do Bitrix24.
    Utilize as opções do menu à esquerda para navegar entre os relatórios disponíveis.
    """)
    
    # Mostrar informações da conexão
    api_type = config.get("api_type", "rest")
    api_type_label = "REST API" if api_type == "rest" else "BI Connector"
    
    st.sidebar.write(f"**Conta conectada:** {config['account_name']}")
    st.sidebar.write(f"**Tipo de API:** {api_type_label}")
    
    # Opção para testar conexão
    if st.sidebar.button("Testar Conexão"):
        st.write("Testando conexão...")
        try:
            test_url = ""
            if api_type == "rest":
                # Usar token da configuração
                token = config.get("token", "")
                test_url = f"https://{config['account_name']}.bitrix24.com.br/rest/{token}/profile"
            else:
                # Para BI Connector, usar o URL já configurado com token
                test_url = config["urls"]["crm_deal"].split("&table=")[0] + "&table=b_user"
                
            response = requests.get(test_url)
            if response.status_code == 200:
                st.success("Conexão testada com sucesso!")
            else:
                st.error(f"Erro ao testar conexão (HTTP {response.status_code}).")
                st.error(response.text)
        except Exception as e:
            st.error(f"Erro ao testar conexão: {str(e)}")
    
    # Opção para limpar configuração
    if st.sidebar.button("Limpar Configuração"):
        if "bitrix_config" in st.session_state:
            del st.session_state.bitrix_config
        try:
            if os.path.exists("app/data/connection_config.json"):
                os.remove("app/data/connection_config.json")
        except:
            pass
        st.sidebar.success("Configuração removida!")
        st.rerun()

    # Mostrar gráficos ou estatísticas gerais
    st.write("### Estatísticas Gerais")
    
    # Aqui você pode adicionar widgets, gráficos e dados
    # que serão exibidos na página principal
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total de Leads", "250", "+12%")
    
    with col2:
        st.metric("Processos Ativos", "145", "-5%")
    
    with col3:
        st.metric("Conversão", "58%", "+2%") 