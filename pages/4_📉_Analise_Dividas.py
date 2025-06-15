import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import locale

# Configurar locale para formato brasileiro
try:
    locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
except:
    try:
        locale.setlocale(locale.LC_ALL, 'portuguese_brazil')
    except:
        locale.setlocale(locale.LC_ALL, '')  # Usa o locale padrão do sistema

# Modifique também a função convert_to_real para ser mais resiliente
def convert_to_real(value):
    try:
        return locale.currency(value, grouping=True)
    except:
        # Fallback para formatação manual se o locale falhar
        return f'R$ {value:,.2f}'.replace(',', '*').replace('.', ',').replace('*', '.')
# URL da planilha
sheet_url = "https://docs.google.com/spreadsheets/d/14kGm7ZcimlB8RMO92Tsc-lCVJtyvURKRKpzpLRGbV6E/export?format=csv&gid=0"



# Função de conversão monetária aprimorada
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

# Função que processa o DF
def process_dataframe(df):
    try:
        # Limpeza inicial do DataFrame
        df = df.iloc[4:].reset_index(drop=True)
        df.columns = df.iloc[0]
        df = df[1:].dropna(axis=1, how='all')
        
        # Tratamento de colunas duplicadas
        df.columns = [f"{col}_{i}" if df.columns.tolist().count(col) > 1 else col 
                     for i, col in enumerate(df.columns)]
        
        # Processamento de colunas monetárias
        parcela_cols = [col for col in df.columns if 'parcelas' in col]
        for col in parcela_cols:
            df[col] = df[col].apply(convert_to_float)
        
        # Processamento de datas
        data_cols = [col for col in df.columns if 'data de pgto' in col]
        for col in data_cols:
            df[col] = pd.to_datetime(df[col], format='%d/%m/%Y', errors='coerce')
            
        return df
    except Exception as e:
        st.error(f"Erro no processamento: {str(e)}")
        return pd.DataFrame()

# Configuração da página
st.set_page_config(
    page_title='Análise Financeira',
    page_icon='💰',
    layout='wide'
)

