import streamlit as st
import json
import pandas as pd
import os
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import time
from streamlit_option_menu import option_menu

# --- CONFIGURAÇÃO DA PÁGINA (WIDE MODE PARA CRM) ---
st.set_page_config(page_title="FinCRM", page_icon="📊", layout="wide")

# --- CSS ESTILO CRM / SAAS ---
def inject_crm_css():
    st.markdown("""
        <style>
        /* Fundo Geral mais corporativo */
        .stApp {
            background-color: #F4F6F9;
        }
        
        /* Sidebar */
        section[data-testid="stSidebar"] {
            background-color: #1E293B; /* Dark Slate Blue */
        }
        
        /* Cards (Metrics) */
        div[data-testid="stMetric"] {
            background-color: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-radius: 8px;
            padding: 15px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        div[data-testid="stMetricLabel"] {
            font-size: 14px;
            color: #64748B;
            font-weight: 600;
        }
        div[data-testid="stMetricValue"] {
            font-size: 24px;
            color: #1E293B;
            font-weight: 700;
        }

        /* Tabelas e Dataframes */
        .stDataFrame {
            border: 1px solid #E2E8F0;
            border-radius: 8px;
            background-color: white;
        }
        
        /* Inputs Estilo Form */
        .stTextInput, .stNumberInput, .stSelectbox {
            background-color: white;
        }

        /* Títulos */
        h1, h2, h3 {
            color: #0F172A;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        
        /* Botões Primários */
        .stButton > button {
            background-color: #3B82F6; /* Blue 500 */
            color: white;
            border-radius: 6px;
            border: none;
            font-weight: 500;
        }
        .stButton > button:hover {
            background-color: #2563EB;
        }
        </style>
    """, unsafe_allow_html=True)

inject_crm_css()

# --- DADOS E FUNÇÕES ---
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

if 'logged_in' not in st.session_state: st.session_state['logged_in'] = False
if 'user_email' not in st.session_state: st.session_state['user_email'] = None

# --- LÓGICA DE INSIGHTS AVANÇADOS (CRM INTELLIGENCE) ---
def calculate_kpis(df):
    if df.empty:
        return 0, 0, 0, 0, 0, "Sem dados"

    receitas = df[df['type'] == 'Receita']['amount'].sum()
    despesas = df[df['type'] == 'Despesa']['amount'].sum()
    saldo = receitas - despesas
    
    # 1. Burn Rate (Gasto Médio Diário)
    # Pega o range de datas
    df['date_dt'] = pd.to_datetime(df['date'])
    dias_ativos = (df['date_dt'].max() - df['date_dt'].min()).days + 1
    if dias_ativos < 1: dias_ativos = 1
    burn_rate = despesas / dias_ativos

    # 2. Runway (Dias de Sobrevivência)
    runway = 0
    if burn_rate > 0:
        runway = int(saldo / burn_rate)
    
    # 3. Savings Rate
    savings_rate = 0
    if receitas > 0:
        savings_rate = ((receitas - despesas) / receitas) * 100

    # 4. Projeção Mensal (Simples)
    projecao = burn_rate * 30

    return saldo, receitas, despesas, burn_rate, runway, savings_rate, projecao

# --- LOGIN SCREEN ---
if not st.session_state['logged_in']:
    col1, col2, col3 = st.columns([1,1,1])
    with col2:
        st.markdown("<br><br><br>", unsafe_allow_html=True)
        st.markdown("<div style='background: white; padding: 40px; border-radius: 8px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); text-align: center;'>", unsafe_allow_html=True)
        st.markdown("## 🚀 FinCRM")
        st.markdown("Gestão financeira para alta performance.")
        st.write("")
        if st.button("Login com Google Account"):
            st.session_state['logged_in'] = True
            st.session_state['user_email'] = "admin@empresa.com"
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

