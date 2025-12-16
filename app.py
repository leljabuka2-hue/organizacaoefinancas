import streamlit as st
import json
import pandas as pd
import os
import plotly.express as px
from datetime import datetime
import time
from streamlit_option_menu import option_menu

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="FinCRM", page_icon="⚡", layout="wide")

# --- ESTILO TAILWIND & CORREÇÃO SIDEBAR ---
def inject_tailwind_style():
    st.markdown("""
        <style>
        /* Importando Fonte Inter (Padrão Tailwind) */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

        /* RESET GERAL ESTILO TAILWIND */
        .stApp {
            background-color: #F8FAFC; /* Slate-50 */
            font-family: 'Inter', sans-serif;
        }

        /* --- CORREÇÃO BARRA LATERAL (SIDEBAR) --- */
        section[data-testid="stSidebar"] {
            background-color: #0F172A; /* Slate-900 */
            border-right: 1px solid #1E293B;
        }
        /* Força texto branco nos elementos nativos da sidebar se houver */
        section[data-testid="stSidebar"] h1, 
        section[data-testid="stSidebar"] h2, 
        section[data-testid="stSidebar"] h3, 
        section[data-testid="stSidebar"] label, 
        section[data-testid="stSidebar"] span {
            color: #F1F5F9 !important; /* Slate-100 */
        }
        
        /* --- CARDS (Métricas) ESTILO TAILWIND --- */
        div[data-testid="stMetric"] {
            background-color: #FFFFFF;
            border: 1px solid #E2E8F0; /* Slate-200 */
            border-radius: 0.75rem; /* rounded-xl */
            padding: 1.5rem; /* p-6 */
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06); /* shadow-md */
            transition: all 0.2s;
        }
        div[data-testid="stMetric"]:hover {
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1); /* shadow-lg */
        }
        div[data-testid="stMetricLabel"] {
            font-size: 0.875rem; /* text-sm */
            font-weight: 500;
            color: #64748B; /* Slate-500 */
        }
        div[data-testid="stMetricValue"] {
            font-size: 1.875rem; /* text-3xl */
            font-weight: 700;
            color: #0F172A; /* Slate-900 */
        }

        /* --- TABELAS E INPUTS --- */
        .stDataFrame {
            border: 1px solid #E2E8F0;
            border-radius: 0.5rem;
            overflow: hidden;
        }
        
        .stTextInput > div > div > input, .stNumberInput > div > div > input, .stSelectbox > div > div > div {
            border-radius: 0.5rem; /* rounded-lg */
            border: 1px solid #CBD5E1; /* Slate-300 */
            color: #1E293B;
        }
        
        /* --- BOTÕES --- */
        .stButton > button {
            background-color: #3B82F6; /* Blue-500 */
            color: white;
            border-radius: 0.5rem; /* rounded-lg */
            font-weight: 600;
            border: none;
            padding: 0.5rem 1rem;
            box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
            transition: background-color 0.2s;
        }
        .stButton > button:hover {
            background-color: #2563EB; /* Blue-600 */
        }

        /* --- REMOVER PADDING EXTRA --- */
        .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
        }
        
        /* Custom Container Styles (Simulando div Tailwind) */
        .tailwind-card {
            background-color: white;
            padding: 1.5rem;
            border-radius: 0.75rem;
            border: 1px solid #E2E8F0;
            box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
            margin-bottom: 1.5rem;
        }
        </style>
    """, unsafe_allow_html=True)

inject_tailwind_style()

# --- BANCO DE DADOS ---
DB_FILE = 'finance_crm.json'

def load_data():
    if not os.path.exists(DB_FILE):
        return {"users": {}, "transactions": []}
    with open(DB_FILE, 'r') as f:
        return json.load(f)

def save_data(data):
    with open(DB_FILE, 'w') as f:
        json.dump(data, f, indent=4)

db = load_data()

# --- SESSÃO ---
if 'logged_in' not in st.session_state: st.session_state['logged_in'] = False
if 'user_email' not in st.session_state: st.session_state['user_email'] = None

# --- LÓGICA DE INSIGHTS (COM CORREÇÃO DE ERRO ANTERIOR) ---
def calculate_kpis(df):
    if df.empty:
        return 0, 0, 0, 0, 0, 0, 0

    receitas = df[df['type'] == 'Receita']['amount'].sum()
    despesas = df[df['type'] == 'Despesa']['amount'].sum()
    saldo = receitas - despesas
    
    df['date_dt'] = pd.to_datetime(df['date'])
    
    if df['date_dt'].max() == df['date_dt'].min():
        dias_ativos = 1
    else:
        dias_ativos = (df['date_dt'].max() - df['date_dt'].min()).days + 1
        
    burn_rate = despesas / dias_ativos if dias_ativos > 0 else 0

    runway = 0
    if burn_rate > 0:
        runway = int(saldo / burn_rate)
    
    savings_rate = 0
    if receitas > 0:
        savings_rate = ((receitas - despesas) / receitas) * 100

    projecao = burn_rate * 30

    return saldo, receitas, despesas, burn_rate, runway, savings_rate, projecao

