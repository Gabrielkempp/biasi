import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
from datetime import datetime
import locale
from datetime import timedelta

# Configuração da página
st.set_page_config(
    page_title="Controle de Despesas",
    page_icon="💰",
    layout="wide"
)

# Configuração global do Plotly para formato brasileiro
pio.templates.default = "plotly_white"
pio.templates[pio.templates.default].layout.update(
    separators=', ',  # Formato brasileiro: ponto para milhar, vírgula para decimal
)

# Aplicando estilo CSS customizado
st.markdown("""
    <style>
    .main {
        padding: 0rem 1rem;
    }
            
    header {
         visibility: hidden;
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
    
    .stMetric {
        background-color: #f8f9fa;
        padding: 1.5rem;
        border-radius: 25px;
        box-shadow: 0 8px 16px rgba(0,0,0,0.1);
    }
    
    /* Estilo melhorado para headers */
    .section-header {
        padding: 0.5rem 0;
        border-bottom: 2px solid #f0f0f0;
        margin-bottom: 1rem;
    }
    
    /* Melhoria para tabelas */
    div[data-testid="stDataFrame"] > div {
        border-radius: 0.5rem;
        box-shadow: 0 0.125rem 0.25rem rgba(0,0,0,0.075);
    }
    
    /* Formatação para o datepicker */
    div[data-testid="stDateInput"] {
        background-color: white;
        border-radius: 0.5rem;
        padding: 0.5rem;
        box-shadow: 0 0.1rem 0.2rem rgba(0,0,0,0.05);
    }
    
    /* Estilo para botões de seleção rápida */
    div[data-testid="stButton"] button {
        background-color: #f0f2f6;
        border-radius: 0.5rem;
        color: #2c3e50;
        font-weight: 500;
        border: 1px solid #e0e3e9;
        transition: all 0.3s ease;
    }
    
    div[data-testid="stButton"] button:hover {
        background-color: #e0e3e9;
        border-color: #c0c3c9;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
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

# Função para formatar valores no padrão brasileiro
def formatar_valor_br(valor):
    if pd.isna(valor) or valor == 0:
        return "R$ 0,00"
    return f'R$ {abs(valor):,.2f}'.replace(',', '*').replace('.', ',').replace('*', '.')

# Leitura e tratamento do DataFrame para Despesas Biasi
# Nova URL para despesas Biasi
sheet_url_biasi = "https://docs.google.com/spreadsheets/d/1tw1i3l2UxCJrm65TiIIieeVXAH8-o1uqjM11yGfNhXE/export?format=csv&gid=0"

# Nova URL para despesas Pessoal
sheet_url_pessoal = "https://docs.google.com/spreadsheets/d/1tw1i3l2UxCJrm65TiIIieeVXAH8-o1uqjM11yGfNhXE/export?format=csv&gid=1520802263"

@st.cache_data(ttl=300)  # Cache por 5 minutos
def load_data_biasi():
    df = pd.read_csv(sheet_url_biasi)
    new_columns = df.iloc[0]
    df.columns = df.columns.astype(str)
    df = df.iloc[1:]
    df.columns = new_columns
    df = df.dropna(axis=1, how='all')
    return df

@st.cache_data(ttl=300)  # Cache por 5 minutos
def load_data_pessoal():
    df = pd.read_csv(sheet_url_pessoal)
    new_columns = df.iloc[0]
    df.columns = df.columns.astype(str)
    df = df.iloc[1:]
    df.columns = new_columns
    df = df.dropna(axis=1, how='all')
    return df

# Carregando os dados de ambas as fontes
df_biasi = load_data_biasi()
df_pessoal_raw = load_data_pessoal()

# Processamento dos dados Biasi
df_contas = df_biasi.iloc[:, 0:6]
df_contas.columns = ['Nome', 'Valor', 'Data_Vencimento', 'Data_Pagamento', 'Forma_Pagamento', 'Categoria']

# Remover linhas onde Nome é nulo
df_contas = df_contas.dropna(subset=['Nome'])

# Limpar valores monetários
df_contas['Valor'] = df_contas['Valor'].apply(clean_monetary_value)

# Converter datas
df_contas['Data_Vencimento'] = pd.to_datetime(df_contas['Data_Vencimento'], format='%d/%m/%Y', errors='coerce')
df_contas['Data_Pagamento'] = pd.to_datetime(df_contas['Data_Pagamento'], format='%d/%m/%Y', errors='coerce')

# Processamento dos dados Pessoal
df_pessoal = df_pessoal_raw.iloc[:, 0:3]  # Ajustando para pegar as primeiras 3 colunas
df_pessoal.columns = ['Nome', 'Valor', 'Data']

# Remover linhas onde Nome é nulo
df_pessoal = df_pessoal.dropna(subset=['Nome'])

# Limpar valores monetários
df_pessoal['Valor'] = df_pessoal['Valor'].apply(clean_monetary_value)

# Converter datas
df_pessoal['Data'] = pd.to_datetime(df_pessoal['Data'], format='%d/%m/%Y', errors='coerce')

# Sidebar com filtros
st.sidebar.title('📊 Filtros')
with st.sidebar:
    st.markdown('---')
    
    # Filtro de data - usando o datepicker do Streamlit
    data_inicial = df_contas['Data_Vencimento'].min().date()
    data_final = df_contas['Data_Vencimento'].max().date()
    
    st.markdown("### 📅 Período de Análise")
    
    # Função para calcular datas para os botões de período
    def calcular_datas_periodo(periodo):
        hoje = datetime.now().date()
        primeiro_dia_mes_atual = hoje.replace(day=1)
        
        # Garantir que as datas estejam dentro dos limites disponíveis
        if periodo == "este_mes":
            # Do dia 1 do mês atual até hoje (ou data_final se hoje > data_final)
            inicio = max(primeiro_dia_mes_atual, data_inicial)
            fim = min(hoje, data_final)
            return inicio, fim
        elif periodo == "mes_passado":
            # Mês anterior completo (ajustado para os limites)
            ultimo_dia_mes_passado = primeiro_dia_mes_atual - timedelta(days=1)
            primeiro_dia_mes_passado = ultimo_dia_mes_passado.replace(day=1)
            inicio = max(primeiro_dia_mes_passado, data_inicial)
            fim = min(ultimo_dia_mes_passado, data_final)
            return inicio, fim
        elif periodo == "este_ano":
            # Do dia 1 de janeiro do ano atual até hoje (ajustado para os limites)
            primeiro_dia_ano = hoje.replace(month=1, day=1)
            inicio = max(primeiro_dia_ano, data_inicial)
            fim = min(hoje, data_final)
            return inicio, fim
        elif periodo == "tudo":
            # Todo o período disponível
            return data_inicial, data_final
    
    # Botões para seleção rápida de períodos
    st.markdown("### ⚡ Seleção Rápida")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Este Ano", use_container_width=True):
            datas_periodo = calcular_datas_periodo("este_ano")
        if st.button("Mês Passado", use_container_width=True):
            datas_periodo = calcular_datas_periodo("mes_passado")
    
    with col2:
        if st.button("Este Mês", use_container_width=True):
            datas_periodo = calcular_datas_periodo("este_mes")
        if st.button("Tudo", use_container_width=True):
            datas_periodo = calcular_datas_periodo("tudo")
    
    # Armazenar seleção em session state caso um botão seja clicado
    if 'datas_periodo' not in st.session_state:
        st.session_state.datas_periodo = (data_inicial, data_final)
    
    # Atualizar as datas se um botão foi clicado
    if 'datas_periodo' in locals():
        st.session_state.datas_periodo = datas_periodo
    
    # Usar o date_input com o valor do session state, garantindo que esteja dentro dos limites
    datas_atuais = st.session_state.datas_periodo
    # Validar que as datas estão dentro dos limites válidos
    if isinstance(datas_atuais, tuple) and len(datas_atuais) == 2:
        if datas_atuais[0] < data_inicial:
            datas_atuais = (data_inicial, datas_atuais[1])
        if datas_atuais[1] > data_final:
            datas_atuais = (datas_atuais[0], data_final)
    else:
        datas_atuais = (data_inicial, data_final)
    
    # Usar o date_input com valores validados
    datas = st.date_input(
        "Selecione o período",
        value=datas_atuais,
        min_value=data_inicial,
        max_value=data_final,
        format="DD/MM/YYYY"  # Formato brasileiro
    )
    
    # Atualizar o session state com a seleção manual do usuário
    if datas != st.session_state.datas_periodo:
        st.session_state.datas_periodo = datas
    
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
    st.markdown("### 🏷️ Categorias")
    categorias = ['Todas'] + sorted(df_contas['Categoria'].dropna().astype(str).unique().tolist())
    categoria_selecionada = st.selectbox('Selecione a categoria:', categorias)
    
    if categoria_selecionada != 'Todas':
        df_contas_filtrado = df_contas_filtrado[df_contas_filtrado['Categoria'] == categoria_selecionada]
    
    st.markdown('---')

# Criar as tabs
tab1, tab2 = st.tabs(["📑 Despesa Biasi", "👤 Despesa Pessoal"])

# Tab 1 - Despesas Fixas
with tab1:
    st.markdown('<h1 class="section-header">📊 Análise de Despesas</h1>', unsafe_allow_html=True)
    
    # Cards de métricas usando st.metric nativo do Streamlit
    col1, col2, col3 = st.columns(3)
    with col1:
        # Aplicar CSS customizado
        st.markdown('<div class="metric-blue">', unsafe_allow_html=True)
        st.metric(
            label="Total de Despesas",
            value=formatar_valor_br(df_contas_filtrado['Valor'].sum())
        )
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="metric-blue">', unsafe_allow_html=True)
        st.metric(
            label="Média por Despesa",
            value=formatar_valor_br(df_contas_filtrado['Valor'].mean())
        )
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col3:
        # Adicionar métrica para a categoria com o maior valor gasto
        gastos_por_categoria = df_contas_filtrado.groupby('Categoria')['Valor'].sum()
        if not gastos_por_categoria.empty:
            categoria_mais_valor = gastos_por_categoria.idxmax()
            valor_mais_valor = gastos_por_categoria.max()
        else:
            categoria_mais_valor = "N/A"
            valor_mais_valor = 0
            
        st.markdown('<div class="metric-purple">', unsafe_allow_html=True)
        st.metric(
            label=f"Maior Despesa: {categoria_mais_valor}",
            value=formatar_valor_br(valor_mais_valor)
        )
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('---')

    # Gráficos em duas colunas
    col1, col2 = st.columns((6,4))
    
    with col1:
        st.markdown('<h3 class="section-header">📈 Despesas por Categoria</h3>', unsafe_allow_html=True)
        categoria_sum = df_contas_filtrado.groupby('Categoria')['Valor'].sum().sort_values(ascending=True)
        
        # Aplicando capitalize nas categorias
        categoria_sum.index = categoria_sum.index.str.capitalize()
        
        # Calculando um threshold para determinar posição do texto (15% do valor máximo)
        valor_max = categoria_sum.max()
        threshold = valor_max * 0.20
        
        # Lista para armazenar posições de texto
        text_positions = []
        text_colors = []
        
        # Determinando posição do texto para cada valor
        for valor in categoria_sum:
            if valor >= threshold:
                text_positions.append('inside')
                text_colors.append('white')
            else:
                text_positions.append('outside')
                text_colors.append('black')
        
        # Valores formatados para exibição no gráfico
        valores_formatados = [formatar_valor_br(v) for v in categoria_sum.values]
        
        # Criando o gráfico base
        fig_categoria = px.bar(
            categoria_sum,
            orientation='h',
            template='plotly_white',
            color_discrete_sequence=['#DD1C1A']
        )
        
        # Configurações gerais do layout
        fig_categoria.update_layout(
            height=600,
            margin=dict(t=30, b=0, l=0, r=0),
            yaxis_title='',
            xaxis_title='Valor Total (R$)',
            showlegend=False,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)'
        )
        
        # Aplicando as posições de texto individualmente
        fig_categoria.update_traces(
            text=valores_formatados,  # Usando os valores já formatados
            textposition=text_positions
        )
        
        # Formatação do eixo X para padrão brasileiro
        fig_categoria.update_xaxes(
            tickprefix="R$ ",
            separatethousands=True
        )
        
        st.plotly_chart(fig_categoria, use_container_width=True, config={'displayModeBar': False, 'staticPlot': True})

    with col2:
        st.markdown('<h3 class="section-header">💳 Formas de Pagamento</h3>', unsafe_allow_html=True)
        
        # Aplicando capitalize nas categorias
        payment_data = df_contas_filtrado.groupby('Forma_Pagamento')['Valor'].sum().sort_values(ascending=False)
        payment_data.index = payment_data.index.str.capitalize()
        
        # Definindo a paleta de cores personalizada (da imagem)
        custom_colors = ['#086788', '#07A0C3', '#F0C808', '#FFF1D0', '#DD1C1A']
        
        # Valores formatados para o hover e exibição
        valores_formatados = [formatar_valor_br(v) for v in payment_data.values]
        
        # Criando gráfico de pizza com as cores personalizadas
        fig_payment = px.pie(
            values=payment_data.values,
            names=payment_data.index,
            template='plotly_white',
            color_discrete_sequence=custom_colors  # Usando a paleta personalizada
        )
        
        # Configurando o layout
        fig_payment.update_layout(
            height=400,
            margin=dict(t=30, b=0, l=0, r=0),
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.15,
                xanchor="center",
                x=0.5
            ),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)'
        )
        
        # Gerando textos customizados para exibição e hover
        percent_values = payment_data.values / payment_data.values.sum() * 100
        
        # Criando textos customizados que combinam percentual e valor formatado
        text_display = []
        for value, percent in zip(payment_data.values, percent_values):
            formatted_value = formatar_valor_br(value)
            text_display.append(f"{percent:.1f}% ({formatted_value})")
        
        # Aplicando textos personalizados
        fig_payment.update_traces(
            text=text_display,
            textinfo='text+label',
            hoverinfo='label+percent+value'
        )
        
        st.plotly_chart(fig_payment, use_container_width=True, config={'displayModeBar': False, 'staticPlot': True})


    # Tabela detalhada
    st.markdown('---')
    st.markdown('<h3 class="section-header">📋 Detalhamento das Despesas</h3>', unsafe_allow_html=True)
    
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
    
    # Utilizando a função formatar_valor_br para formatar a coluna Valor no estilo brasileiro
    st.dataframe(
        df_contas_display.style
        .format({'Valor': lambda x: formatar_valor_br(x)})
        .set_properties(**{
            'color': '#2c3e50',
            'border-color': '#dee2e6'
        })
        .set_table_styles([
            {'selector': 'th', 'props': [('background-color', '#ff6b6b'), ('color', 'white'), ('font-weight', 'bold')]},
            {'selector': 'tr:hover', 'props': [('background-color', '#fff5f5')]}
        ])
        .apply(lambda x: ['background-color: #f8f9fa' for _ in range(len(x))])
        .apply(lambda x: [
            'background-color: #fff5f5' if col == 'Status' and val == '⚠️ Vencido' else
            'background-color: #f8f9fa'
            for col, val in x.items()
        ], axis=1),
        height=400, 
        width=1000
    )

# Tab 2 - Despesas Variáveis
with tab2:
    st.markdown('<h1 class="section-header">👤 Análise de Despesa Pessoal</h1>', unsafe_allow_html=True)
    
    # Cards de métricas
    col1, col2, col3 = st.columns(3)
    with col1:
        # Verificar se o DataFrame não está vazio
        if not df_pessoal_filtrado.empty:
            total_despesas = df_pessoal_filtrado['Valor'].sum()
        else:
            total_despesas = 0
            
        st.markdown('<div class="metric-green">', unsafe_allow_html=True)
        st.metric(
            label="Total de Despesas",
            value=formatar_valor_br(total_despesas)
        )
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        # Verificar se o DataFrame não está vazio
        if not df_pessoal_filtrado.empty:
            media_despesas = df_pessoal_filtrado['Valor'].mean()
        else:
            media_despesas = 0
            
        st.markdown('<div class="metric-blue">', unsafe_allow_html=True)
        st.metric(
            label="Média por Despesa",
            value=formatar_valor_br(media_despesas)
        )
        st.markdown('</div>', unsafe_allow_html=True)

    with col3:
        # Tratar com segurança a extração de mês
        if not df_pessoal_filtrado.empty:
            # Criar uma cópia segura do DataFrame
            df_temp = df_pessoal_filtrado.copy()
            # Garantir que a coluna Data não tenha NaN
            df_temp = df_temp.dropna(subset=['Data'])
            
            if not df_temp.empty:
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
        
        st.markdown('<div class="metric-purple">', unsafe_allow_html=True)
        st.metric(
            label=f"Maior Gasto: {pessoa_mais_gastou}",
            value=formatar_valor_br(valor_mais_gastou)
        )
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('---')

    # Gráficos em duas colunas
    col1, col2 = st.columns(2)

    with col1:
        st.markdown('<h3 class="section-header">👥 Despesas por Pessoa</h3>', unsafe_allow_html=True)
        
        if not df_pessoal_filtrado.empty:
            pessoa_sum = df_pessoal_filtrado.groupby('Nome')['Valor'].sum().sort_values(ascending=False)

            if not pessoa_sum.empty:
                # Valores formatados para exibição
                valores_formatados = [formatar_valor_br(v) for v in pessoa_sum.values]
                
                # Criando o gráfico de colunas (barras verticais)
                fig_pessoa = px.bar(
                    pessoa_sum,
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
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)'
                )
                
                # Configurando o formato do eixo Y (valores em R$)
                fig_pessoa.update_yaxes(
                    tickprefix="R$ ",
                    separatethousands=True
                )
                
                # Configurando o texto e posição
                fig_pessoa.update_traces(
                    text=valores_formatados,
                    texttemplate="%{text}",
                    textposition='outside'
                )
                
                # Exibindo o gráfico no Streamlit
                st.plotly_chart(fig_pessoa, use_container_width=True, config={'displayModeBar': False, 'staticPlot': True})
                
            else:
                st.info("Não há dados para exibir no período selecionado.")
        else:
            st.info("Não há dados para exibir no período selecionado.")

    with col2:
        st.markdown('<h3 class="section-header">📈 Despesas Acumuladas</h3>', unsafe_allow_html=True)
        
        if not df_pessoal_filtrado.empty:
            # Verificar se há dados não-NaN para ordenação
            df_temp = df_pessoal_filtrado.dropna(subset=['Data'])
            
            if not df_temp.empty:
                df_pessoal_sorted = df_temp.sort_values('Data')
                df_pessoal_sorted['Valor_Acumulado'] = df_pessoal_sorted['Valor'].cumsum()
                
                # Criando valores formatados para hover
                valores_formatados = [formatar_valor_br(v) for v in df_pessoal_sorted['Valor_Acumulado']]
                
                fig_acumulado = px.line(
                    df_pessoal_sorted,
                    x='Data',
                    y='Valor_Acumulado',
                    template='plotly_white',
                    color_discrete_sequence=['#9775fa']
                )
                
                # Adicionando os valores formatados como customdata para uso no hover
                fig_acumulado.update_traces(
                    customdata=valores_formatados
                )
                
                # Configurando o hover com textos formatados
                hovertemplate = '<b>Data:</b> %{x|%d/%m/%Y}<br><b>Valor:</b> %{customdata}<extra></extra>'
                fig_acumulado.update_traces(
                    hovertemplate=hovertemplate
                )
                
                # Configurando o eixo Y com valores em R$
                fig_acumulado.update_yaxes(
                    tickprefix="R$ ",
                    separatethousands=True
                )
                
                fig_acumulado.update_layout(
                    height=400,
                    margin=dict(t=30, b=0, l=0, r=0),
                    yaxis_title='Valor Acumulado (R$)',
                    xaxis_title='',
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)'
                )
                st.plotly_chart(fig_acumulado, use_container_width=True, config={'displayModeBar': False, 'staticPlot': True})
            else:
                st.info("Não há dados com datas válidas para exibir no período selecionado.")
        else:
            st.info("Não há dados para exibir no período selecionado.")

    # Tabela detalhada
    st.markdown('---')
    st.markdown('<h3 class="section-header">📋 Detalhamento das Despesas</h3>', unsafe_allow_html=True)
       
    df_pessoal_display = df_pessoal_filtrado.copy()
    df_pessoal_display['Data'] = df_pessoal_display['Data'].dt.strftime('%d/%m/%Y')
    df_pessoal_display['Mês'] = pd.to_datetime(df_pessoal_display['Data'], format='%d/%m/%Y', dayfirst=True).dt.strftime('%B/%Y')
    df_pessoal_display['Mês'] = df_pessoal_display['Mês'].apply(traduzir_mes)
        
    # Reordenar colunas
    df_pessoal_display = df_pessoal_display[['Data', 'Nome', 'Valor']]
    
    # Utilizando a função formatar_valor_br para formatar a coluna Valor no estilo brasileiro
    st.dataframe(
        df_pessoal_display.style
        .format({'Valor': lambda x: formatar_valor_br(x)})
        .set_properties(**{
            'color': '#2c3e50',
            'border-color': '#dee2e6'
        })
        .set_table_styles([
            {'selector': 'th', 'props': [('background-color', '#9775fa'), ('color', 'white'), ('font-weight', 'bold')]},
            {'selector': 'tr:hover', 'props': [('background-color', '#f3f0ff')]}
        ])
        .apply(lambda x: ['background-color: #f8f9fa' for _ in range(len(x))]),
        height=400,
        width=800
    )