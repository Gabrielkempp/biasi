import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import locale
from datetime import timedelta

# Configuração da página
st.set_page_config(
    page_title="Controle de Despesas",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Aplicando estilo CSS customizado
st.markdown("""
    <style>
    .main {
        padding: 0rem 1rem;
    }
    .st-emotion-cache-1r6slb0 {
        background-color: #f8f9fa;
        border-radius: 0.5rem;
        padding: 1rem;
        box-shadow: 0 0.125rem 0.25rem rgba(0,0,0,0.075);
    }
    .st-emotion-cache-1629p8f h2 {
        color: #2c3e50;
        font-weight: 600;
        margin-bottom: 1rem;
    }
    .metric-card {
        background-color: white;
        padding: 1rem;
        border-radius: 0.5rem;
        box-shadow: 0 0.125rem 0.25rem rgba(0,0,0,0.075);
        text-align: center;
    }
    </style>
    """, unsafe_allow_html=True)

# Configuração de locale
try:
    locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
except:
    try:
        locale.setlocale(locale.LC_ALL, 'portuguese_brazil')
    except:
        locale.setlocale(locale.LC_ALL, '')

# Meses em português
meses_ptbr = {
    'January': 'Janeiro', 'February': 'Fevereiro', 'March': 'Março',
    'April': 'Abril', 'May': 'Maio', 'June': 'Junho',
    'July': 'Julho', 'August': 'Agosto', 'September': 'Setembro',
    'October': 'Outubro', 'November': 'Novembro', 'December': 'Dezembro'
}

def convert_to_real(value):
    try:
        return locale.currency(abs(value), grouping=True)
    except:
        return f'R$ {abs(value):,.2f}'.replace(',', '*').replace('.', ',').replace('*', '.')

def clean_monetary_value(value):
    if pd.isna(value):
        return 0.0
    if isinstance(value, (int, float)):
        return abs(float(value))
    cleaned = str(value).replace('R$', '').replace(' ', '').replace('.', '').replace(',', '.')
    return abs(float(cleaned))

def traduzir_mes(texto):
    for en, pt in meses_ptbr.items():
        texto = texto.replace(en, pt)
    return texto

# Leitura e tratamento do DataFrame
sheet_url = "https://docs.google.com/spreadsheets/d/1nbNmbgO37FC-9dlwivefFZnQ43-5A8H8Is7K9WLqgx4/export?format=csv&gid=634814073"

@st.cache_data(ttl=300)  # Cache por 5 minutos
def load_data():
    df = pd.read_csv(sheet_url)
    new_columns = df.iloc[0]
    df.columns = df.columns.astype(str)
    df = df.iloc[1:]
    df.columns = new_columns
    df = df.dropna(axis=1, how='all')
    return df

df = load_data()

# Separar em dois DataFrames
df_contas = df.iloc[:, 0:6]
df_pessoal = df.iloc[:, 6:9]

# Renomear colunas
df_contas.columns = ['Nome', 'Valor', 'Data_Vencimento', 'Data_Pagamento', 'Forma_Pagamento', 'Categoria']
df_pessoal.columns = ['Nome', 'Valor', 'Data']

# Remover linhas onde Nome é nulo
df_contas = df_contas.dropna(subset=['Nome'])
df_pessoal = df_pessoal.dropna(subset=['Nome'])

# Limpar valores monetários
df_contas['Valor'] = df_contas['Valor'].apply(clean_monetary_value)
df_pessoal['Valor'] = df_pessoal['Valor'].apply(clean_monetary_value)

# Converter datas
df_contas['Data_Vencimento'] = pd.to_datetime(df_contas['Data_Vencimento'], format='%d/%m/%Y', errors='coerce')
df_contas['Data_Pagamento'] = pd.to_datetime(df_contas['Data_Pagamento'], format='%d/%m/%Y', errors='coerce')
df_pessoal['Data'] = pd.to_datetime(df_pessoal['Data'], format='%d/%m/%Y', errors='coerce')

# Sidebar com filtros
st.sidebar.title('📊 Filtros')
with st.sidebar:
    st.markdown('---')
    
    # Filtro de data
    data_inicial = df_contas['Data_Vencimento'].min().date()
    data_final = df_contas['Data_Vencimento'].max().date()
    
    datas = st.date_input(
        "Período de Análise",
        value=(data_inicial, data_final),
        min_value=data_inicial,
        max_value=data_final
    )
    
    
    if len(datas) == 2:
        start_date, end_date = datas
        # Converter para Timestamp para garantir que a comparação seja feita entre tipos compatíveis
        start_timestamp = pd.Timestamp(start_date)
        end_timestamp = pd.Timestamp(end_date)
        
        mask_contas = (df_contas['Data_Vencimento'] >= start_timestamp) & (df_contas['Data_Vencimento'] <= end_timestamp)
        mask_pessoal = (df_pessoal['Data'] >= start_timestamp) & (df_pessoal['Data'] <= end_timestamp)
        
        df_contas_filtrado = df_contas[mask_contas]
        df_pessoal_filtrado = df_pessoal[mask_pessoal]
    else:
        df_contas_filtrado = df_contas
        df_pessoal_filtrado = df_pessoal
    
    # Filtro de categoria
    categorias = ['Todas'] + sorted(df_contas['Categoria'].unique().tolist())
    categoria_selecionada = st.selectbox('Categoria', categorias)
    
    if categoria_selecionada != 'Todas':
        df_contas_filtrado = df_contas_filtrado[df_contas_filtrado['Categoria'] == categoria_selecionada]
    
    st.markdown('---')

# Criar as tabs
tab1, tab2 = st.tabs(["📑 Despesa Biasi", "👤 Despesa Pessoal"])

# Tab 1 - Despesas Fixas
with tab1:
    st.header('📊 Análise de Despesas')
    st.markdown('---')
    
    # Cards de métricas
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""
            <div style="background-color: white; padding: 1rem; border-radius: 0.5rem; box-shadow: 0 0.125rem 0.25rem rgba(0,0,0,0.075);">
            <div style="color: rgb(71, 85, 105); font-size: 1rem; font-weight: 400;">💰 Total de Despesas</div>
        """, unsafe_allow_html=True)
        
        st.metric(
            label="",  # label vazio pois já temos o título no markdown
            value=convert_to_real(df_contas_filtrado['Valor'].sum()))
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        with st.container():
            st.markdown("""
            <div style="background-color: white; padding: 1rem; border-radius: 0.5rem; box-shadow: 0 0.125rem 0.25rem rgba(0,0,0,0.075);">
            <div style="color: rgb(71, 85, 105); font-size: 1rem; font-weight: 400;">📊 Média por Despesa</div>
            """, unsafe_allow_html=True)
            st.metric("",
                convert_to_real(df_contas_filtrado['Valor'].mean())
            )
            st.markdown('</div>', unsafe_allow_html=True)
    
    with col3:
        with st.container():
            st.markdown("""
            <div style="background-color: white; padding: 1rem; border-radius: 0.5rem; box-shadow: 0 0.125rem 0.25rem rgba(0,0,0,0.075);">
            <div style="color: rgb(71, 85, 105); font-size: 1rem; font-weight: 400;">⚠️ Maior Despesa</div>
            """, unsafe_allow_html=True)
            despesas_vencidas = df_contas_filtrado[
                (df_contas_filtrado['Data_Vencimento'] <= pd.Timestamp.now()) & 
                (df_contas_filtrado['Data_Pagamento'].isna())
            ]

            # Adicionar métrica para a categoria com o maior valor gasto considerando todas as despesas
            gastos_por_categoria = df_contas_filtrado.groupby('Categoria')['Valor'].sum()
            if not gastos_por_categoria.empty:
                categoria_mais_valor = gastos_por_categoria.idxmax()
                valor_mais_valor = gastos_por_categoria.max()
            else:
                categoria_mais_valor = "N/A"
                valor_mais_valor = 0

            st.metric(f"{categoria_mais_valor}", f"{convert_to_real(valor_mais_valor)}")

            st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('---')

    # Gráficos em duas colunas
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader('📈 Despesas por Categoria')
        categoria_sum = df_contas_filtrado.groupby('Categoria')['Valor'].sum().sort_values(ascending=True)
        fig_categoria = px.bar(
            categoria_sum,
            orientation='h',
            template='plotly_white',
            color_discrete_sequence=['#ff6b6b']
        )
        fig_categoria.update_layout(
            height=400,
            margin=dict(t=30, b=0, l=0, r=0),
            yaxis_title='',
            xaxis_title='Valor Total (R$)',
            showlegend=False,
        )
        fig_categoria.update_traces(
            texttemplate='R$ %{x:,.2f}',
            textposition='outside'
        )
        st.plotly_chart(fig_categoria, use_container_width=True, config={'displayModeBar': False, 'staticPlot': True})

    with col2:
        st.subheader('💳 Formas de Pagamento')
        payment_data = df_contas_filtrado.groupby('Forma_Pagamento')['Valor'].sum().sort_values(ascending=True)
        
        fig_payment = px.bar(
            payment_data,
            orientation='h',
            template='plotly_white',
            color_discrete_sequence=['#4dabf7']
        )
        fig_payment.update_layout(
            height=300,
            margin=dict(t=30, b=0, l=0, r=0),
            yaxis_title='',
            xaxis_title='Valor Total (R$)',
            showlegend=False,
        )
        fig_payment.update_traces(
            texttemplate='R$ %{x:,.2f}',
            textposition='outside'
        )
        st.plotly_chart(fig_payment, use_container_width=True, config={'displayModeBar': False, 'staticPlot': True})
    
    # Tabela detalhada
    st.markdown('---')
    st.subheader('📋 Detalhamento das Despesas')
    
    df_contas_display = df_contas_filtrado.copy()
    df_contas_display['Data_Vencimento'] = df_contas_display['Data_Vencimento'].dt.strftime('%d/%m/%Y')
    df_contas_display['Data_Pagamento'] = df_contas_display['Data_Pagamento'].dt.strftime('%d/%m/%Y')
    df_contas_display['Status'] = np.where(
    df_contas_display['Data_Pagamento'].notna(),
        '✅ Pago',
        np.where(
            pd.to_datetime(df_contas_display['Data_Vencimento'], format='%d/%m/%Y', dayfirst=True) > pd.Timestamp.now(),
            '⏳ Pendente',
            '⚠️ Vencido'
        )
    )
    
    # Reordenar colunas
    df_contas_display = df_contas_display[['Nome', 'Valor', 'Data_Vencimento', 'Data_Pagamento', 'Forma_Pagamento', 'Categoria', 'Status']]
    
    st.dataframe(
        df_contas_display.style
        .format({'Valor': 'R$ {:,.2f}'})
        .set_properties(**{
            'color': '#2c3e50',
            'border-color': '#dee2e6'
        })
        .set_table_styles([
            {'selector': 'th', 'props': [('background-color', '#ff6b6b'), ('color', 'white')]},
            {'selector': 'tr:hover', 'props': [('background-color', '#fff5f5')]}
        ])
        .apply(lambda x: ['background-color: #f8f9fa' for _ in range(len(x))])
        .apply(lambda x: [
            'background-color: #fff5f5' if col == 'Status' and val == '⚠️ Vencido' else
            'background-color: #f8f9fa'
            for col, val in x.items()
        ], axis=1),
        height=400, width=1000
    )

# Tab 2 - Despesas Variáveis
with tab2:
    st.header('👤 Análise de Despesa Pessoal')
    st.markdown('---')
    
    # Cards de métricas
    col1, col2, col3 = st.columns(3)
    with col1:
        with st.container():
            st.markdown("""
            <div style="background-color: white; padding: 1rem; border-radius: 0.5rem; box-shadow: 0 0.125rem 0.25rem rgba(0,0,0,0.075);">
            <div style="color: rgb(71, 85, 105); font-size: 1rem; font-weight: 400;">💰 Total de Despesas</div>
            """, unsafe_allow_html=True)
            
            # Verificar se o DataFrame não está vazio
            if not df_pessoal_filtrado.empty:
                total_despesas = df_pessoal_filtrado['Valor'].sum()
            else:
                total_despesas = 0
                
            st.metric("", convert_to_real(total_despesas))
            st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        with st.container():
            st.markdown("""
            <div style="background-color: white; padding: 1rem; border-radius: 0.5rem; box-shadow: 0 0.125rem 0.25rem rgba(0,0,0,0.075);">
            <div style="color: rgb(71, 85, 105); font-size: 1rem; font-weight: 400;">📊 Média por Despesa</div>
            """, unsafe_allow_html=True)
            
            # Verificar se o DataFrame não está vazio
            if not df_pessoal_filtrado.empty:
                media_despesas = df_pessoal_filtrado['Valor'].mean()
            else:
                media_despesas = 0
                
            st.metric("", convert_to_real(media_despesas))
            st.markdown('</div>', unsafe_allow_html=True)

    with col3:
        with st.container():
            st.markdown("""
            <div style="background-color: white; padding: 1rem; border-radius: 0.5rem; box-shadow: 0 0.125rem 0.25rem rgba(0,0,0,0.075);">
            <div style="color: rgb(71, 85, 105); font-size: 1rem; font-weight: 400;">💰 Maior Gasto</div>
            """, unsafe_allow_html=True)
            
            # Tratar com segurança a extração de mês
            if not df_pessoal_filtrado.empty:
                # Criar uma cópia segura do DataFrame
                df_temp = df_pessoal_filtrado.copy()
                # Garantir que a coluna Data não tenha NaN
                df_temp = df_temp.dropna(subset=['Data'])
                
                if not df_temp.empty:
                    df_temp['Mês'] = df_temp['Data'].dt.strftime('%Y-%m')
                    mes_atual = pd.Timestamp.now().strftime('%Y-%m')
                    
                    # Calcular as despesas do mês atual de forma segura
                    despesas_mes_atual = df_temp[df_temp['Mês'] == mes_atual]['Valor'].sum() if not df_temp.empty else 0
                    
                    # Calcular os gastos por pessoa de forma segura
                    gastos_por_pessoa = df_temp.groupby('Nome')['Valor'].sum()
                    
                    if not gastos_por_pessoa.empty:
                        pessoa_mais_gastou = gastos_por_pessoa.idxmax()
                        valor_mais_gastou = gastos_por_pessoa.max()
                    else:
                        pessoa_mais_gastou = "N/A"
                        valor_mais_gastou = 0
                else:
                    pessoa_mais_gastou = "N/A"
                    valor_mais_gastou = 0
            else:
                pessoa_mais_gastou = "N/A"
                valor_mais_gastou = 0
            
            st.metric("", f"{pessoa_mais_gastou}: {convert_to_real(valor_mais_gastou)}")
            st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('---')

    # Gráficos em duas colunas
    col1, col2 = st.columns(2)

with col1:
    st.subheader('👥 Despesas por Pessoa')
    
    if not df_pessoal_filtrado.empty:
        pessoa_sum = df_pessoal_filtrado.groupby('Nome')['Valor'].sum().sort_values(ascending=False)

        if not pessoa_sum.empty:
            # Convertendo a série para DataFrame para melhor manipulação
            df_plot = pessoa_sum.reset_index()
            
            # Criando o gráfico de colunas (barras verticais)
            fig_pessoa = px.bar(
                df_plot,
                x='Nome',           # Eixo X com nomes das pessoas
                y='Valor',          # Eixo Y com valores
                template='plotly_white',
                color_discrete_sequence=['#9775fa']
            )
            
            # Configurando o layout do gráfico
            fig_pessoa.update_layout(
                height=400,
                margin=dict(t=30, b=0, l=0, r=0),
                yaxis_title='Valor Total (R$)',
                xaxis_title='',
                showlegend=False,
            )
            
            # Configurando o formato dos textos nas barras
            fig_pessoa.update_traces(
                texttemplate='R$ %{y:,.2f}',
                textposition='outside'
            )
            
            # Exibindo o gráfico no Streamlit
            st.plotly_chart(fig_pessoa, use_container_width=True, config={'displayModeBar': False, 'staticPlot': True})
            
        else:
            st.info("Não há dados para exibir no período selecionado.")
    else:
        st.info("Não há dados para exibir no período selecionado.")

with col2:
    st.subheader('📈 Despesas Acumuladas')
    
    if not df_pessoal_filtrado.empty:
        # Verificar se há dados não-NaN para ordenação
        df_temp = df_pessoal_filtrado.dropna(subset=['Data'])
        
        if not df_temp.empty:
            df_pessoal_sorted = df_temp.sort_values('Data')
            df_pessoal_sorted['Valor_Acumulado'] = df_pessoal_sorted['Valor'].cumsum()
            
            fig_acumulado = px.line(
                df_pessoal_sorted,
                x='Data',
                y='Valor_Acumulado',
                template='plotly_white',
                color_discrete_sequence=['#9775fa']
            )
            fig_acumulado.update_layout(
                height=300,
                margin=dict(t=30, b=0, l=0, r=0),
                yaxis_title='Valor Acumulado (R$)',
                xaxis_title='',
            )
            st.plotly_chart(fig_acumulado, use_container_width=True,  config={'displayModeBar': False, 'staticPlot': True})
        else:
            st.info("Não há dados com datas válidas para exibir no período selecionado.")
    else:
        st.info("Não há dados para exibir no período selecionado.")

# Tabela detalhada
st.markdown('---')
st.subheader('📋 Detalhamento das Despesas')
   
df_pessoal_display = df_pessoal_filtrado.copy()
df_pessoal_display['Data'] = df_pessoal_display['Data'].dt.strftime('%d/%m/%Y')
df_pessoal_display['Mês'] = pd.to_datetime(df_pessoal_display['Data'], format='%d/%m/%Y', dayfirst=True).dt.strftime('%B/%Y')
df_pessoal_display['Mês'] = df_pessoal_display['Mês'].apply(traduzir_mes)
    
# Reordenar colunas
df_pessoal_display = df_pessoal_display[['Data', 'Nome', 'Valor']]
    
st.dataframe(
        df_pessoal_display.style
        .format({'Valor': 'R$ {:,.2f}'})
        .set_properties(**{
            'color': '#2c3e50',
            'border-color': '#dee2e6'
        })
        .set_table_styles([
            {'selector': 'th', 'props': [('background-color', '#9775fa'), ('color', 'white')]},
            {'selector': 'tr:hover', 'props': [('background-color', '#f3f0ff')]}
        ])
        .apply(lambda x: ['background-color: #f8f9fa' for _ in range(len(x))]),
        height=400, width=600
)    