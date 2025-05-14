import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import re
from datetime import datetime

# Paleta de cores personalizada
COLOR_PALETTE = ['#086788', '#07A0C3', '#F0C808', '#FFF1D0', '#DD1C1A']

# Configuração da página
st.set_page_config(
    page_title='Análise Financeira',
    page_icon='💰',
    layout='wide'
)

# URL da planilha
sheet_url = "https://docs.google.com/spreadsheets/d/106cKYOMqz5Zn1adQBLRvBFHwWqkmHA1Tlv4jLYNTcVs/export?format=csv&gid=0"

# Estilo CSS - apenas para elementos não críticos
st.markdown("""
<style>
    .main {
        padding: 2rem;
    }
    
    header {
         visibility: hidden;
        }        

    .stMetric {
        background-color: #f8f9fa;
        padding: 1.5rem;
        border-radius: 25px;
        box-shadow: 0 8px 16px rgba(0,0,0,0.1);
    }
    
    .stProgress {
        background-color: rgba(28, 225, 117, 0.18);
        padding: 1.5rem;
        border-radius: 25px;
        border: 1px solid green;    
        box-shadow: 0 8px 16px rgba(0,0,0,0.1);
    }
    
    h1 {
        color: #086788;
        padding-bottom: 1rem;
    }
    
    h2 {
        color: #333;
        padding: 1rem 0;
    }
    
    .pending-payment {
        color: #DD1C1A;
        font-weight: bold;
    }
    
    .section-title {
        color: #086788;
        font-size: 1.5rem;
        font-weight: 600;
        margin: 2rem 0 1rem 0;
        padding-bottom: 0.5rem;
        border-bottom: 1px solid #e0e0e0;
    }
    
    .timeline-container {
        margin-top: 20px;
        padding: 20px;
        background-color: white;
        border-radius: 10px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    
    .bank-badge {
        display: inline-block;
        padding: 3px 8px;
        border-radius: 12px;
        font-size: 0.7rem;
        margin-left: 8px;
        background-color: #07A0C3;
        color: white;
    }
    
    /* Removido o estilo card-column que não será mais usado */
</style>
""", unsafe_allow_html=True)

# Função para converter string para float
def converter_para_float(valor):
    if pd.isna(valor) or valor == '':
        return 0.0
        
    if isinstance(valor, (int, float)):
        return float(valor)
        
    # Se for string, limpar e converter
    if isinstance(valor, str):
        # Remover R$, espaços, pontos e substituir vírgula por ponto
        valor_limpo = valor.replace('R$', '').replace(' ', '').strip()
        
        # Verificar se há caracteres não numéricos (exceto ponto, vírgula e sinal)
        if re.search(r'[^\d.,\-+]', valor_limpo):
            # Tentar extrair o valor numérico
            match = re.search(r'[\d.,]+', valor_limpo)
            if match:
                valor_limpo = match.group(0)
            else:
                return 0.0
            
        # Substituir pontos por nada e vírgulas por pontos (formato brasileiro)
        if ',' in valor_limpo:
            valor_limpo = valor_limpo.replace('.', '').replace(',', '.')
        
        try:
            return float(valor_limpo)
        except:
            return 0.0
            
    return 0.0

# Função para formatar valor como moeda brasileira
def formatar_moeda(valor):
    try:
        if valor == 0:
            return "R$ 0,00"
        return f"R$ {valor:,.2f}".replace(',', '_').replace('.', ',').replace('_', '.')
    except:
        return "R$ 0,00"

# Função para ler dados
@st.cache_data(ttl=300)  # Cache por 5 minutos
def carregar_dados(url):
    try:
        # Tentar diferentes separadores
        separadores = [';', ',', '\t']
        
        for sep in separadores:
            try:
                df = pd.read_csv(url, sep=sep)
                # Se temos mais de uma coluna, provavelmente o separador está correto
                if len(df.columns) > 1:
                    return df
            except:
                continue
        
        # Se nenhum separador funcionou, tentar detecção automática
        return pd.read_csv(url, sep=None, engine='python')
    except Exception as e:
        st.error(f"Erro ao carregar os dados: {e}")
        return pd.DataFrame()

