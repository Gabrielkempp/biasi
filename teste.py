import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import locale
import requests
from io import BytesIO

# Configurar locale para formato brasileiro
try:
    locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
except:
    try:
        locale.setlocale(locale.LC_ALL, 'portuguese_brazil')
    except:
        locale.setlocale(locale.LC_ALL, '')  # Usa o locale padrão do sistema

# URL da planilha
sheet_url = "https://docs.google.com/spreadsheets/d/1m6tj6OOIKi2AFM3wLsga_vZkVwlLnXuGVkDco9PKHvg/export?format=csv&gid=690764200"

# Função de conversão monetária
def convert_to_float(value):
    if pd.isna(value):
        return 0.0
    try:
        str_value = str(value).strip()
        str_value = str_value.replace('R$', '').replace(' ', '').replace('.', '').replace(',', '.')
        return float(str_value)
    except:
        return 0.0

# Função que converte para o Real
def convert_to_real(value):
    try:
        return locale.currency(value, grouping=True)
    except:
        return f'R$ {value:,.2f}'.replace(',', '_').replace('.', ',').replace('_', '.')

# Função para carregar e processar os dados
def carregar_dados():
    try:
        response = requests.get(sheet_url)
        if response.status_code == 200:
            # Ler CSV
            df = pd.read_csv(BytesIO(response.content))
            
            # Verificar se a planilha está no formato esperado
            if 'CONTROLE DE ENTRADA E SAÍDA GERAL BIASI' in df.columns:
                # Pular as linhas que não são dados (títulos)
                df = df.iloc[2:].reset_index(drop=True)
                
                # Renomear colunas
                df.columns = ['Mês', 'Entrada', 'Saída', 'Meta', 'NaN1', 'NaN2']
                
                # Remover colunas desnecessárias
                df = df.drop(['NaN1', 'NaN2'], axis=1)
                
                # Converter valores monetários
                for col in ['Entrada', 'Saída', 'Meta']:
                    # Converter para string
                    df[col] = df[col].astype(str).str.strip()
                    
                    # Remover R$
                    df[col] = df[col].str.replace('R$', '', regex=False).str.strip()
                    
                    # Remover pontos de milhar
                    df[col] = df[col].str.replace('.', '', regex=False)
                    
                    # Substituir vírgula por ponto
                    df[col] = df[col].str.replace(',', '.', regex=False)
                    
                    # Converter para float com tratamento para valores especiais
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
                
                return df
            else:
                st.warning("Formato não reconhecido.")
                return pd.DataFrame()
        else:
            st.error(f"Erro ao acessar a planilha: {response.status_code}")
            return pd.DataFrame()
    except Exception as e:
        st.error(f"Erro ao carregar dados: {str(e)}")
        return pd.DataFrame()

# Configuração da página
st.set_page_config(
    page_title='Controle Financeiro BIASI',
    page_icon='💰',
    layout='wide',
    initial_sidebar_state='expanded'
)

# Estilo CSS customizado
st.markdown("""
    <style>
    .main {
        padding: 2rem;
    }
    .stMetric {
        background-color: #f8f9fa;
        padding: 1.5rem;
        border-radius: 0.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .stProgress {
        background-color: rgba(28, 225, 117, 0.18);
        padding: 1.5rem;
        border-radius: 0.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    h1 {
        color: #1e88e5;
        padding-bottom: 1rem;
    }
    h2 {
        color: #333;
        padding: 1rem 0;
    }
    .card {
        background-color: #f8f9fa;
        padding: 1.2rem;
        border-radius: 0.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin-bottom: 1rem;
    }
    .summary-metrics {
        padding: 0.5rem 0;
    }
    </style>
""", unsafe_allow_html=True)

