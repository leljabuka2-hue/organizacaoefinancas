import streamlit as st
import pandas as pd
import json
import os
import plotly.graph_objects as go
from datetime import datetime, date, timedelta
import plotly.express as px
from streamlit_option_menu import option_menu

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Minhas Finanças", page_icon="💰", layout="wide")

# --- CSS PERSONALIZADO (MANTENDO O DESIGN LIMPO) ---
def inject_custom_css():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700&display=swap');
        .stApp { background-color: #F4F7FC; font-family: 'Nunito', sans-serif; }
        .block-container { padding-top: 1.5rem; padding-bottom: 2rem; }
        
        /* CARDS */
        .white-card {
            background-color: #FFFFFF; border-radius: 15px; padding: 20px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.05); margin-bottom: 20px; height: 100%;
        }
        
        /* STEPPER */
        .step-item { display: flex; align-items: flex-start; margin-bottom: 15px; position: relative; }
        .step-icon {
            width: 30px; height: 30px; border-radius: 50%; display: flex; 
            align-items: center; justify-content: center; color: white; 
            font-weight: bold; z-index: 2; margin-right: 15px; flex-shrink: 0;
        }
        .step-line {
            position: absolute; left: 14px; top: 30px; bottom: -20px; width: 2px;
            background-color: #E0E0E0; z-index: 1;
        }
        .step-last .step-line { display: none; }
        
        /* VISÃO GERAL COLORIDA */
        .color-card {
            border-radius: 15px; padding: 20px; color: white;
            box-shadow: 0 4px 10px rgba(0,0,0,0.1); display: flex;
            align-items: center; margin-bottom: 10px;
        }
        .cc-icon {
            background-color: rgba(255,255,255,0.2); width: 45px; height: 45px;
            border-radius: 50%; display: flex; align-items: center; justify-content: center;
            font-size: 20px; margin-right: 15px;
        }
        .bg-blue { background-color: #2D9CDB; }
        .bg-green { background-color: #27AE60; }
        .bg-red { background-color: #EB5757; }
        .bg-yellow { background-color: #F2C94C; }
        
        /* TABLE */
        .custom-table { width: 100%; border-collapse: collapse; }
        .custom-table th { text-align: left; color: #888; font-weight: 600; padding: 10px; border-bottom: 1px solid #eee; }
        .custom-table td { padding: 15px 10px; border-bottom: 1px solid #f9f9f9; color: #333; font-weight: 600; }
        
        /* TEXTOS */
        .val-big { font-size: 22px; font-weight: 700; color: #333; }
        .text-gray { color: #828282; font-size: 13px; }
        
        /* PLOTLY */
        .js-plotly-plot .plotly .modebar { display: none !important; }
        </style>
    """, unsafe_allow_html=True)

inject_custom_css()

# --- GERENCIAMENTO DE DADOS (DB REAL) ---
DB_FILE = 'finance_db_real.json'

def load_data():
    if not os.path.exists(DB_FILE):
        return []
    with open(DB_FILE, 'r') as f:
        return json.load(f)

def save_data(data):
    with open(DB_FILE, 'w') as f:
        json.dump(data, f, indent=4)

# Carrega Dados
transactions = load_data()
df = pd.DataFrame(transactions)

# --- PROCESSAMENTO LÓGICO ---
# Se o DF não estiver vazio, converter datas
if not df.empty:
    df['date'] = pd.to_datetime(df['date'])
    df['amount'] = df['amount'].astype(float)
else:
    # Cria colunas vazias para evitar erros
    df = pd.DataFrame(columns=['id', 'date', 'type', 'category', 'account', 'amount', 'status', 'desc'])

# Define Mês Atual (Simulação de Filtro)
current_month = datetime.now().month
current_year = datetime.now().year
current_date = datetime.now()

# 1. Filtros Temporais
# Transações até o mês passado (para Saldo Inicial)
mask_anterior = (df['date'] < datetime(current_year, current_month, 1)) if not df.empty else pd.Series([False]*len(df))
df_anterior = df[mask_anterior] if not df.empty else df

# Transações deste mês
mask_atual = (df['date'].dt.month == current_month) & (df['date'].dt.year == current_year) if not df.empty else pd.Series([False]*len(df))
df_mes = df[mask_atual] if not df.empty else df

# 2. Cálculos de Saldo
def get_balance(dataframe, only_paid=False):
    if dataframe.empty: return 0.0
    if only_paid:
        dataframe = dataframe[dataframe['status'] == 'Pago']
    
    receitas = dataframe[dataframe['type'] == 'Receita']['amount'].sum()
    despesas = dataframe[dataframe['type'] == 'Despesa']['amount'].sum()
    return receitas - despesas

saldo_acumulado_anterior = get_balance(df_anterior, only_paid=True)

receitas_mes_pago = df_mes[(df_mes['type'] == 'Receita') & (df_mes['status'] == 'Pago')]['amount'].sum() if not df_mes.empty else 0
despesas_mes_pago = df_mes[(df_mes['type'] == 'Despesa') & (df_mes['status'] == 'Pago')]['amount'].sum() if not df_mes.empty else 0

receitas_mes_total = df_mes[df_mes['type'] == 'Receita']['amount'].sum() if not df_mes.empty else 0
despesas_mes_total = df_mes[df_mes['type'] == 'Despesa']['amount'].sum() if not df_mes.empty else 0

# Lógica dos Cards Principais
saldo_inicial = saldo_acumulado_anterior
saldo_atual = saldo_inicial + receitas_mes_pago - despesas_mes_pago
saldo_previsto = saldo_inicial + receitas_mes_total - despesas_mes_total

# Pendências
despesas_pendentes_count = len(df_mes[(df_mes['type'] == 'Despesa') & (df_mes['status'] == 'Pendente')]) if not df_mes.empty else 0
valor_despesas_pendentes = df_mes[(df_mes['type'] == 'Despesa') & (df_mes['status'] == 'Pendente')]['amount'].sum() if not df_mes.empty else 0

# --- SIDEBAR (NOVO FORMULÁRIO COMPLETO) ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2910/2910768.png", width=50)
    st.markdown("### Nova Transação")
    
    with st.form("main_form", clear_on_submit=True):
        f_tipo = st.selectbox("Tipo", ["Despesa", "Receita"])
        f_valor = st.number_input("Valor", min_value=0.0, step=10.0)
        f_data = st.date_input("Data", datetime.now())
        f_conta = st.selectbox("Conta / Banco", ["Nubank", "Bradesco", "Itaú", "Carteira", "Inter"])
        f_cat = st.selectbox("Categoria", ["Moradia", "Alimentação", "Transporte", "Lazer", "Salário", "Investimentos", "Outros"])
        f_status = st.radio("Status", ["Pago", "Pendente"], horizontal=True)
        f_desc = st.text_input("Descrição")
        
        if st.form_submit_button("Salvar Movimentação"):
            new_t = {
                "id": int(datetime.now().timestamp()),
                "date": f_data.strftime("%Y-%m-%d"),
                "type": f_tipo,
                "amount": f_valor,
                "account": f_conta,
                "category": f_cat,
                "status": f_status,
                "desc": f_desc
            }
            transactions.append(new_t)
            save_data(transactions)
            st.toast("Adicionado!", icon="✅")
            import time
            time.sleep(0.5)
            st.rerun()

    st.markdown("---")
    st.info("💡 **Dica de Teste:** Adicione uma despesa 'Pendente' no Nubank e veja que o 'Saldo Atual' não muda, mas o 'Previsto' sim.")

# --- UI PRINCIPAL ---

# Header Mês
c_top1, c_top2 = st.columns([6, 2])
with c_top2:
    mes_nome = datetime.now().strftime("%B").capitalize()
    st.markdown(f"""
    <div style="display: flex; justify-content: flex-end; align-items: center; gap: 10px;">
        <div style="background: white; padding: 8px 15px; border-radius: 20px; color: #555; font-weight: 600; box-shadow: 0 2px 5px rgba(0,0,0,0.05);">📅 {mes_nome} (Atual)</div>
    </div>
    """, unsafe_allow_html=True)

# Linha 1
c1, c2, c3 = st.columns([3, 4, 3])

# CARD 1: SALDOS (Stepper)
with c1:
    st.markdown(f"""
    <div class="white-card">
        <div class="step-item">
            <div class="step-line"></div>
            <div class="step-icon" style="background-color: #2D9CDB;">✓</div>
            <div>
                <div class="val-big" style="font-size: 16px; color: #888; font-weight: 400;">R$ {saldo_inicial:,.2f}</div>
                <div class="text-gray">Inicial (Mês Anterior)</div>
            </div>
        </div>
        <div class="step-item">
            <div class="step-line"></div>
            <div class="step-icon" style="background-color: #2D9CDB; box-shadow: 0 0 0 4px #D6EAF8;"></div>
            <div>
                <div class="val-big">R$ {saldo_atual:,.2f}</div>
                <div class="text-gray">Saldo atual (Realizado)</div>
            </div>
        </div>
        <div class="step-item step-last">
            <div class="step-icon" style="background-color: #E0E0E0; color: #888;">🕒</div>
            <div>
                <div class="val-big" style="font-size: 18px; color: #888;">R$ {saldo_previsto:,.2f}</div>
                <div class="text-gray">Previsto (Final do Mês)</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# CARD 2: GRÁFICO EVOLUÇÃO (Dinâmico)
with c2:
    st.markdown('<div class="white-card" style="padding: 10px;">', unsafe_allow_html=True)
    st.markdown("<p style='color:#555; font-weight:600; margin-left: 10px;'>Evolução das despesas (Diário)</p>", unsafe_allow_html=True)
    
    if not df_mes.empty:
        # Agrupa despesas por dia
        df_chart = df_mes[df_mes['type'] == 'Despesa'].groupby('date')['amount'].sum().reset_index().sort_values('date')
        
        fig_area = go.Figure()
        fig_area.add_trace(go.Scatter(
            x=df_chart['date'], y=df_chart['amount'], 
            fill='tozeroy', mode='lines+markers', 
            line=dict(color='#EB5757', width=2),
            marker=dict(size=6, color='#EB5757')
        ))
        fig_area.update_layout(
            margin=dict(l=20, r=20, t=10, b=20), height=180,
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            showlegend=False,
            xaxis=dict(showgrid=False, tickformat="%d/%m"),
            yaxis=dict(showgrid=True, gridcolor='#f0f0f0')
        )
        st.plotly_chart(fig_area, use_container_width=True, config={'displayModeBar': False})
    else:
        st.markdown("<p style='text-align:center; color:#ccc; margin-top:50px;'>Sem dados neste mês</p>", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# CARD 3: PENDÊNCIAS (Dinâmico)
with c3:
    st.markdown(f"""
    <div class="white-card" style="text-align: center; display: flex; flex-direction: column; justify-content: center; align-items: center;">
        <div style="font-weight: 600; color: #EB5757; margin-bottom: 10px;">Despesas Pendentes</div>
        <div style="background-color: #FDEDEE; width: 60px; height: 60px; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin-bottom: 15px;">
            <span style="font-size: 24px;">🧾</span>
        </div>
        <p style="color: #555; font-size: 14px; margin-bottom: 15px;">
            Você tem <b>{despesas_pendentes_count} despesas pendentes</b><br>
            <span style="font-size: 18px; font-weight: 700; color: #333;">R$ {valor_despesas_pendentes:,.2f}</span>
        </p>
    </div>
    """, unsafe_allow_html=True)

# Linha 2: Visão Geral (Widgets)
row2_1, row2_2, row2_3, row2_4 = st.columns(4)
# Cálculo de Balanço (Transferencias simuladas como Saldo - Gastos)
balanco = receitas_mes_total - despesas_mes_total

def card_html(color_class, icon, label, value):
    return f"""
    <div class="color-card {color_class}">
        <div class="cc-icon">{icon}</div>
        <div>
            <div style="font-size: 20px; font-weight: 700;">{value}</div>
            <div style="font-size: 12px; opacity: 0.9;">{label}</div>
        </div>
    </div>
    """

with row2_1: st.markdown(card_html("bg-blue", "🏛️", "Saldo Previsto", f"R$ {saldo_previsto:,.2f}"), unsafe_allow_html=True)
with row2_2: st.markdown(card_html("bg-green", "➕", "Receitas (Mês)", f"R$ {receitas_mes_total:,.2f}"), unsafe_allow_html=True)
with row2_3: st.markdown(card_html("bg-red", "➖", "Despesas (Mês)", f"R$ {despesas_mes_total:,.2f}"), unsafe_allow_html=True)
with row2_4: st.markdown(card_html("bg-yellow", "⇄", "Balanço Mensal", f"R$ {balanco:,.2f}"), unsafe_allow_html=True)

# Linha 3: Contas e Categorias
st.markdown("<br>", unsafe_allow_html=True)
c_bot1, c_bot2 = st.columns([2, 1])

# LÓGICA DA TABELA DE CONTAS
with c_bot1:
    st.markdown('<div class="white-card">', unsafe_allow_html=True)
    st.markdown("<h4 style='color: #555;'>Contas Bancárias</h4>", unsafe_allow_html=True)
    
    # Gerar dados agrupados por Conta (Logic Core)
    if not df.empty:
        # Pega todas as contas que existem no DB
        contas_unicas = df['account'].unique()
        
        table_html = """
        <table class="custom-table">
            <thead>
                <tr>
                    <th>Conta</th>
                    <th>Receitas</th>
                    <th>Despesas</th>
                    <th>Saldo Atual</th>
                </tr>
            </thead>
            <tbody>
        """
        
        logos = {
            "Nubank": "https://logodownload.org/wp-content/uploads/2019/08/nubank-logo-3.png",
            "Bradesco": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3f/Logo_Bradesco.svg/1200px-Logo_Bradesco.svg.png",
            "Itaú": "https://logodownload.org/wp-content/uploads/2014/05/itau-logo-1.png",
            "Inter": "https://logodownload.org/wp-content/uploads/2018/10/banco-inter-logo.png",
            "Carteira": "https://cdn-icons-png.flaticon.com/512/482/482541.png"
        }

        for conta in contas_unicas:
            # Filtra transações dessa conta
            df_c = df[df['account'] == conta]
            
            # Rec (Total pago)
            c_rec = df_c[(df_c['type'] == 'Receita') & (df_c['status'] == 'Pago')]['amount'].sum()
            # Desp (Total pago)
            c_desp = df_c[(df_c['type'] == 'Despesa') & (df_c['status'] == 'Pago')]['amount'].sum()
            # Saldo (Receita Total - Despesa Total de toda história)
            c_saldo = c_rec - c_desp 
            
            img_url = logos.get(conta, "https://cdn-icons-png.flaticon.com/512/2910/2910768.png")
            
            table_html += f"""
            <tr>
                <td style="display: flex; align-items: center; gap: 10px;">
                    <img src="{img_url}" width="25" style="border-radius: 4px;"> {conta}
                </td>
                <td style="color: #27AE60;">R$ {c_rec:,.2f}</td>
                <td style="color: #EB5757;">R$ {c_desp:,.2f}</td>
                <td>R$ {c_saldo:,.2f}</td>
            </tr>
            """
        table_html += "</tbody></table>"
        st.markdown(table_html, unsafe_allow_html=True)
    else:
        st.info("Nenhuma conta movimentada ainda.")
        
    st.markdown('</div>', unsafe_allow_html=True)

# LÓGICA DO GRÁFICO DE CATEGORIAS
with c_bot2:
    st.markdown('<div class="white-card">', unsafe_allow_html=True)
    st.markdown("<h4 style='color: #555;'>Por Categoria</h4>", unsafe_allow_html=True)
    
    if not df_mes.empty:
        df_pie = df_mes[df_mes['type'] == 'Despesa'].groupby('category')['amount'].sum().reset_index()
        
        if not df_pie.empty:
            colors = ['#8E44AD', '#EB5757', '#95A5A6', '#F39C12', '#34495E', '#2D9CDB']
            
            fig_donut = go.Figure(data=[go.Pie(labels=df_pie['category'], values=df_pie['amount'], hole=.6)])
            fig_donut.update_traces(marker=dict(colors=colors), textinfo='percent', textposition='inside')
            fig_donut.update_layout(showlegend=True, margin=dict(t=0, b=0, l=0, r=0), height=250, 
                                    legend=dict(orientation="h", y=-0.2))
            
            total_cat = df_pie['amount'].sum()
            fig_donut.add_annotation(text=f"<b>R$ {total_cat:,.0f}</b>", showarrow=False, font=dict(size=14, color="#333"))
            
            st.plotly_chart(fig_donut, use_container_width=True, config={'displayModeBar': False})
        else:
            st.info("Sem despesas neste mês.")
    else:
        st.info("Sem dados.")
    st.markdown('</div>', unsafe_allow_html=True)