# --- DASHBOARD PRINCIPAL ---
else:
    # SIDEBAR NAVEGAÇÃO
    with st.sidebar:
        st.markdown("### FinCRM v1.0")
        selected = option_menu(
            menu_title=None,
            options=["Dashboard", "Lançamentos", "Relatórios"],
            icons=["speedometer2", "pencil-square", "graph-up-arrow"],
            menu_icon="cast",
            default_index=0,
            styles={
                "container": {"padding": "0!important", "background-color": "#1E293B"},
                "icon": {"color": "#94A3B8", "font-size": "18px"}, 
                "nav-link": {"font-size": "14px", "text-align": "left", "margin":"5px", "--hover-color": "#334155", "color": "white"},
                "nav-link-selected": {"background-color": "#3B82F6"},
            }
        )
        st.markdown("---")
        if st.button("Logout"):
            st.session_state['logged_in'] = False
            st.rerun()

    # PROCESSAMENTO DE DADOS
    user_txs = [t for t in db['transactions'] if t['user'] == st.session_state['user_email']]
    df = pd.DataFrame(user_txs)
    
    # --- PÁGINA 1: DASHBOARD ---
    if selected == "Dashboard":
        st.markdown("## Visão Geral")
        
        # KPIS
        saldo, rec, desp, burn, runway, savings, projecao = calculate_kpis(df)
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Saldo Líquido", f"R$ {saldo:,.2f}", delta=f"{savings:.1f}% Margem")
        c2.metric("Receita Total", f"R$ {rec:,.2f}")
        c3.metric("Burn Rate (Diário)", f"R$ {burn:,.2f}", delta_color="inverse", help="Quanto você gasta por dia em média")
        c4.metric("Runway (Dias)", f"{runway} dias", help="Quanto tempo o dinheiro dura se a receita parar")

        # ÁREA DE GRÁFICOS
        st.markdown("---")
        g1, g2 = st.columns([2, 1])
        
        with g1:
            st.markdown("##### 📈 Fluxo de Caixa Temporal")
            if not df.empty:
                # Gráfico de Área CRM Style
                df_sorted = df.sort_values('date')
                df_sorted['cumulative'] = 0 # Placeholder logic for nice chart
                
                fig = px.bar(df_sorted, x='date', y='amount', color='type', barmode='group',
                             color_discrete_map={'Receita': '#10B981', 'Despesa': '#EF4444'})
                fig.update_layout(paper_bgcolor="white", plot_bgcolor="white", height=350, margin=dict(l=20, r=20, t=20, b=20))
                fig.update_yaxes(showgrid=True, gridcolor='#F1F5F9')
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Sem dados para exibir o gráfico.")

        with g2:
            st.markdown("##### 🧠 AI Insights")
            st.markdown("""
            <div style="background-color: white; padding: 15px; border-radius: 8px; border: 1px solid #E2E8F0; height: 350px;">
            """, unsafe_allow_html=True)
            
            if not df.empty:
                # Insight 1: Projeção
                st.markdown(f"**Projeção de Gasto Mensal:**<br><span style='font-size: 20px; color: #EF4444'>R$ {projecao:,.2f}</span>", unsafe_allow_html=True)
                st.progress(min(burn/1000 if burn > 0 else 0, 1.0))
                st.caption("Baseado na média diária atual.")
                
                st.markdown("---")
                
                # Insight 2: Alerta de Categoria
                if desp > 0:
                    top_cat = df[df['type']=='Despesa'].groupby('category')['amount'].sum().idxmax()
                    val_cat = df[df['type']=='Despesa'].groupby('category')['amount'].sum().max()
                    st.markdown(f"**Maior Ofensor:**<br>{top_cat} (R$ {val_cat:.2f})", unsafe_allow_html=True)
                    st.caption("Considere reduzir custos nesta área.")
                
            else:
                st.write("Insira dados para gerar insights.")
            
            st.markdown("</div>", unsafe_allow_html=True)

    # --- PÁGINA 2: LANÇAMENTOS ---
    elif selected == "Lançamentos":
        st.markdown("## Gestão de Lançamentos")
        
        with st.form("entry_form", clear_on_submit=True):
            col_a, col_b, col_c, col_d = st.columns(4)
            with col_a:
                tipo = st.selectbox("Tipo", ["Receita", "Despesa"])
            with col_b:
                valor = st.number_input("Valor", min_value=0.0, step=100.0)
            with col_c:
                cat = st.selectbox("Categoria", ["Vendas", "Serviços", "Marketing", "Infraestrutura", "Pessoal", "Impostos"])
            with col_d:
                desc = st.text_input("Descrição", placeholder="Ex: Pagamento AWS")
            
            submitted = st.form_submit_button("💾 Salvar Registro")
            
            if submitted and valor > 0:
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
                st.success("Registro adicionado com sucesso.")
                time.sleep(1)
                st.rerun()

        st.markdown("### Últimos Registros")
        if not df.empty:
            # Table estilo CRM (Clean)
            st.dataframe(
                df[['date', 'category', 'desc', 'type', 'amount']].sort_values(by='date', ascending=False),
                use_container_width=True,
                hide_index=True,
                column_config={
                    "date": "Data",
                    "category": "Categoria",
                    "desc": "Descrição",
                    "type": "Tipo",
                    "amount": st.column_config.NumberColumn("Valor", format="R$ %.2f")
                }
            )

    # --- PÁGINA 3: RELATÓRIOS ---
    elif selected == "Relatórios":
        st.markdown("## Análise Detalhada")
        if not df.empty:
            col_r1, col_r2 = st.columns(2)
            
            with col_r1:
                st.markdown("#### Despesas por Categoria")
                df_desp = df[df['type'] == 'Despesa']
                fig_pie = px.pie(df_desp, values='amount', names='category', hole=0.4)
                st.plotly_chart(fig_pie, use_container_width=True)
                
            with col_r2:
                st.markdown("#### Composição da Receita")
                df_rec = df[df['type'] == 'Receita']
                if not df_rec.empty:
                    fig_bar = px.bar(df_rec, x='category', y='amount')
                    st.plotly_chart(fig_bar, use_container_width=True)
                else:
                    st.info("Sem receitas registradas.")