try:
    # Carregamento dos dados
    df = carregar_dados()
    
    if df.empty:
        st.error("Falha no carregamento dos dados. Verifique a fonte.")
    else:
        # Header com título
        st.title('💰 Controle de Entrada e Saída BIASI')
        
        # Cálculo dos valores
        total_entrada = df['Entrada'].sum()
        total_saida = df['Saída'].sum()
        saldo = total_entrada - total_saida
        
        # Calcular diferença
        df['Diferença'] = df['Entrada'] - df['Saída']
        
        # Calcular estatísticas de desempenho (movido de baixo para cima)
        meses_positivos = (df['Diferença'] > 0).sum()
        total_meses = len(df)
        percentual_positivo = (meses_positivos / total_meses) * 100 if total_meses > 0 else 0
        
        meses_acima_meta = (df['Entrada'] >= df['Meta']).sum()
        percentual_meta = (meses_acima_meta / total_meses) * 100 if total_meses > 0 else 0
        
        if not df.empty:
            melhor_mes_idx = df['Diferença'].idxmax()
            pior_mes_idx = df['Diferença'].idxmin()
            
            melhor_mes = df.iloc[melhor_mes_idx]
            pior_mes = df.iloc[pior_mes_idx]
        
        # LAYOUT REORGANIZADO: DASHBOARD PRINCIPAL
        st.header('Dashboard Principal')
        
        # Duas seções principais lado a lado
        col_totais, col_performance = st.columns([1, 1])
        
        # Seção 1: Valores totais
        with col_totais:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.subheader('📊 Valores Totais')
            
            metrics_col1, metrics_col2, metrics_col3 = st.columns(3)
            
            metrics_col1.metric('💹 Total de Entradas', convert_to_real(total_entrada))
            metrics_col2.metric('📉 Total de Saídas', convert_to_real(total_saida))
            metrics_col3.metric('💰 Saldo', convert_to_real(saldo), 
                   delta=f"{convert_to_real(saldo)}" if saldo != 0 else None)
            
            st.markdown('</div>', unsafe_allow_html=True)
            
        # Seção 2: Análise de desempenho (movida para cima)
        with col_performance:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.subheader('🎯 Análise de Desempenho')
            
            # Layout em duas linhas para os indicadores
            perf_row1_col1, perf_row1_col2 = st.columns(2)
            perf_row2_col1, perf_row2_col2 = st.columns(2)
            
            perf_row1_col1.metric(
                "Meses com Saldo Positivo", 
                f"{meses_positivos} de {total_meses}", 
                f"{percentual_positivo:.1f}%"
            )
            
            perf_row1_col2.metric(
                "Meses Acima da Meta", 
                f"{meses_acima_meta} de {total_meses}", 
                f"{percentual_meta:.1f}%"
            )
            
            if not df.empty:
                perf_row2_col1.metric(
                    "Melhor Mês", 
                    f"{melhor_mes['Mês']}", 
                    f"+{convert_to_real(melhor_mes['Diferença'])}"
                )
                
                perf_row2_col2.metric(
                    "Pior Mês",
                    f"{pior_mes['Mês']}",
                    f"{convert_to_real(pior_mes['Diferença'])}",
                    delta_color="inverse"
                )
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Separador para a próxima seção
        st.markdown("---")
        
        # GRÁFICO PRINCIPAL
        st.subheader('📈 Evolução Mensal')
        
        # Gráfico comparativo em tela cheia
        fig = go.Figure()
        
        # Adicionar barras de entrada
        fig.add_trace(go.Bar(
            x=df['Mês'],
            y=df['Entrada'],
            name='Entrada',
            marker_color='#4CAF50'
        ))
        
        # Adicionar barras de saída
        fig.add_trace(go.Bar(
            x=df['Mês'],
            y=df['Saída'],
            name='Saída',
            marker_color='#F44336'
        ))
        
        # Adicionar linha de meta
        fig.add_trace(go.Scatter(
            x=df['Mês'],
            y=df['Meta'],
            name='Meta',
            line=dict(color='#FFC107', width=2, dash='dash'),
            mode='lines+markers'
        ))
        
        # Configurar layout
        fig.update_layout(
            barmode='group',
            template='plotly_white',
            height=400,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            yaxis_title='Valor (R$)',
            xaxis_title='Mês'
        )
        
        # Exibir gráfico
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False, 'staticPlot': True})
        
        # ANÁLISE DETALHADA
        st.markdown("---")
        st.header('Análise Detalhada')
        
        # Layout de análise em três colunas
        col_table, col_chart1, col_chart2 = st.columns([1, 1, 1])
        
        with col_table:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.subheader("📋 Dados Mensais")
            # Formatar para exibição
            df_exibicao = df.copy()
            for col in ['Entrada', 'Saída', 'Meta', 'Diferença']:
                df_exibicao[col] = df_exibicao[col].apply(convert_to_real)
            
            # Exibir tabela
            st.dataframe(
                df_exibicao,
                use_container_width=True,
                hide_index=True
            )
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col_chart1:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.subheader("💵 Saldo Mensal")
            # Gráfico de saldo mensal
            fig_saldo = go.Figure()
            
            # Adicionar barras de saldo
            fig_saldo.add_trace(go.Bar(
                x=df['Mês'],
                y=df['Diferença'],
                name='Saldo',
                marker_color=['#4CAF50' if val >= 0 else '#F44336' for val in df['Diferença']]
            ))
            
            # Adicionar linha de zero
            fig_saldo.add_shape(
                type="line",
                x0=df['Mês'].iloc[0],
                y0=0,
                x1=df['Mês'].iloc[-1],
                y1=0,
                line=dict(color="black", width=1, dash="dash")
            )
            
            # Configurar layout
            fig_saldo.update_layout(
                template='plotly_white',
                height=300,
                showlegend=False,
                yaxis_title='Valor (R$)',
                margin=dict(l=20, r=20, t=20, b=20)  # Margens reduzidas
            )
            
            # Adicionar valores às barras
            fig_saldo.update_traces(
                texttemplate='%{y:,.2f}',
                textposition='outside'
            )
            
            # Exibir gráfico
            st.plotly_chart(fig_saldo, use_container_width=True, config={'displayModeBar': False, 'staticPlot': True})
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col_chart2:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.subheader("📊 Tendência Acumulada")
            
            # Calcular valores acumulados
            df_acumulado = df.copy()
            df_acumulado['Entrada_Acumulada'] = df_acumulado['Entrada'].cumsum()
            df_acumulado['Saída_Acumulada'] = df_acumulado['Saída'].cumsum()
            
            # Gráfico de acumulado
            fig_acum = go.Figure()
            
            fig_acum.add_trace(go.Scatter(
                x=df_acumulado['Mês'],
                y=df_acumulado['Entrada_Acumulada'],
                name='Entrada Acumulada',
                line=dict(color='#4CAF50', width=3),
                fill='tozeroy',
                mode='lines+markers'
            ))
            
            fig_acum.add_trace(go.Scatter(
                x=df_acumulado['Mês'],
                y=df_acumulado['Saída_Acumulada'],
                name='Saída Acumulada',
                line=dict(color='#F44336', width=3),
                fill='tozeroy',
                mode='lines+markers'
            ))
            
            # Configurar layout
            fig_acum.update_layout(
                template='plotly_white',
                height=300,
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                yaxis_title='Valor Acumulado (R$)',
                margin=dict(l=20, r=20, t=20, b=20)  # Margens reduzidas
            )
            
            # Exibir gráfico
            st.plotly_chart(fig_acum, use_container_width=True, config={'displayModeBar': False, 'staticPlot': True})
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Nota de rodapé
        st.markdown("---")
        st.caption("Dados atualizados automaticamente da planilha do Google Sheets.")

except Exception as e:
    st.error(f"Erro na execução do dashboard: {str(e)}")