# Estilo CSS customizado
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
        color: #1e88e5;
        padding-bottom: 1rem;
    }
    h2 {
        color: #333;
        padding: 1rem 0;
    }
    .late-payment {
        color: #FF5252;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

try:
    # Carregamento e processamento dos dados
    df = pd.read_csv(sheet_url)
    df_processed = process_dataframe(df)
    
    if df_processed.empty:
        st.error("Falha no processamento dos dados. Verifique a fonte.")
    else:
        # Data atual para verificação de atrasos
        data_atual = datetime.now()
        
        # Header com logo e título
        col_logo, col_title = st.columns([1, 4])
        with col_title:
            st.title('💰 Dashboard Financeiro - Análise de Dívidas')
        
        # Cálculo dos valores
        dividas = {
            'Capital de Giro': {'cols': ['parcelas_0'], 'status': 'status_2', 'data': 'data de pgto_1'},
            'Ducato': {'cols': ['parcelas_3'], 'status': 'status_5', 'data': 'data de pgto_4'},
            'Muck': {'cols': ['parcelas_6'], 'status': 'status_8', 'data': 'data de pgto_7'}
        }
        
        totais = {}
        total_atrasado = 0
        
        for nome, info in dividas.items():
            col = info['cols'][0]
            status_col = info['status']
            data_col = info['data']
            
            # Verifica pagamentos atrasados
            df_atrasados = df_processed[
                (df_processed[status_col] == 'PENDENTE') & 
                (df_processed[data_col] < data_atual)
            ]
            
            valor_atrasado = df_atrasados[col].sum()
            total_atrasado += valor_atrasado
            
            totais[nome] = {
                'total': df_processed[col].sum(),
                'pago': df_processed[df_processed[status_col] == 'PAGO'][col].sum(),
                'pendente': df_processed[df_processed[status_col] == 'PENDENTE'][col].sum(),
                'atrasado': valor_atrasado
            }
            totais[nome]['porcentagem'] = (totais[nome]['pago'] / totais[nome]['total']) * 100
        
        # Métricas principais
        st.header('Visão Geral')
        
        total_geral = sum(d['total'] for d in totais.values())
        total_pendente = sum(d['pendente'] for d in totais.values())
        total_pago = sum(d['pago'] for d in totais.values())
        
        col1, col2, col3, col4, col5 = st.columns(5)
        
        col1.metric('💼 Total de Dívidas', convert_to_real(total_geral))
        col2.metric('🔴 Total Pendente', convert_to_real(total_pendente))
        col3.metric('🟢 Total Pago', convert_to_real(total_pago))
        col4.metric('⚠️ Total Atrasado', convert_to_real(total_atrasado))
        col5.metric('📊 Percentual Pago', f"{(total_pago/total_geral)*100:.1f}%")
        
        # Análise detalhada
        st.markdown("---")
        st.header('Análise Detalhada por Dívida')
        
        # Cards para cada dívida
        cols = st.columns(3)
        for idx, (nome, valores) in enumerate(totais.items()):
            with cols[idx]:
                st.subheader(f"📑 {nome}")
                st.metric('Total', convert_to_real(valores['total']))
                
                # Criação de colunas para valores pago/pendente/atrasado
                col_paid, col_pending = st.columns(2)
                with col_paid:
                    st.markdown(f"🟢 **Pago:**\n{convert_to_real(valores['pago'])}")
                with col_pending:
                    st.markdown(f"🔴 **Pendente:**\n{convert_to_real(valores['pendente'])}")
                
                st.markdown(f"⚠️ **Atrasado:** <span class='late-payment'>{convert_to_real(valores['atrasado'])}</span>", unsafe_allow_html=True)
                
                # Barra de progresso
                progress = int(valores['porcentagem'])
                st.progress(progress/100, text=f"**{progress}% Concluído**")
                st.divider()
        
        # Gráficos
        st.header('Visualizações')
        
        col_chart1, col_chart2 = st.columns(2)
        
        with col_chart1:
            # Gráfico de barras empilhadas com valores atrasados
            fig_bars = go.Figure()
            
            # Adiciona barras para valores pagos
            fig_bars.add_trace(go.Bar(
                name='Pago',
                x=list(totais.keys()),
                y=[valores['pago'] for valores in totais.values()],
                marker_color='#2ecc71'
            ))
            
            # Adiciona barras para valores atrasados
            fig_bars.add_trace(go.Bar(
                name='Atrasado',
                x=list(totais.keys()),
                y=[valores['atrasado'] for valores in totais.values()],
                marker_color='#FF5252'
            ))
            
            # Adiciona barras para valores pendentes (não atrasados)
            fig_bars.add_trace(go.Bar(
                name='Pendente',
                x=list(totais.keys()),
                y=[valores['pendente'] - valores['atrasado'] for valores in totais.values()],
                marker_color='#e74c3c'
            ))
            
            fig_bars.update_layout(
                title='Composição das Dívidas',
                barmode='stack',
                showlegend=True,
                plot_bgcolor='white',
                height=400,
                yaxis_title='Valor (R$)',
                xaxis_title='Tipo de Dívida'
            )
            st.plotly_chart(fig_bars, use_container_width=True)
        
        with col_chart2:
            # Gráfico de pizza do total
            fig_pie = go.Figure(data=[go.Pie(
                labels=list(totais.keys()),
                values=[valores['total'] for valores in totais.values()],
                hole=.3,
                marker=dict(colors=['#3498db', '#e67e22', '#9b59b6'])
            )])
            
            fig_pie.update_layout(
                title='Distribuição do Total de Dívidas',
                height=400,
                showlegend=True
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        
        with col_chart1:
            # Gráfico para valores atrasados
            fig_atrasados = go.Figure(data=[
                go.Bar(
                    x=list(totais.keys()),
                    y=[valores['atrasado'] for valores in totais.values()],
                    marker_color='#FF5252'
                )
            ])
            
            fig_atrasados.update_layout(
                title='Valores Atrasados por Dívida',
                height=300,
                plot_bgcolor='white',
                yaxis_title='Valor (R$)',
                xaxis_title='Tipo de Dívida'
            )
            
            st.plotly_chart(fig_atrasados, use_container_width=True)
        
        # Tabela detalhada
        if st.checkbox('Mostrar Dados Detalhados'):
            st.markdown("---")
            st.header('Dados Detalhados')
            
            # Preparar dados para exibição
            detailed_data = []
            for nome, valores in totais.items():
                detailed_data.append({
                    'Tipo de Dívida': nome,
                    'Total': convert_to_real(valores['total']),
                    'Pago': convert_to_real(valores['pago']),
                    'Pendente': convert_to_real(valores['pendente']),
                    'Atrasado': convert_to_real(valores['atrasado']),
                    'Progresso': f"{valores['porcentagem']:.1f}%"
                })
            
            st.dataframe(
                pd.DataFrame(detailed_data),
                use_container_width=True,
                hide_index=True
            )
            
            # Detalhamento de pagamentos atrasados
            st.subheader('Detalhamento de Pagamentos Atrasados')
            
            atrasados_detalhados = []
            for nome, info in dividas.items():
                col = info['cols'][0]
                status_col = info['status']
                data_col = info['data']
                
                df_atrasados = df_processed[
                    (df_processed[status_col] == 'PENDENTE') & 
                    (df_processed[data_col] < data_atual)
                ]
                
                for _, row in df_atrasados.iterrows():
                    atrasados_detalhados.append({
                        'Tipo de Dívida': nome,
                        'Valor': convert_to_real(row[col]),
                        'Data de Pagamento': row[data_col].strftime('%d/%m/%Y'),
                        'Dias de Atraso': (data_atual - row[data_col]).days
                    })
            
            if atrasados_detalhados:
                st.dataframe(
                    pd.DataFrame(atrasados_detalhados),
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.info('Não há pagamentos atrasados.')

except Exception as e:
    st.error(f"Erro na execução do dashboard: {str(e)}")