import streamlit as st
import json
import os
import requests

# Configuração da página
st.set_page_config(
    page_title="JusGestante",
    page_icon="👩‍⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Título principal
st.title("JusGestante - Painel de Gestão")

# Função para carregar configuração
def load_connection_config():
    try:
        with open("app/data/connection_config.json", "r") as f:
            return json.load(f)
    except:
        return None

# Função para salvar configuração
def save_connection_config(account_name, token, api_type="rest"):
    # Garantir que o diretório existe
    os.makedirs("app/data", exist_ok=True)
    
    config = {
        "account_name": account_name,
        "api_type": api_type,
        "urls": {}
    }
    
    # Configurar URLs baseado no tipo de API selecionada
    if api_type == "rest":
        # Usar a API REST do Bitrix24
        config["urls"] = {
            "crm_deal": f"https://{account_name}.bitrix24.com.br/rest/1/{token}/crm.deal.list.json",
            "crm_deal_uf": f"https://{account_name}.bitrix24.com.br/rest/1/{token}/crm.deal.userfield.list.json"
        }
    elif api_type == "biconnector":
        # Usar o BI Connector
        config["urls"] = {
            "crm_deal": f"https://{account_name}.bitrix24.com.br/bitrix/tools/biconnector/pbi.php?token={token}&table=crm_deal",
            "crm_deal_uf": f"https://{account_name}.bitrix24.com.br/bitrix/tools/biconnector/pbi.php?token={token}&table=crm_deal_uf"
        }
    
    # Salvar em arquivo
    try:
        with open("app/data/connection_config.json", "w") as f:
            json.dump(config, f, indent=2)
        return True
    except Exception as e:
        st.error(f"Erro ao salvar configuração: {str(e)}")
        return False

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
        token = st.text_input(token_label, type="password", value="y7x6ImLAAP8X2Xvwze3BnksPIIZ6iyyNbr")
        
        submitted = st.form_submit_button("Salvar Configuração")
        
        if submitted:
            if account_name and token:
                if save_connection_config(account_name, token, api_type_value):
                    # Testar conexão antes de prosseguir
                    try:
                        test_url = ""
                        if api_type_value == "rest":
                            test_url = f"https://{account_name}.bitrix24.com.br/rest/1/{token}/profile"
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
                # Extrair token do URL
                token = config["urls"]["crm_deal"].split("/rest/1/")[1].split("/")[0]
                test_url = f"https://{config['account_name']}.bitrix24.com.br/rest/1/{token}/profile"
            else:
                # Extrair token do URL
                token = config["urls"]["crm_deal"].split("token=")[1].split("&")[0]
                test_url = f"https://{config['account_name']}.bitrix24.com.br/bitrix/tools/biconnector/pbi.php?token={token}&table=b_user"
            
            response = requests.get(test_url)
            if response.status_code == 200:
                st.success("Conexão bem-sucedida!")
                st.write("Resposta:")
                st.json(response.json())
            else:
                st.error(f"Erro na conexão: {response.status_code}")
                st.write(f"Resposta: {response.text}")
        except Exception as e:
            st.error(f"Erro ao testar conexão: {str(e)}")
    
    # Opção para reconfigurar
    if st.sidebar.button("Reconfigurar Conexão"):
        if os.path.exists("app/data/connection_config.json"):
            os.remove("app/data/connection_config.json")
            st.rerun() 