# Função para processar dados
def processar_dados(df):
    if df.empty:
        return df
        
    # Remover linhas vazias
    df = df.dropna(how='all').reset_index(drop=True)
    
    # Identificar colunas esperadas
    colunas_esperadas = {
        'descricao': 'Descrição',
        'valor_total': 'Valor Total',
        'valor_a_pagar': 'Valor A Pagar',
        'parcelas': 'Número Total de Parcelas',
        'ano_aquisicao': 'Ano de aquisição',
        'ano_quitacao': 'Ano quitação',
        'banco': 'Banco'
    }
    
    # Normalizar nomes das colunas
    df.columns = [col.lower().strip() for col in df.columns]
    
    # Mapear colunas para nomes padrão
    for padrao, nome_padrao in colunas_esperadas.items():
        for col in df.columns:
            col_normalizada = col.lower().replace(' ', '_').replace('ç', 'c').replace('ã', 'a')
            if padrao in col_normalizada:
                df = df.rename(columns={col: nome_padrao})
                break
    
    # Garantir que as colunas necessárias existam
    for nome_coluna in colunas_esperadas.values():
        if nome_coluna not in df.columns:
            df[nome_coluna] = np.nan
    
    # Tratar casos especiais como "DucatoR$ 72.625,60"
    for idx, row in df.iterrows():
        for col in df.columns:
            if isinstance(row[col], str) and 'R$' in row[col] and col == 'Descrição':
                partes = row[col].split('R$')
                if len(partes) > 1:
                    df.at[idx, 'Descrição'] = partes[0].strip()
                    
                    # Se houver valor monetário na descrição, mover para a coluna apropriada
                    if pd.isna(row['Valor Total']) or row['Valor Total'] == 0:
                        df.at[idx, 'Valor Total'] = converter_para_float(f"R${partes[1]}")
    
    # Converter colunas numéricas
    for col in ['Valor Total', 'Valor A Pagar']:
        df[col] = df[col].apply(converter_para_float)
    
    # Converter colunas de parcelas e anos
    for col in ['Número Total de Parcelas', 'Ano de aquisição', 'Ano quitação']:
        try:
            df[col] = pd.to_numeric(df[col], errors='coerce')
            df[col] = df[col].fillna(datetime.now().year).astype(int)  # Usar ano atual como padrão
        except:
            df[col] = datetime.now().year
    
    # Calcular valor da parcela
    df['Valor da Parcela'] = df.apply(
        lambda row: row['Valor Total'] / row['Número Total de Parcelas'] 
        if row['Número Total de Parcelas'] > 0 else row['Valor Total'], 
        axis=1
    )
    
    # Calcular percentual a pagar (com base no valor a pagar, não em parcelas)
    df['Percentual Pago'] = df.apply(
        lambda row: (1 - (row['Valor A Pagar'] / row['Valor Total'])) * 100 
        if row['Valor Total'] > 0 else 0, 
        axis=1
    )
    
    # Status com base no valor a pagar
    df['Status'] = df.apply(
        lambda row: 'QUITADO' if row['Valor A Pagar'] <= 0 or row['Percentual Pago'] >= 99.9 else 'EM ANDAMENTO', 
        axis=1
    )
    
    # Calcular anos restantes
    df['Anos Restantes'] = df.apply(
        lambda row: max(0, row['Ano quitação'] - datetime.now().year) if row['Status'] == 'EM ANDAMENTO' else 0,
        axis=1
    )
    
    # Garantir que anos de aquisição não sejam zerados
    ano_atual = datetime.now().year
    df.loc[df['Ano de aquisição'] <= 0, 'Ano de aquisição'] = ano_atual
    df.loc[df['Ano quitação'] <= 0, 'Ano quitação'] = ano_atual + 1
    
    # Garantir que ano de quitação não seja anterior ao de aquisição
    df.loc[df['Ano quitação'] < df['Ano de aquisição'], 'Ano quitação'] = df['Ano de aquisição'] + 1
    
    return df

