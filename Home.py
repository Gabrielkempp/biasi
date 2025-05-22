import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import locale

# Configuração da página
st.set_page_config(
    page_title="Dashboard Financeiro Biasi",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Configurar locale para formato brasileiro
try:
    locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
except:
    try:
        locale.setlocale(locale.LC_ALL, 'portuguese_brazil')
    except:
        locale.setlocale(locale.LC_ALL, '')  # Usa o locale padrão do sistema

# Estilo CSS customizado
st.markdown("""
    <style>
    .main {
        padding: 2rem;
    }
    
    header {
        visibility: hidden;
    }
    
    h1 {
        color: #086788;
        padding-bottom: 1rem;
    }
    
    h2 {
        color: #333;
        padding: 1rem 0;
    }
    
    /* Estilo para os botões do Streamlit */
    div.stButton > button {
        display: flex !important;
        flex-direction: column !important;
        justify-content: flex-start !important;
        width: 100%;
        background-color: #f8f9fa;
        border: none;
        padding: 1.5rem !important;
        border-radius: 15px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        text-align: left;
        color: #333;
        font-weight: normal;
        margin-bottom: 1.5rem;
        transition: transform 0.3s, box-shadow 0.3s;
        height: 150px !important; /* Altura fixa para todos os cards */
        min-height: 200px !important;
        white-space: normal !important;
        overflow-y: auto !important; /* Adiciona scroll se o conteúdo for muito extenso */
    }
    
    div.stButton > button:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 16px rgba(0,0,0,0.15);
        border: none;
        background-color: #f8f9fa;
        color: #333;
    }
    
    div.stButton > button:focus {
        transform: translateY(-5px);
        box-shadow: 0 8px 16px rgba(0,0,0,0.15);
        border: none;
        background-color: #f8f9fa;
        color: #333;
    }
    
    div.stButton > button:active {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.15);
        background-color: #f0f0f0;
    }

    /* Estilo para o texto dentro dos botões */
    div.stButton > button p {
        margin: 0;
    }
    
    div.stButton > button strong {
        font-size: 1.1rem;
        margin-bottom: 0.8rem;
        display: block;
    }
    </style>
""", unsafe_allow_html=True)

# Título principal
st.title("💰 Dashboard Financeiro Biasi")
st.markdown("Bem-vindo ao sistema de dashboards financeiros da Biasi. Escolha uma das páginas para acessar os diferentes relatórios.")

# Visão geral dos dashboards disponíveis
st.header("Dashboards Disponíveis")

# Criar grid para os cards de dashboards
col1, col2, col3, col4, col5 = st.columns(5)

# Configuração dos dashboards
dashboards = [
    {
        "titulo": "Análise de Financiamentos",
        "descricao": "Acompanhe o status dos financiamentos, valores pagos e a pagar, além de projeções de quitação.",
        "icon": "💰",
        "pagina": "1_💰_Analise_Financiamentos",
        "coluna": col1
    },
    {
        "titulo": "Controle de Entrada e Saída",
        "descricao": "Visualize o balanço financeiro com entradas, saídas e comparativos com metas estabelecidas.",
        "icon": "📊",
        "pagina": "2_📊_Controle_Entradas_Saidas",
        "coluna": col2
    },
    {
        "titulo": "Controle de Despesas",
        "descricao": "Acompanhe despesas fixas e variáveis, categorizadas por tipo e forma de pagamento.",
        "icon": "💸",
        "pagina": "3_💸_Controle_Despesas",
        "coluna": col3
    },
    {
        "titulo": "Análise de Produção",
        "descricao": "Monitore a produção por período, produto, categoria e responsável, com métricas de eficiência.",
        "icon": "🏭",
        "pagina": "5_🏭_Analise_Producao",
        "coluna": col4
    },
    {
        "titulo": "Análise de Dívidas",
        "descricao": "Visualize o detalhamento das dívidas, status de pagamento e valores em atraso.",
        "icon": "📉",
        "pagina": "4_📉_Analise_Dividas",
        "coluna": col5
    }
]

# Criação dos botões personalizados em formato de card
for dash in dashboards:
    with dash["coluna"]:
        btn_label = f"""**{dash['icon']} {dash['titulo']}**\n\n{dash['descricao']}"""
        if st.button(btn_label, key=dash["pagina"], use_container_width=True):
            st.switch_page(f"pages/{dash['pagina']}.py")

st.markdown("---")
st.caption(f"Dashboard Biasi • Atualizado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")