# --- LOGIN ---
if not st.session_state['logged_in']:
    c1, c2, c3 = st.columns([1, 1, 1])
    with c2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        # Card de Login estilo Tailwind
        st.markdown("""
        <div style="background-color: white; padding: 2rem; border-radius: 1rem; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); border: 1px solid #E2E8F0; text-align: center;">
            <div style="font-size: 3rem; margin-bottom: 1rem;">⚡</div>
            <h2 style="color: #0F172A; font-weight: 700; margin-bottom: 0.5rem;">Acessar FinCRM</h2>
            <p style="color: #64748B; margin-bottom: 2rem;">Entre com sua conta corporativa</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("Entrar com Google (Demo)"):
            st.session_state['logged_in'] = True
            st.session_state['user_email'] = "admin@empresa.com"
            st.rerun()

# --- APP PRINCIPAL ---
else:
    # --- SIDEBAR (CORRIGIDA) ---
    with st.sidebar:
        st.markdown("<h3 style='text-align: center; color: white; font-weight: 600;'>FinCRM</h3>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #94A3B8; font-size: 12px; margin-bottom: 20px;'>EDITION V2.0</p>", unsafe_allow_html=True)
        
        # O option_menu precisa de cores explícitas para garantir contraste
        selected = option_menu(
            menu_title=None,
            options=["Dashboard", "Lançamentos", "Relatórios"],
            icons=["grid-1x2", "plus-circle", "pie-chart"], # Icones Bootstrap
            default_index=0,
            styles={
                "container": {"padding": "0!important", "background-color": "transparent"},
                "icon": {"color": "#94A3B8", "font-size": "16px"}, 
                "nav-link": {
                    "font-size": "14px", 
                    "text-align": "left", 
                    "margin": "5px", 
                    "color": "#E2E8F0", # Texto quase branco
                    "background-color": "transparent"
                },
                "nav-link-selected": {
                    "background-color": "#3B82F6", # Blue-500
                    "color": "white",
                    "font-weight": "500"
                },
            }
        )
        
        st.markdown("---")
        # Botão de Logout personalizado
        if st.button("Sair da Conta"):
            st.session_state['logged_in'] = False
            st.rerun()

    # DADOS
    user_txs = [t for t in db['transactions'] if t['user'] == st.session_state['user_email']]
    df = pd.DataFrame(user_txs)

    # --- TELA 1: DASHBOARD ---
    if selected == "Dashboard":
        st.markdown("<h2 style='color: #0F172A; font-weight: 700;'>Visão Geral</h2>", unsafe_allow_html=True)
        st.markdown("<p style='color: #64748B; margin-bottom: 20px;'>Acompanhe suas métricas chave em tempo real.</p>", unsafe_allow_html=True)
        
        # KPIS
        saldo, rec, desp, burn, runway, savings, projecao = calculate_kpis(df)
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("💰 Saldo Líquido", f"R$ {saldo:,.2f}")
        col2.metric("📉 Burn Rate (Dia)", f"R$ {burn:,.2f}")
        col3.metric("📅 Runway Estimado", f"{runway} dias", delta_color="normal")
        col4.metric("📈 Taxa Poupança", f"{savings:.1f}%")

        st.markdown("<br>", unsafe_allow_html=True)
        
        # AREA PRINCIPAL
        g1, g2 = st.columns([2, 1])
        
        with g1:
            st.markdown("""
            <div class="tailwind-card">
                <h4 style="color: #0F172A; font-weight: 600; margin-bottom: 1rem;">Fluxo Financeiro</h4>
            """, unsafe_allow_html=True)
            
            if not df.empty:
                df_sorted = df.sort_values('date')
                # Gráfico com cores do Tailwind
                fig = px.bar(df_sorted, x='date', y='amount', color='type', 
                             color_discrete_map={'Receita': '#10B981', 'Despesa': '#EF4444'}, # Emerald-500 & Red-500
                             barmode='group')
                fig.update_layout(
                    paper_bgcolor="white", 
                    plot_bgcolor="white", 
                    height=300, 
                    margin=dict(l=0, r=0, t=0, b=0),
                    font={'family': 'Inter'}
                )
                fig.update_yaxes(gridcolor='#F1F5F9')
                st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
            else:
                st.info("Nenhum dado para exibir.")
            
            st.markdown("</div>", unsafe_allow_html=True)

        with g2:
            st.markdown("""
            <div class="tailwind-card">
                <h4 style="color: #0F172A; font-weight: 600; margin-bottom: 1rem;">Insights AI</h4>
            """, unsafe_allow_html=True)
            
            if not df.empty:
                st.markdown(f"""
                <div style="border-left: 4px solid #F59E0B; padding-left: 12px; margin-bottom: 15px;">
                    <p style="font-size: 12px; color: #64748B; margin: 0; text-transform: uppercase; font-weight: 600;">Projeção Mensal</p>
                    <p style="font-size: 20px; color: #0F172A; font-weight: 700; margin: 0;">R$ {projecao:,.2f}</p>
                </div>
                """, unsafe_allow_html=True)
                
                if desp > 0:
                    top_cat = df[df['type']=='Despesa'].groupby('category')['amount'].sum().idxmax()
                    st.markdown(f"""
                    <div style="border-left: 4px solid #EF4444; padding-left: 12px;">
                        <p style="font-size: 12px; color: #64748B; margin: 0; text-transform: uppercase; font-weight: 600;">Maior Gasto</p>
                        <p style="font-size: 16px; color: #0F172A; font-weight: 600; margin: 0;">{top_cat}</p>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.markdown("<p style='color: #94A3B8;'>Insira dados para análise.</p>", unsafe_allow_html=True)
            
            st.markdown("</div>", unsafe_allow_html=True)

    # --- TELA 2: LANÇAMENTOS ---
    elif selected == "Lançamentos":
        st.markdown("<h2 style='color: #0F172A; font-weight: 700;'>Lançamentos</h2>", unsafe_allow_html=True)
        
        st.markdown('<div class="tailwind-card">', unsafe_allow_html=True)
        with st.form("entry_form", clear_on_submit=True):
            c_a, c_b = st.columns(2)
            c_c, c_d = st.columns(2)
            
            with c_a: tipo = st.selectbox("Tipo de Movimento", ["Receita", "Despesa"])
            with c_b: valor = st.number_input("Valor (R$)", min_value=0.0)
            with c_c: cat = st.selectbox("Categoria", ["Vendas", "Serviços", "Marketing", "Infraestrutura", "Pessoal", "Impostos"])
            with c_d: desc = st.text_input("Descrição")
            
            st.markdown("<br>", unsafe_allow_html=True)
            if st.form_submit_button("Adicionar Registro"):
                if valor > 0:
                    new_trans = {
                        "id": int(time.time()),
                        "user": st.session_state['user_email'],
                        "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "type": tipo,
                        "amount": float(valor),
                        "category": cat,
                        "desc": desc
                    }
                    db['transactions'].append(new_trans)
                    save_data(db)
                    st.toast("Salvo com sucesso!", icon="✅")
                    time.sleep(0.5)
                    st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

        if not df.empty:
            st.markdown("### Histórico Recente")
            # Estilizando dataframe para parecer tabela Tailwind
            st.dataframe(
                df[['date', 'category', 'desc', 'type', 'amount']].sort_values(by='date', ascending=False),
                use_container_width=True,
                hide_index=True
            )

    # --- TELA 3: RELATÓRIOS ---
    elif selected == "Relatórios":
        st.markdown("<h2 style='color: #0F172A; font-weight: 700;'>Relatórios</h2>", unsafe_allow_html=True)
        
        if not df.empty:
            c1, c2 = st.columns(2)
            with c1:
                st.markdown('<div class="tailwind-card">', unsafe_allow_html=True)
                st.markdown("##### Despesas")
                df_desp = df[df['type'] == 'Despesa']
                if not df_desp.empty:
                    fig = px.pie(df_desp, values='amount', names='category', hole=0.5, color_discrete_sequence=px.colors.sequential.RdBu)
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("Sem despesas.")
                st.markdown('</div>', unsafe_allow_html=True)
            
            with c2:
                st.markdown('<div class="tailwind-card">', unsafe_allow_html=True)
                st.markdown("##### Receitas")
                df_rec = df[df['type'] == 'Receita']
                if not df_rec.empty:
                    fig = px.bar(df_rec, x='category', y='amount', color_discrete_sequence=['#10B981'])
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("Sem receitas.")
                st.markdown('</div>', unsafe_allow_html=True)