# Função para exibir card de financiamento usando componentes nativos
def exibir_card_financiamento(container, row):
    # Calcular valor pago
    valor_pago = row['Valor Total'] - row['Valor A Pagar']
    
    # Adicionar fundo de card usando componentes nativos
    with container.container():
        # Título e status
        title_col, status_col = container.columns([3, 1])
        with title_col:
            container.markdown(f"### {row['Descrição']}")
        
        with status_col:
            status_text = "🔵 QUITADO" if row['Status'] == 'QUITADO' else "🔷 EM ANDAMENTO"
            container.markdown(f"**{status_text}**")
    
    # Informações básicas
    container.markdown(
        f"**Banco:** {row['Banco'] if not pd.isna(row['Banco']) else 'Não informado'} | "
        f"**Aquisição:** {int(row['Ano de aquisição'])} | "
        f"**Quitação:** {int(row['Ano quitação'])}"
    )
    
    # Valores principais - 3 colunas
    val_col1, val_col2, val_col3 = container.columns(3)
    
    with val_col1:
        container.markdown("<small style='color: #555;'>Valor Total</small>", unsafe_allow_html=True)
        container.markdown(f"<b style='font-size: 1.1rem;'>{formatar_moeda(row['Valor Total'])}</b>", unsafe_allow_html=True)
    
    with val_col2:
        container.markdown("<small style='color: #555;'>Valor Pago</small>", unsafe_allow_html=True)
        container.markdown(f"<b style='font-size: 1.1rem; color: {COLOR_PALETTE[1]};'>{formatar_moeda(valor_pago)}</b>", unsafe_allow_html=True)
    
    with val_col3:
        container.markdown("<small style='color: #555;'>Valor a Pagar</small>", unsafe_allow_html=True)
        container.markdown(f"<b style='font-size: 1.1rem; color: {COLOR_PALETTE[4]};'>{formatar_moeda(row['Valor A Pagar'])}</b>", unsafe_allow_html=True)
    
    # Parcelas - 2 colunas
    parc_col1, parc_col2 = container.columns(2)
    
    with parc_col1:
        container.markdown("<small style='color: #555;'>Total de Parcelas</small>", unsafe_allow_html=True)
        container.markdown(f"<b style='font-size: 1.1rem;'>{int(row['Número Total de Parcelas'])}</b>", unsafe_allow_html=True)
    
    with parc_col2:
        container.markdown("<small style='color: #555;'>Valor da Parcela</small>", unsafe_allow_html=True)
        container.markdown(f"<b style='font-size: 1.1rem;'>{formatar_moeda(row['Valor da Parcela'])}</b>", unsafe_allow_html=True)
    
    # Barra de progresso
    container.progress(float(row['Percentual Pago']/100), f"{row['Percentual Pago']:.1f}% Concluído")

