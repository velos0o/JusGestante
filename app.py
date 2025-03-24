import streamlit as st
import json
import os
import requests
from app.utils.bitrix_api import load_connection_config, save_connection_config, is_streamlit_cloud, extract_biconnector_info, extract_rest_info

# Configuração da página
st.set_page_config(
    page_title="JusGestante",
    page_icon="👩‍⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Título principal
st.title("JusGestante - Painel de Gestão")

# Garantir que o diretório de dados exista se não estiver no Streamlit Cloud
if not is_streamlit_cloud():
    os.makedirs("app/data", exist_ok=True)

# Verificar se há configuração de conexão
config = load_connection_config()

if not config:
    # Se não houver configuração, mostrar formulário
    st.write("### Configuração da Conexão com Bitrix24")
    st.write("Para usar este aplicativo, é necessário configurar a conexão com o Bitrix24.")
    
    # Verificar se há secrets configurados
    has_secrets = False
    webhook_url = ""
    webhook_type = "unknown"  # 'rest' ou 'biconnector'
    
    try:
        if "api" in st.secrets and "bitrix_webhook" in st.secrets["api"]:
            webhook_url = st.secrets["api"]["bitrix_webhook"]
            
            # Detectar o tipo de URL
            if "bitrix24.com.br/bitrix/tools/biconnector/pbi.php?token=" in webhook_url:
                webhook_type = "biconnector"
                has_secrets = True
            elif "bitrix24.com.br/rest/" in webhook_url:
                webhook_type = "rest"
                has_secrets = True
    except:
        pass
    
    if has_secrets:
        st.success(f"Secrets detectados! ({'BI Connector' if webhook_type == 'biconnector' else 'REST API'})")
        
        # Exibir informações sobre o webhook
        if webhook_type == "biconnector":
            account_name, token = extract_biconnector_info(webhook_url)
            if account_name and token:
                st.info(f"Conta Bitrix24: **{account_name}**")
        else:
            account_name, token = extract_rest_info(webhook_url)
            if account_name and token:
                st.info(f"Conta Bitrix24: **{account_name}**")
    
    # Adicionar seleção de tipo de API
    api_type = st.radio(
        "Tipo de API",
        ["REST API (Recomendado)", "BI Connector"],
        index=0 if webhook_type != "biconnector" else 1,
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
        # Extrair nome da conta e token do webhook, se disponível
        default_account_name = ""
        default_token = ""
        
        if webhook_url:
            if webhook_type == "biconnector":
                account_name, token = extract_biconnector_info(webhook_url)
                if account_name and token:
                    default_account_name = account_name
                    default_token = token
            else:
                account_name, token = extract_rest_info(webhook_url)
                if account_name and token:
                    default_account_name = account_name
                    default_token = token
        
        account_name = st.text_input("Nome da Conta Bitrix24", value=default_account_name)
        
        # Label adequado ao tipo de API
        token_label = "Token do Webhook" if api_type_value == "rest" else "Token do BI Connector"
        token = st.text_input(token_label, type="password", value=default_token)
        
        # Opção para usar secrets
        use_secrets = False
        if has_secrets:
            use_secrets = st.checkbox("Usar credenciais dos secrets", value=True, 
                                    help="Se marcado, usará as credenciais configuradas no servidor Streamlit")
        
        submitted = st.form_submit_button("Salvar Configuração")
        
        if submitted:
            if use_secrets and has_secrets:
                # Usar os valores dos secrets
                if webhook_type == "biconnector":
                    account_name, token = extract_biconnector_info(webhook_url)
                    api_type_value = "biconnector"
                else:
                    account_name, token = extract_rest_info(webhook_url)
                    api_type_value = "rest"
            
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
                            if response.text:
                                st.error(response.text[:200] + '...' if len(response.text) > 200 else response.text)
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
                # Para BI Connector, criar URL de teste
                token = config.get("token", "")
                test_url = f"https://{config['account_name']}.bitrix24.com.br/bitrix/tools/biconnector/pbi.php?token={token}&table=b_user"
                
            response = requests.get(test_url)
            if response.status_code == 200:
                st.success("Conexão testada com sucesso!")
                st.write("Resposta:")
                st.json(response.json() if response.text else {})
            else:
                st.error(f"Erro ao testar conexão (HTTP {response.status_code}).")
                if response.text:
                    st.error(response.text[:200] + '...' if len(response.text) > 200 else response.text)
        except Exception as e:
            st.error(f"Erro ao testar conexão: {str(e)}")
    
    # Opção para limpar configuração
    if st.sidebar.button("Limpar Configuração"):
        if "bitrix_config" in st.session_state:
            del st.session_state.bitrix_config
        
        # Apenas tentar remover o arquivo se não estiver no Streamlit Cloud
        if not is_streamlit_cloud():
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