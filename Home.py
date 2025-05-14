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
    initial_sidebar_state="expanded"
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
        display: block;
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
        height: auto !important;
        white-space: normal !important;
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
    </style>
""", unsafe_allow_html=True)

# Título principal
st.title("💰 Dashboard Financeiro Biasi")
st.markdown("Bem-vindo ao sistema de dashboards financeiros da Biasi. Escolha uma das páginas na barra lateral para acessar os diferentes relatórios.")

# Visão geral dos dashboards disponíveis
st.header("Dashboards Disponíveis")

# Criar grid para os cards de dashboards
col1, col2, col3 = st.columns(3)

# Configuração dos dashboards
dashboards = [
    {
        "titulo": "Análise de Financiamentos",
        "descricao": "Acompanhe o status dos financiamentos, valores pagos e a pagar, além de projeções de quitação.",
        "icon": "💰",
        "pagina": "1_Analise_Financiamentos",
        "coluna": col1
    },
    {
        "titulo": "Controle de Entrada e Saída",
        "descricao": "Visualize o balanço financeiro com entradas, saídas e comparativos com metas estabelecidas.",
        "icon": "📊",
        "pagina": "2_Controle_Entradas_Saidas",
        "coluna": col1
    },
    {
        "titulo": "Controle de Despesas",
        "descricao": "Acompanhe despesas fixas e variáveis, categorizadas por tipo e forma de pagamento.",
        "icon": "💸",
        "pagina": "3_Controle_Despesas",
        "coluna": col2
    },
    {
        "titulo": "Análise de Produção",
        "descricao": "Monitore a produção por período, produto, categoria e responsável, com métricas de eficiência.",
        "icon": "🏭",
        "pagina": "5_Analise_Producao",
        "coluna": col2
    },
    {
        "titulo": "Análise de Dívidas",
        "descricao": "Visualize o detalhamento das dívidas, status de pagamento e valores em atraso.",
        "icon": "📈",
        "pagina": "4_Analise_Dividas",
        "coluna": col3
    }
]

# Criação dos botões personalizados em formato de card
for dash in dashboards:
    with dash["coluna"]:
        btn_label = f"""**{dash['icon']} {dash['titulo']}**\n\n{dash['descricao']}"""
        if st.button(btn_label, key=dash["pagina"], use_container_width=True):
            st.switch_page(f"pages/{dash['pagina']}.py")

# Informações gerais
st.markdown("---")
st.header("Sobre o Dashboard")
st.markdown("""
Este sistema de dashboards foi desenvolvido para ajudar na gestão financeira da Biasi, 
oferecendo visualizações claras e detalhadas dos diversos aspectos financeiros da empresa.

### Principais funcionalidades:
- Acompanhamento de financiamentos e dívidas
- Controle de despesas fixas e variáveis
- Monitoramento de entradas e saídas financeiras
- Análise de produção e eficiência

### Como usar:
1. Selecione o dashboard desejado no menu lateral ou clique nos cards acima
2. Utilize os filtros disponíveis para personalizar as visualizações
3. Explore os gráficos e tabelas interativos
4. Exporte os dados quando necessário
""")

# Rodapé
st.markdown("---")
st.caption(f"Dashboard Financeiro Biasi • Atualizado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")