# Função principal
def main():
    # Título da página
    st.title('💰 Dashboard Financeiro - Análise de Financiamentos')
    
    # Carregar dados
    with st.spinner('Carregando dados...'):
        df_raw = carregar_dados(sheet_url)
        
        if df_raw.empty:
            st.error("Não foi possível carregar os dados. Verifique a URL da planilha.")
            return
    
    # Processar dados
    df = processar_dados(df_raw)
    
    if df.empty:
        st.error("Erro ao processar os dados.")
        return
    
    # Dados de debug na barra lateral - REMOVIDO
    # with st.sidebar:
    #     st.subheader("Opções de Debug")
    #     
    #     if st.checkbox("Mostrar dados brutos"):
    #         st.write("Dados Originais")
    #         st.dataframe(df_raw)
    #         
    #     if st.checkbox("Mostrar dados processados"):
    #         st.write("Dados Processados")
    #         st.dataframe(df)
    
    # Cálculos gerais
    total_valor = df['Valor Total'].sum()
    total_a_pagar = df['Valor A Pagar'].sum()
    total_pago = total_valor - total_a_pagar
    pct_pago = (total_pago / total_valor * 100) if total_valor > 0 else 0
    
    # Visão Geral - Métricas no estilo do exemplo original
    st.header('Visão Geral')
    
    col1, col2, col3, col4 = st.columns(4)
    
    col1.metric('💼 Total de Financiamentos', formatar_moeda(total_valor))
    col2.metric('🟢 Total Pago', formatar_moeda(total_pago))
    col3.metric('🔴 Total a Pagar', formatar_moeda(total_a_pagar))
    col4.metric('📊 Percentual Pago', f"{pct_pago:.1f}%")
    
    # Tabs para análises diferentes
    st.markdown('<div class="section-title">Análise Detalhada</div>', unsafe_allow_html=True)
    
    tabs = st.tabs(["Por Banco", "Por Financiamento", "Projeções Anuais"])
    
    # Tab 1: Análise por Banco
    with tabs[0]:
        if 'Banco' in df.columns and not df['Banco'].isna().all():
            # Preencher valores NaN na coluna Banco
            df['Banco'] = df['Banco'].fillna('Não informado')
            
            # Agrupar por banco
            bancos_df = df.groupby('Banco').agg({
                'Valor Total': 'sum',
                'Valor A Pagar': 'sum',
                'Descrição': 'count'
            }).reset_index()
            
            # Calcular valor pago
            bancos_df['Valor Pago'] = bancos_df['Valor Total'] - bancos_df['Valor A Pagar']
            
            # Adicionar percentual pago
            bancos_df['Percentual Pago'] = bancos_df.apply(
                lambda row: (row['Valor Pago'] / row['Valor Total'] * 100) if row['Valor Total'] > 0 else 0,
                axis=1
            )
            
            # Renomear coluna de contagem
            bancos_df = bancos_df.rename(columns={'Descrição': 'Quantidade'})
            
            # Gráficos lado a lado
            col1, col2 = st.columns(2)
            
            with col1:
                # Gráfico de pizza para distribuição total
                fig = px.pie(
                    bancos_df, 
                    values='Valor Total', 
                    names='Banco',
                    title='Distribuição do Valor Total por Banco',
                    color_discrete_sequence=COLOR_PALETTE
                )
                
                fig.update_traces(textposition='inside', textinfo='percent+label')
                
                fig.update_layout(
                    height=400,
                    margin=dict(t=30, b=0, l=0, r=0)
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
            with col2:
                # Gráfico de barras empilhadas
                fig = go.Figure()
                
                fig.add_trace(go.Bar(
                    name='Pago',
                    x=bancos_df['Banco'],
                    y=bancos_df['Valor Pago'],
                    marker_color=COLOR_PALETTE[2]  # Amarelo para valores pagos
                ))
                
                fig.add_trace(go.Bar(
                    name='A Pagar',
                    x=bancos_df['Banco'],
                    y=bancos_df['Valor A Pagar'],
                    marker_color=COLOR_PALETTE[4]  # Vermelho para valores a pagar
                ))
                
                fig.update_layout(
                    barmode='stack',
                    title='Composição dos Financiamentos por Banco',
                    height=400,
                    margin=dict(t=30, b=0, l=0, r=0),
                    yaxis=dict(title='Valor (R$)'),
                    legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1)
                )
                
                # Formatando eixo Y
                fig.update_yaxes(tickprefix='R$ ', tickformat=',.0f')
                
                st.plotly_chart(fig, use_container_width=True)
            
            # Cards para cada banco
            st.subheader("Detalhamento por Banco")
            
            # Dividir em três colunas
            col1, col2, col3 = st.columns(3)
            
            for i, (_, row) in enumerate(bancos_df.iterrows()):
                # Distribuir entre três colunas (0->col1, 1->col2, 2->col3, 3->col1, etc.)
                if i % 3 == 0:
                    col = col1
                elif i % 3 == 1:
                    col = col2
                else:
                    col = col3
                
                with col:
                    # Usar métrica do Streamlit
                    col.metric(f"🏦 {row['Banco']}", 
                             formatar_moeda(row['Valor Total']), 
                             f"{row['Percentual Pago']:.1f}% Pago")
                    
                    # Informações adicionais
                    info_cols = col.columns(2)
                    with info_cols[0]:
                        st.markdown(f"**Pago:** {formatar_moeda(row['Valor Pago'])}")
                    with info_cols[1]:
                        st.markdown(f"**A Pagar:** {formatar_moeda(row['Valor A Pagar'])}")
                    
                    # Barra de progresso
                    col.progress(float(row['Percentual Pago']/100))
                    
                    # Quantidade de financiamentos
                    col.markdown(f"**Quantidade de Financiamentos:** {int(row['Quantidade'])}")
                    col.markdown("---")
        else:
            st.info("Informações por banco não disponíveis nos dados.")
    
    # Tab 2: Análise por Financiamento
    with tabs[1]:
        # Filtro de banco se disponível
        if 'Banco' in df.columns and not df['Banco'].isna().all():
            bancos = ['Todos'] + sorted(df['Banco'].unique().tolist())
            banco_selecionado = st.selectbox('Filtrar por banco:', bancos)
            
            if banco_selecionado != 'Todos':
                df_filtered = df[df['Banco'] == banco_selecionado]
            else:
                df_filtered = df
        else:
            df_filtered = df
        
        # Criar 5 colunas com proporções (10,1,10,1,10) - colunas 1, 3, 5 para conteúdo e 2, 4 para espaçamento
        col1, spacer1, col2, spacer2, col3 = st.columns([10, 1, 10, 1, 10])
        
        # Distribuir financiamentos nas três colunas principais (ignorando as colunas de espaçamento)
        for i, row in df_filtered.iterrows():
            if i % 3 == 0:
                with col1:
                    with st.container():
                        exibir_card_financiamento(st, row)
                        st.markdown("---")
            elif i % 3 == 1:
                with col2:
                    with st.container():
                        exibir_card_financiamento(st, row)
                        st.markdown("---")
            else:  # i % 3 == 2
                with col3:
                    with st.container():
                        exibir_card_financiamento(st, row)
                        st.markdown("---")
    
    # Tab 3: Projeções Anuais
    with tabs[2]:
        st.subheader("Timeline de Financiamentos")
        
        # Criar timeline visual simplificada
        st.markdown("""
        <div class="timeline-container">
            <h3>Quando os financiamentos serão quitados?</h3>
        """, unsafe_allow_html=True)
        
        # Ordenar financiamentos por ano de quitação
        df_timeline = df[df['Status'] == 'EM ANDAMENTO'].sort_values('Ano quitação')
        
        # Verificar se existem financiamentos em andamento
        if not df_timeline.empty:
            # Criar gráfico de Gantt simplificado
            fig = go.Figure()
            
            # Adicionar barras para cada financiamento
            for i, row in df_timeline.iterrows():
                # Nome para exibição
                nome_exibicao = f"{row['Descrição']} ({row['Banco'] if not pd.isna(row['Banco']) else 'Não informado'})"
                
                # Calcular posição das barras
                fig.add_trace(go.Bar(
                    y=[nome_exibicao],
                    x=[row['Ano quitação'] - row['Ano de aquisição'] + 1],  # Duração em anos
                    base=[row['Ano de aquisição'] - 0.5],     # Ano inicial
                    orientation='h',
                    text=f"{row['Ano de aquisição']} - {row['Ano quitação']}",
                    textposition='inside',
                    marker=dict(color=COLOR_PALETTE[0]),
                    hoverinfo='text',
                    hovertext=f"<b>{row['Descrição']}</b><br>Banco: {row['Banco'] if not pd.isna(row['Banco']) else 'Não informado'}<br>Aquisição: {row['Ano de aquisição']}<br>Quitação: {row['Ano quitação']}"
                ))
            
            # Adicionar linha vertical para o ano atual
            ano_atual = datetime.now().year
            fig.add_shape(
                type='line',
                x0=ano_atual,
                x1=ano_atual,
                y0=-0.5,
                y1=len(df_timeline) - 0.5,
                line=dict(
                    color=COLOR_PALETTE[4],
                    width=2,
                    dash='dash'
                )
            )
            
            # Adicionar texto para ano atual
            fig.add_annotation(
                x=ano_atual,
                y=len(df_timeline) - 0.5,
                text="Ano Atual",
                showarrow=False,
                yshift=10,
                font=dict(
                    color=COLOR_PALETTE[4],
                    size=12
                )
            )
            
            fig.update_layout(
                title='Linha do Tempo de Quitação',
                xaxis=dict(
                    title='Anos',
                    tickvals=list(range(
                        min(df_timeline['Ano de aquisição'].min(), ano_atual),
                        df_timeline['Ano quitação'].max() + 1
                    ))
                ),
                yaxis=dict(
                    title='Financiamentos'
                ),
                height=400,
                margin=dict(l=50, r=50, t=50, b=50),
                showlegend=False
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Tabela de projeção por ano
            st.subheader("Financiamentos por Ano de Quitação")
            
            # Criar três colunas com proporções (5,1,5) - a coluna do meio é apenas espaçamento
            col_left, col_middle, col_right = st.columns([5, 1, 5])
            
            # Obter lista de anos ordenados
            anos_quitacao = sorted(df_timeline['Ano quitação'].unique())
            
            # Dividir os anos em duas partes
            metade = (len(anos_quitacao) + 1) // 2  # Arredonda para cima se for ímpar
            anos_esquerda = anos_quitacao[:metade]
            anos_direita = anos_quitacao[metade:]
            
            # Processando anos na coluna da esquerda
            with col_left:
                for ano in anos_esquerda:
                    df_ano = df_timeline[df_timeline['Ano quitação'] == ano]
                    
                    st.markdown(f"### {ano}")
                    
                    for _, row in df_ano.iterrows():
                        banco = row['Banco'] if not pd.isna(row['Banco']) else "Não informado"
                        valor = formatar_moeda(row['Valor A Pagar'])
                        
                        st.markdown(f"""
                        <div style="display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #eee;">
                            <div>
                                <span style="font-weight: 500;">{row['Descrição']}</span>
                                <span class="bank-badge" style="background-color: {COLOR_PALETTE[1]};">{banco}</span>
                            </div>
                            <div>{valor}</div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    st.markdown("---")
            
            # Processando anos na coluna da direita
            with col_right:
                for ano in anos_direita:
                    df_ano = df_timeline[df_timeline['Ano quitação'] == ano]
                    
                    st.markdown(f"### {ano}")
                    
                    for _, row in df_ano.iterrows():
                        banco = row['Banco'] if not pd.isna(row['Banco']) else "Não informado"
                        valor = formatar_moeda(row['Valor A Pagar'])
                        
                        st.markdown(f"""
                        <div style="display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #eee;">
                            <div>
                                <span style="font-weight: 500;">{row['Descrição']}</span>
                                <span class="bank-badge" style="background-color: {COLOR_PALETTE[1]};">{banco}</span>
                            </div>
                            <div>{valor}</div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    st.markdown("---")
        else:
            st.info("Não há financiamentos em andamento para projeção.")
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Rodapé com informações
    st.markdown(f"""
    <div style="font-size: 0.8rem; color: #666; font-style: italic; text-align: center; margin-top: 30px;">
        Dados carregados da planilha. Última atualização: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
    </div>
    """, unsafe_allow_html=True)

# Executar aplicação
if __name__ == "__main__":
    main()