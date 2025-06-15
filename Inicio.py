import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import locale
import pytz

# Configuração da página
st.set_page_config(
    page_title="Dashboard Financeiro Biasi",
    page_icon="💰",
    layout="wide"
)

# Configurar locale para formato brasileiro
try:
    locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
except:
    try:
        locale.setlocale(locale.LC_ALL, 'portuguese_brazil')
    except:
        locale.setlocale(locale.LC_ALL, '')

# Título principal
st.title("💰 Dashboard Financeiro Biasi")
st.markdown("Bem-vindo ao sistema de dashboards financeiros da Biasi. Explore os diferentes relatórios disponíveis usando o menu lateral.")
st.info("👈 **Use o menu lateral** para navegar entre os diferentes dashboards disponíveis.")
st.markdown("") # Espaço

# Visão geral dos dashboards disponíveis
st.header("📊 Dashboards Disponíveis")

st.markdown("") # Espaço

# Configuração dos dashboards
dashboards = [
    {
        "titulo": "Análise de Financiamentos",
        "descricao": "Acompanhe o status dos financiamentos, valores pagos e a pagar, além de projeções de quitação.",
        "icon": "💰"
    },
    {
        "titulo": "Controle de Entrada e Saída",
        "descricao": "Visualize o balanço financeiro com entradas, saídas e comparativos com metas estabelecidas.",
        "icon": "📊"
    },
    {
        "titulo": "Controle de Despesas",
        "descricao": "Acompanhe despesas fixas e variáveis, categorizadas por tipo e forma de pagamento.",
        "icon": "💸"
    },
    {
        "titulo": "Análise de Produção",
        "descricao": "Monitore a produção por período, produto, categoria e responsável, com métricas de eficiência.",
        "icon": "🏭"
    },
    {
        "titulo": "Análise de Dívidas",
        "descricao": "Visualize o detalhamento das dívidas, status de pagamento e valores em atraso.",
        "icon": "📉"
    }
]

# Criar grid para os cards informativos
col1, col2, col3, col4, col5 = st.columns(5)
colunas = [col1, col2, col3, col4, col5]

# Criação dos cards informativos
for idx, dash in enumerate(dashboards):
    with colunas[idx]:
        # Container para cada card
        with st.container():
            # Ícone grande
            st.markdown(f"<div style='text-align: center; font-size: 3rem; margin-bottom: 1rem;'>{dash['icon']}</div>", unsafe_allow_html=True)
            
            # Título do dashboard
            st.markdown(f"**{dash['titulo']}**")
            
            # Descrição
            st.markdown(f"<small>{dash['descricao']}</small>", unsafe_allow_html=True)
            
            st.markdown("") # Espaço entre cards

# Seção de informações adicionais
st.markdown("---")
st.markdown("") 
# Dicas de uso

with st.expander("💡 Como Navegar"):
    st.markdown("""
    **Para acessar os dashboards:**
    - Use o **menu lateral** (seta no canto superior esquerdo) para navegar entre as páginas
    - Cada dashboard possui filtros específicos na barra lateral
    - Baixe os dados filtrados quando necessário
    """)

# Rodapé
st.markdown("---")
col_footer1, col_footer2, col_footer3 = st.columns([1,2,1])

# Horário de São Paulo
sp_timezone = pytz.timezone('America/Sao_Paulo')
hora_sp = datetime.now(sp_timezone)

with col_footer2:
    st.markdown(f"""
    <div style='text-align: center;'>
        <p><strong>Dashboard Biasi</strong> • Versão 2.0</p>
        <p><small>Atualizado em: {hora_sp.strftime('%d/%m/%Y %H:%M:%S')} (SP)</small></p>
        <p><small>Sistema desenvolvido usando Streamlit e Python</small></p>
    </div>
    """, unsafe_allow_html=True)