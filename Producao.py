import pandas as pd
import numpy as np
import streamlit as st
import altair as alt
from datetime import datetime
import locale
from datetime import timedelta
import io

# Configuração da página
st.set_page_config(
    page_title="Controle de Produção BIASI",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Definição da paleta de cores da imagem
COLOR_PALETTE = ['#086788', '#07A0C3', '#F0C808', '#FFF1D0', '#DD1C1A']
PRIMARY_COLOR = '#DD1C1A'  # Cor principal para gráficos de barra

# Configuração do Altair para renderizar gráficos maiores
alt.data_transformers.disable_max_rows()

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
    
    .stMetric {
        background-color: #f8f9fa;
        padding: 1.5rem;
        border-radius: 25px;
        box-shadow: 0 8px 16px rgba(0,0,0,0.1);
    }
    
    /* Formatação para o datepicker */
    div[data-testid="stDateInput"] {
        background-color: white;
        border-radius: 0.5rem;
        padding: 0.5rem;
        box-shadow: 0 0.1rem 0.2rem rgba(0,0,0,0.05);
    }
    
    /* Estilos para categorias de produtos */
    .categoria-melado-batido {
        background-color: #FFD166;
        padding: 0.2rem 0.5rem;
        border-radius: 0.2rem;
        color: #333;
        font-weight: bold;
    }
    
    .categoria-melado-fino {
        background-color: #06D6A0;
        padding: 0.2rem 0.5rem;
        border-radius: 0.2rem;
        color: #333;
        font-weight: bold;
    }
    
    .categoria-rapadura {
        background-color: #118AB2;
        padding: 0.2rem 0.5rem;
        border-radius: 0.2rem;
        color: white;
        font-weight: bold;
    }
    
    .categoria-outro {
        background-color: #EF476F;
        padding: 0.2rem 0.5rem;
        border-radius: 0.2rem;
        color: white;
        font-weight: bold;
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

def traduzir_mes(texto):
    # Verificar se o valor é NaN ou não é uma string
    if pd.isna(texto) or not isinstance(texto, str):
        return texto
    
    # Se for string, faz a tradução
    for en, pt in meses_ptbr.items():
        texto = texto.replace(en, pt)
    return texto

# Formatação de números para o padrão brasileiro
def format_number(value):
    try:
        return locale.format_string("%.0f", value, grouping=True)
    except:
        # Se falhar, forçar o formato brasileiro manualmente
        return f"{value:,.0f}".replace(',', '.').replace('.', ',')

# Formatação de números com casas decimais para o padrão brasileiro
def format_decimal_br(value, decimal_places=2):
    """Formata um número com casas decimais no padrão brasileiro (1.234,56)"""
    # Formatar com separador de milhar (,) e casas decimais
    formatted = f"{value:,.{decimal_places}f}"
    # Substituir o separador decimal (.) por uma marca temporária
    formatted = formatted.replace('.', 'TEMP_DECIMAL')
    # Substituir o separador de milhar (,) por ponto
    formatted = formatted.replace(',', '.')
    # Substituir a marca temporária pela vírgula decimal
    formatted = formatted.replace('TEMP_DECIMAL', ',')
    return formatted

# Função para classificar produtos em categorias de forma dinâmica
def categorizar_produto(produto, df_produtos=None):
    """
    Categoriza produtos de forma automática baseado na primeira palavra significativa
    ou usando análise de frequência para identificar categorias principais.
    """
    # Se for a primeira vez que chamamos a função, criamos categorias dinâmicas
    if df_produtos is None or not hasattr(categorizar_produto, "categorias"):
        # Extrair primeiro termo de cada produto (geralmente é a categoria)
        produtos_unicos = df['Produto'].unique()
        categorias_base = {}
        
        # Extrair termos principais e contar suas ocorrências
        for prod in produtos_unicos:
            # Dividir o nome e pegar o primeiro termo significativo
            termos = prod.split()
            if len(termos) > 0:
                termo_principal = termos[0]
                
                # Incrementar contagem para este termo
                if termo_principal in categorias_base:
                    categorias_base[termo_principal] += 1
                else:
                    categorias_base[termo_principal] = 1
        
        # Filtrar apenas termos com frequência significativa (mais de uma ocorrência)
        categorias_significativas = {k: v for k, v in categorias_base.items() if v > 1}
        
        # Se não houver categorias significativas, manter pelo menos todas as encontradas
        if not categorias_significativas:
            categorias_significativas = categorias_base
        
        # Criar dicionário de mapeamento de produtos para categorias
        mapeamento_categorias = {}
        
        # Para cada produto, atribuir uma categoria baseada no termo principal 
        for prod in produtos_unicos:
            for categoria in categorias_significativas.keys():
                if categoria in prod:
                    mapeamento_categorias[prod] = categoria
                    break
            
            # Se não encontrou categoria, usar "Outro"
            if prod not in mapeamento_categorias:
                mapeamento_categorias[prod] = "Outro"
        
        # Armazenar para uso futuro
        categorizar_produto.categorias = mapeamento_categorias
    
    # Usar o mapeamento já criado
    if produto in categorizar_produto.categorias:
        return categorizar_produto.categorias[produto]
    
    # Se for um produto nunca visto antes, tenta identificar a categoria
    for categoria in set(categorizar_produto.categorias.values()):
        if categoria in produto:
            return categoria
    
    return "Outro"

# Função para extrair o tamanho/peso do produto
def extrair_tamanho(produto):
    if "kg" in produto.lower():
        # Extrair o número antes de 'kg'
        import re
        match = re.search(r'(\d+[\.,]?\d*)kg', produto, re.IGNORECASE)
        if match:
            return float(match.group(1).replace(',', '.'))
    elif "g" in produto and "kg" not in produto.lower():
        # Extrair o número antes de 'g' e converter para kg
        import re
        match = re.search(r'(\d+)g', produto)
        if match:
            return float(match.group(1)) / 1000
    
    # Se não conseguir extrair, retorna valor padrão para não quebrar cálculos
    return 1.0  # Valor padrão em kg

# Dados da planilha
@st.cache_data(ttl=300)  # Cache por 5 minutos
def load_data():
    # URL da planilha Google Sheets
    sheet_url = "https://docs.google.com/spreadsheets/d/1yBnRcKE9BpLMdjHuCkdnqR3dNm_do2a0tLylYG0ze8c/export?format=csv&gid=1843530588"
    
    try:
        # Tentar ler a planilha online
        df = pd.read_csv(sheet_url)
        return df
    except Exception as e:
        st.error(f"Erro ao ler a planilha: {e}")
        
        # Se não conseguir acessar a planilha, usa os dados locais
        try:
            df = pd.read_csv('paste.txt', sep='\t')
            return df
        except Exception as e2:
            st.error(f"Erro ao ler arquivo local: {e2}")
            return pd.DataFrame()

# Carregamento e preparação dos dados
df = load_data()

if not df.empty:
    # Assegurar que os nomes das colunas estejam corretos (caso sejam lidos do arquivo)
    if 'Data' not in df.columns and len(df.columns) >= 4:
        df.columns = ['Data', 'Produto', 'Unidades', 'Responsável Produção']
    
    # Remover linhas com valores NaN em colunas importantes
    df = df.dropna(subset=['Data', 'Produto', 'Unidades'])
    
    # Converter 'Unidades' para numérico
    df['Unidades'] = pd.to_numeric(df['Unidades'], errors='coerce')
    
    # Converter 'Data' para datetime - formato brasileiro DD/MM/YYYY
    df['Data'] = pd.to_datetime(df['Data'], format='%d/%m/%Y', errors='coerce')
    
    # Adicionar colunas derivadas
    # Primeiro aplicar a função de categorização nos dados para criar as categorias
    df['Categoria'] = df.apply(lambda row: categorizar_produto(row['Produto'], df), axis=1)
    df['Tamanho_kg'] = df['Produto'].apply(extrair_tamanho)
    
    # Adicionar coluna de mês e ano
    df['Mês'] = df['Data'].dt.month
    df['Ano'] = df['Data'].dt.year
    df['Mês_Ano'] = df['Data'].dt.strftime('%m/%Y')
    
    # Tratamento dos nomes dos meses para o português
    df['Nome_Mês'] = df['Data'].dt.strftime('%B/%Y').apply(traduzir_mes)
    
    # Calcular o total em kg para cada produto
    df['Total_kg'] = df['Unidades'] * df['Tamanho_kg']
    
    # Sidebar com filtros
    st.sidebar.title('🔍 Filtros')
    
    # Filtro de data
    st.sidebar.markdown("### 📅 Período de Análise")
    
    # Obter datas min e max do DataFrame
    data_inicial = df['Data'].min().date()
    data_final = df['Data'].max().date()
    
    datas = st.sidebar.date_input(
        "Selecione o período",
        value=(data_inicial, data_final),
        min_value=data_inicial,
        max_value=data_final,
        format="DD/MM/YYYY"
    )
    
    if len(datas) == 2:
        start_date, end_date = datas
        start_timestamp = pd.Timestamp(start_date)
        end_timestamp = pd.Timestamp(end_date)
        
        df_filtrado = df[(df['Data'] >= start_timestamp) & (df['Data'] <= end_timestamp)]
    else:
        df_filtrado = df
    
    # Filtro de categoria
    st.sidebar.markdown("### 🏷️ Categorias")
    categorias = ['Todas'] + sorted(df['Categoria'].unique().tolist())
    categoria_selecionada = st.sidebar.selectbox('Selecione a categoria:', categorias)
    
    if categoria_selecionada != 'Todas':
        df_filtrado = df_filtrado[df_filtrado['Categoria'] == categoria_selecionada]
    
    # Filtro de produto
    st.sidebar.markdown("### 📦 Produtos")
    produtos = ['Todos'] + sorted(df_filtrado['Produto'].unique().tolist())
    produto_selecionado = st.sidebar.selectbox('Selecione o produto:', produtos)
    
    if produto_selecionado != 'Todos':
        df_filtrado = df_filtrado[df_filtrado['Produto'] == produto_selecionado]
    
    # Filtro de responsável
    st.sidebar.markdown("### 👤 Responsável")
    responsaveis = ['Todos'] + sorted(df_filtrado['Responsável Produção'].unique().tolist())
    responsavel_selecionado = st.sidebar.selectbox('Selecione o responsável:', responsaveis)
    
    if responsavel_selecionado != 'Todos':
        df_filtrado = df_filtrado[df_filtrado['Responsável Produção'] == responsavel_selecionado]
    
    # Título principal
    st.markdown('<h1 class="section-header">🏭 Análise de Produção BIASI</h1>', unsafe_allow_html=True)
    
    # Métricas principais
    col1, col2, col3, col4 = st.columns(4)
    
    total_unidades = df_filtrado['Unidades'].sum()
    total_kg = df_filtrado['Total_kg'].sum()
    media_diaria = df_filtrado.groupby('Data')['Unidades'].sum().mean()
    total_produtos = df_filtrado['Produto'].nunique()
    
    with col1:
        st.metric(
            label="Total de Unidades Produzidas",
            value=format_number(total_unidades)
        )
    
    with col2:
        st.metric(
            label="Total em Quilogramas",
            value=format_decimal_br(total_kg) + " kg"
        )
    
    with col3:
        st.metric(
            label="Média Diária de Produção",
            value=format_number(media_diaria)
        )
    
    with col4:
        st.metric(
            label="Variedade de Produtos",
            value=total_produtos
        )
    
    st.markdown('---')
    
    # Gráficos em abas
    tab1, tab2, tab3 = st.tabs(["📊 Produção por Produto", "📈 Evolução Temporal", "🔄 Comparativos"])
    
    # Tab 1 - Produção por Produto
    with tab1:
        st.markdown('<h2 class="section-header">📊 Produção por Produto</h2>', unsafe_allow_html=True)
        
        # Gráfico: Total de unidades por produto
        producto_df = df_filtrado.groupby('Produto')['Unidades'].sum().reset_index()
        producto_df = producto_df.sort_values(by="Unidades", ascending=False)  # Ordem decrescente
        
        # Manter a ordem original no dataframe (importante para o Altair respeitar)
        producto_df['ordem'] = range(len(producto_df))
        
        # Calcular o tamanho relativo para posicionamento do texto
        producto_df['tamanho_relativo'] = producto_df['Unidades'] / producto_df['Unidades'].max()
        
        # Criar um campo personalizado para ordenação
        domain = producto_df['Produto'].tolist()
        
        # Criar gráfico base e as barras
        chart_produto = alt.Chart(producto_df).mark_bar(color=PRIMARY_COLOR).encode(
            y=alt.Y('Produto:N', sort=domain, title='Produto'),
            x=alt.X('Unidades:Q', title='Total de Unidades'),
            tooltip=['Produto', 'Unidades']
        )
        
        # Texto para barras
        text_grandes = alt.Chart(producto_df).mark_text(
            align='left',
            baseline='middle',
            dx=15,
            color='red',
            fontSize=14,
            fontWeight='bold'
        ).encode(
            y=alt.Y('Produto:N', sort=domain),
            x='Unidades:Q',
            text=alt.Text('Unidades:Q', format=',')
        )
        
        # Combinar e configurar
        chart_final_produto = (chart_produto + text_grandes).properties(
            height=500
        ).configure_view(
            strokeWidth=0
        ).configure_axis(
            grid=False
        )
        
        st.altair_chart(chart_final_produto, use_container_width=True)
    
    # Tab 2 - Evolução Temporal
    with tab2:
        st.markdown('<h2 class="section-header">📈 Evolução da Produção</h2>', unsafe_allow_html=True)
        c1,c2 = st.columns(2)
        # Análise por mês - apenas com meses que realmente têm dados
        c1.markdown('<h3 class="section-header">Evolução Mensal</h3>', unsafe_allow_html=True)
        
        # Criar um grupo único de mês e ano para agrupar corretamente
        df_filtrado['MesAno_Key'] = df_filtrado['Data'].dt.strftime('%Y-%m')
        
        # Agrupar por mês e ano
        df_por_mes = df_filtrado.groupby('MesAno_Key').agg({
            'Unidades': 'sum',
            'Total_kg': 'sum',
            'Nome_Mês': 'first'  # Pegamos o nome do mês traduzido
        }).reset_index()
        
        # Ordenar corretamente pelo período
        df_por_mes = df_por_mes.sort_values('MesAno_Key')
        
        # Calcular média móvel se tivermos mais de um mês
        if len(df_por_mes) > 1:
            df_por_mes['Media_Movel'] = df_por_mes['Unidades'].rolling(window=min(2, len(df_por_mes)), min_periods=1).mean()
        
        # Criamos o gráfico apenas se tivermos dados
        if len(df_por_mes) > 0:
            # Gráfico de barras para unidades por mês
            chart_bar_mes = alt.Chart(df_por_mes).mark_bar(color=COLOR_PALETTE[2]).encode(
                x=alt.X('Nome_Mês:N', title='Mês', sort=None),  # sort=None para preservar a ordem
                y=alt.Y('Unidades:Q', title='Total de Unidades'),
                tooltip=['Nome_Mês', 'Unidades']
            )
            
            # Adicionar linha para média móvel se tivermos mais de um mês
            if 'Media_Movel' in df_por_mes.columns and len(df_por_mes) > 1:
                chart_line_mes = alt.Chart(df_por_mes).mark_line(
                    color=COLOR_PALETTE[0], 
                    point=True
                ).encode(
                    x=alt.X('Nome_Mês:N', sort=None),
                    y=alt.Y('Media_Movel:Q'),
                    tooltip=['Nome_Mês', 'Media_Movel']
                )
                
                # Combinar barras e linha
                chart_mes = (chart_bar_mes + chart_line_mes).properties(
                    height=400
                ).configure_view(
                    strokeWidth=0
                )
            else:
                chart_mes = chart_bar_mes.properties(
                    height=400
                ).configure_view(
                    strokeWidth=0
                )
            
            c1.altair_chart(chart_mes, use_container_width=True)
        
        # Produção acumulada
        c2.markdown('<h3 class="section-header">Produção Acumulada</h3>', unsafe_allow_html=True)

        # Agrupar dados por data
        df_por_data = df_filtrado.groupby('Data')[['Unidades', 'Total_kg']].sum().reset_index()

        # Ordenar por data para o acumulado correto
        df_por_data = df_por_data.sort_values('Data')

        # Calcular acumulado
        df_por_data['Unidades_Acumulado'] = df_por_data['Unidades'].cumsum()
        df_por_data['Kg_Acumulado'] = df_por_data['Total_kg'].cumsum()

        # Gráfico de área para produção acumulada
        chart_acumulado = alt.Chart(df_por_data).mark_area(
            color=COLOR_PALETTE[1],
            opacity=0.7
        ).encode(
            x=alt.X('Data:T', title='Data', axis=alt.Axis(format='%d/%m/%y')),
            y=alt.Y('Unidades_Acumulado:Q', title='Unidades Acumuladas'),
            tooltip=['Data', 'Unidades_Acumulado']
        ).properties(
            height=400
        )

        c2.altair_chart(chart_acumulado, use_container_width=True)
        
        # Grafico produção diaria
        st.markdown('<h3 class="section-header">Produção Diária</h3>', unsafe_allow_html=True)

        # Agrupar dados por data
        df_diario = df_filtrado.groupby('Data')[['Unidades', 'Total_kg']].sum().reset_index()

        # Ordenar por data
        df_diario = df_diario.sort_values('Data')

        # Gráfico de linha com curvas suaves para produção diária
        chart_diario = alt.Chart(df_diario).mark_area(
            point=False,  # Adiciona pontos nos dados
            strokeWidth=3,  # Espessura da linha
            color=COLOR_PALETTE[4],
            opacity=0.3,
            line={
                'color': COLOR_PALETTE[4],  # Cor da linha
                'strokeWidth': 2  # Espessura da linha
            },
            interpolate='monotone'  # Tipo de interpolação para curvas suaves
        ).encode(
            x=alt.X('Data:T', title='Data', axis=alt.Axis(format='%d/%m/%y')),
            y=alt.Y('Unidades:Q', title='Unidades Produzidas'),
            tooltip=['Data:T', 'Unidades:Q']
        ).properties(
            height=400
        )

        # Combinar os gráficos
        chart_final_diario = (chart_diario)

        st.altair_chart(chart_final_diario, use_container_width=True)
    
    # Tab 3 - Comparativos
    with tab3:
        st.markdown('<h2 class="section-header">🔄 Análises Comparativas</h2>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Produtos mais produzidos (top 5)
            st.markdown('<h3 class="section-header">Top 5 Produtos Mais Produzidos</h3>', unsafe_allow_html=True)
            
            # Preparar dados para os top 5 produtos
            top_produtos_df = df_filtrado.groupby('Produto')['Unidades'].sum().nlargest(5).reset_index()
            top_produtos_df = top_produtos_df.sort_values(by='Unidades', ascending=True)  # Ordenar ascendente para o gráfico
            
            # Gráfico de barras horizontais para top 5 produtos
            base_top = alt.Chart(top_produtos_df).encode(
                y=alt.Y('Produto:N', sort='-x', title=''),
                x=alt.X('Unidades:Q', title='Unidades'),
                tooltip=['Produto', 'Unidades']
            )
            
            # Barras
            bars_top = base_top.mark_bar(color=COLOR_PALETTE[4])
            
            # Texto nas barras
            text_top = base_top.mark_text(
                align='left',
                baseline='middle',
                dx=3,
                color='white'
            ).encode(
                text=alt.Text('Unidades:Q', format=',')
            )
            
            chart_top_final = (bars_top + text_top).properties(
                height=400
            ).configure_view(
                strokeWidth=0
            )
            
            st.altair_chart(chart_top_final, use_container_width=True)
        
        with col2:
            # Distribuição por dia da semana
            st.markdown('<h3 class="section-header">Produção por Dia da Semana</h3>', unsafe_allow_html=True)
            
            # Adicionar dia da semana
            df_weekday = df_filtrado.copy()
            df_weekday['Dia_Semana'] = df_weekday['Data'].dt.day_name()
            
            # Mapear para nomes em português
            dias_semana = {
                'Monday': 'Segunda-feira',
                'Tuesday': 'Terça-feira',
                'Wednesday': 'Quarta-feira',
                'Thursday': 'Quinta-feira',
                'Friday': 'Sexta-feira',
                'Saturday': 'Sábado',
                'Sunday': 'Domingo'
            }
            
            df_weekday['Dia_Semana_PT'] = df_weekday['Dia_Semana'].map(dias_semana)
            
            # Ordem correta dos dias da semana
            ordem_dias = ['Segunda-feira', 'Terça-feira', 'Quarta-feira', 'Quinta-feira', 'Sexta-feira', 'Sábado', 'Domingo']
            
            # Agrupar por dia da semana
            dia_semana_df = df_weekday.groupby('Dia_Semana_PT')['Unidades'].sum().reset_index()
            
            # Remover dias da semana sem produção
            dia_semana_df = dia_semana_df[dia_semana_df['Dia_Semana_PT'].isin(ordem_dias)]
            
            # Criar mapeamento de cores por dia da semana
            dia_semana_df['order'] = dia_semana_df['Dia_Semana_PT'].apply(lambda x: ordem_dias.index(x) if x in ordem_dias else 999)
            dia_semana_df = dia_semana_df.sort_values('order')
            dia_semana_df['color'] = [COLOR_PALETTE[i % len(COLOR_PALETTE)] for i in range(len(dia_semana_df))]
            
            # Gráfico de barras para dias da semana
            chart_weekday = alt.Chart(dia_semana_df).mark_bar().encode(
                x=alt.X('Dia_Semana_PT:N', sort=ordem_dias, title=''),
                y=alt.Y('Unidades:Q', title='Unidades'),
                color=alt.Color('Dia_Semana_PT:N', scale=alt.Scale(domain=dia_semana_df['Dia_Semana_PT'].tolist(), 
                                                                  range=dia_semana_df['color'].tolist())),
                tooltip=['Dia_Semana_PT', 'Unidades']
            ).properties(
                height=400
            )
            
            # Adicionar rótulos de texto
            text_weekday = alt.Chart(dia_semana_df).mark_text(
                align='center',
                baseline='bottom',
                dy=-5
            ).encode(
                x=alt.X('Dia_Semana_PT:N', sort=ordem_dias),
                y=alt.Y('Unidades:Q'),
                text=alt.Text('Unidades:Q', format=',')
            )
            
            chart_weekday_final = (chart_weekday + text_weekday).properties(
                height=400
            ).configure_view(
                strokeWidth=0
            ).configure_legend(
                disable=True  # Remover a legenda
            )
            
            st.altair_chart(chart_weekday_final, use_container_width=True)
        
        # Análise por responsável
        st.markdown('<h3 class="section-header">Produção por Responsável</h3>', unsafe_allow_html=True)
        
        # Agrupar por responsável
        resp_sum = df_filtrado.groupby('Responsável Produção')[['Unidades', 'Total_kg']].sum().reset_index()
        
        # Calcular percentagens para o gráfico de pizza
        total_unidades = resp_sum['Unidades'].sum()
        resp_sum['Percentual'] = resp_sum['Unidades'] / total_unidades * 100
        
        # Criar campo para formatar texto no tooltip
        resp_sum['Percentual_Formatado'] = resp_sum['Percentual'].apply(lambda x: f'{x:.1f}%')
        resp_sum['Unidades_Formatadas'] = resp_sum['Unidades'].apply(lambda x: format_number(x))
        
        # Criar gráfico de pizza usando mark_arc (sem calculador ângulos manualmente)
        pie_chart = alt.Chart(resp_sum).mark_arc(innerRadius=50).encode(
            theta=alt.Theta('Unidades:Q'),
            color=alt.Color('Responsável Produção:N', scale=alt.Scale(range=COLOR_PALETTE)),
            tooltip=[
                alt.Tooltip('Responsável Produção:N', title='Responsável'),
                alt.Tooltip('Unidades_Formatadas:N', title='Unidades'),
                alt.Tooltip('Percentual_Formatado:N', title='Percentual')
            ]
        ).properties(
            height=400
        )
        
        # Adicionar texto para os valores
        text_pie = alt.Chart(resp_sum).mark_text(radius=90).encode(
            theta=alt.Theta('Unidades:Q', stack=True),
            text=alt.Text('Percentual_Formatado:N'),
            color=alt.value('white')
        )
        
        # Combinar o gráfico
        chart_resp_final = (pie_chart + text_pie)
        
        st.altair_chart(chart_resp_final, use_container_width=True)
        
        # Comparativo de eficiência por categoria e responsável
        st.markdown('<h3 class="section-header">Eficiência por Categoria e Responsável</h3>', unsafe_allow_html=True)
        
        # Calcular médias diárias por responsável e categoria
        df_eficiencia = df_filtrado.groupby(['Responsável Produção', 'Categoria', 'Data']).agg({
            'Unidades': 'sum',
            'Total_kg': 'sum'
        }).reset_index()
        
        df_eficiencia_media = df_eficiencia.groupby(['Responsável Produção', 'Categoria']).agg({
            'Unidades': 'mean',
            'Total_kg': 'mean',
            'Data': 'count'
        }).reset_index()
        
        df_eficiencia_media = df_eficiencia_media.rename(columns={
            'Unidades': 'Média_Unidades_Diária',
            'Total_kg': 'Média_kg_Diária',
            'Data': 'Dias_Trabalhados'
        })
        
        # Arredondar valores para facilitar a visualização
        df_eficiencia_media['Média_Unidades_Diária'] = df_eficiencia_media['Média_Unidades_Diária'].round(1)
        
        # Gráfico de barras agrupadas (versão corrigida sem faceting)
        chart_efic = alt.Chart(df_eficiencia_media).mark_bar().encode(
            x=alt.X('Categoria:N', title=''),
            y=alt.Y('Média_Unidades_Diária:Q', title='Média Diária (Unidades)'),
            color=alt.Color('Responsável Produção:N', scale=alt.Scale(range=COLOR_PALETTE)),
            xOffset='Responsável Produção:N',  # Usar xOffset para agrupar barras lado a lado
            tooltip=[
                'Categoria', 
                'Responsável Produção', 
                alt.Tooltip('Média_Unidades_Diária:Q', title='Média Diária'), 
                alt.Tooltip('Dias_Trabalhados:Q', title='Dias Trabalhados')
            ]
        ).properties(
            height=400
        )
        
        # Adicionar texto às barras
        text_efic = alt.Chart(df_eficiencia_media).mark_text(
            align='center',
            baseline='middle',
            dy=-10
        ).encode(
            x=alt.X('Categoria:N'),
            y=alt.Y('Média_Unidades_Diária:Q'),
            text=alt.Text('Média_Unidades_Diária:Q', format='.1f'),
            xOffset='Responsável Produção:N'  # Alinhar texto com as barras
        )
        
        # Combinar e configurar
        chart_efic_final = (chart_efic + text_efic).configure_view(
            strokeWidth=0
        ).configure_legend(
            symbolType='circle'  # Alterar formato da legenda para círculo
        )
        
        st.altair_chart(chart_efic_final, use_container_width=True)
    
    # Tabela detalhada
    st.markdown('---')
    st.markdown('<h2 class="section-header">📋 Detalhamento da Produção</h2>', unsafe_allow_html=True)
    
    # Opções para visualização
    detalhamento = st.radio(
        "Selecione o tipo de detalhamento:",
        ["Por Produto", "Por Data", "Por Responsável", "Dados Completos"],
        key="detalhamento_final"
    )
    
    if detalhamento == "Por Produto":
        # Agrupar dados por produto
        df_detalhado = df_filtrado.groupby('Produto').agg({
            'Unidades': 'sum',
            'Total_kg': 'sum',
            'Data': ['min', 'max', 'count']
        }).reset_index()
        
        # Renomear colunas
        df_detalhado.columns = ['Produto', 'Total Unidades', 'Total kg', 'Primeira Produção', 'Última Produção', 'Dias Produzidos']
        
        # Formatar datas
        df_detalhado['Primeira Produção'] = df_detalhado['Primeira Produção'].dt.strftime('%d/%m/%Y')
        df_detalhado['Última Produção'] = df_detalhado['Última Produção'].dt.strftime('%d/%m/%Y')
        
        # Ordenar por unidades
        df_detalhado = df_detalhado.sort_values('Total Unidades', ascending=False)
        
        # Aplicar estilização
        st.dataframe(
            df_detalhado,
            use_container_width=True,
            height=400
        )
        
    elif detalhamento == "Por Data":
        # Agrupar dados por data
        df_detalhado = df_filtrado.groupby('Data').agg({
            'Unidades': 'sum',
            'Total_kg': 'sum',
            'Produto': 'nunique',
            'Categoria': lambda x: ', '.join(sorted(set(x)))
        }).reset_index()
        
        # Renomear colunas
        df_detalhado.columns = ['Data', 'Total Unidades', 'Total kg', 'Qtde. Produtos', 'Categorias']
        
        # Formatar data
        df_detalhado['Data'] = df_detalhado['Data'].dt.strftime('%d/%m/%Y')
        
        # Ordenar por data (decrescente)
        df_detalhado = df_detalhado.sort_values('Data', ascending=False)
        
        # Aplicar estilização
        st.dataframe(
            df_detalhado,
            use_container_width=True,
            height=400
        )
        
    elif detalhamento == "Por Responsável":
        # Agrupar dados por responsável
        df_detalhado = df_filtrado.groupby('Responsável Produção').agg({
            'Unidades': 'sum',
            'Total_kg': 'sum',
            'Data': 'nunique',
            'Produto': lambda x: ', '.join(sorted(set(x))[:3]) + ('...' if len(set(x)) > 3 else '')
        }).reset_index()
        
        # Renomear colunas
        df_detalhado.columns = ['Responsável', 'Total Unidades', 'Total kg', 'Dias Trabalhados', 'Principais Produtos']
        
        # Ordenar por unidades
        df_detalhado = df_detalhado.sort_values('Total Unidades', ascending=False)
        
        # Aplicar estilização
        st.dataframe(
            df_detalhado,
            use_container_width=True,
            height=400
        )
        
    else:  # Dados Completos
        # Selecionar colunas relevantes
        df_detalhado = df_filtrado[['Data', 'Produto', 'Categoria', 'Unidades', 'Tamanho_kg', 'Total_kg', 'Responsável Produção']]
        
        # Formatar data
        df_detalhado['Data'] = df_detalhado['Data'].dt.strftime('%d/%m/%Y')
        
        # Ordenar por data (decrescente)
        df_detalhado = df_detalhado.sort_values('Data', ascending=False)
        
        # Aplicar estilização
        st.dataframe(
            df_detalhado,
            use_container_width=True,
            height=400
        )
    
    # Exportar para CSV
    csv = df_filtrado.to_csv(index=False).encode('utf-8')
    st.markdown('---')
    st.download_button(
        label="📥 Baixar Dados Filtrados (CSV)",
        data=csv,
        file_name=f"producao_biasi_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv",
    )
    
    # Nota de rodapé
    st.markdown("---")
    st.caption("Dados atualizados automaticamente da planilha do Google Sheets. Última atualização: " + datetime.now().strftime('%d/%m/%Y %H:%M:%S'))

else:
    st.error("Não foi possível carregar os dados. Verifique a URL da planilha ou sua conexão de internet.")
    