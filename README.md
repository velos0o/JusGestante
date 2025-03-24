# JusGestante - Painel de Gestão

Um aplicativo Streamlit para visualização e gerenciamento de informações do Bitrix24 para a empresa JusGestante.

## Funcionalidades

- Visualização de pendências e datas marcadas do Bitrix24
- Filtro por categoria (COMERCIAL ou TRÂMITES ADMINISTRATIVO)
- Filtro por estágio (PENDENTE DOCUMENTOS)
- Métricas e gráficos dos dados

## Instalação

1. Clone este repositório
2. Instale as dependências:

```bash
pip install -r requirements.txt
```

3. Execute o aplicativo:

```bash
streamlit run app.py
```

## Configuração

Na primeira execução, você precisará configurar a conexão com o Bitrix24:

1. Nome da conta Bitrix24 (ex: nome_da_sua_conta)
2. Token do BI Connector para acesso às APIs

## Estrutura do Projeto

```
JusGestante/
├── app/
│   ├── components/     # Componentes reutilizáveis da interface
│   ├── data/           # Arquivos de dados e configurações
│   ├── pages/          # Páginas do aplicativo
│   └── utils/          # Funções utilitárias
├── app.py              # Ponto de entrada principal
├── requirements.txt    # Dependências do projeto
└── README.md           # Documentação
```

## Expansão Futura

Este projeto foi estruturado para permitir fácil adição de novas funcionalidades e páginas no futuro. 