import streamlit as st
import pandas as pd
import json
import os
import plotly.express as px
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from streamlit_option_menu import option_menu

# --- CONFIGURAÇÃO INICIAL ---
st.set_page_config(page_title="FinSaaS Pro", page_icon="💰", layout="wide")

# --- CSS (DESIGN) ---
def inject_custom_css():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700&display=swap');
        .stApp { background-color: #F4F7FC; font-family: 'Nunito', sans-serif; }
        .block-container { padding-top: 1.5rem; padding-bottom: 3rem; }
        .white-card {
            background-color: #FFFFFF; border-radius: 16px; padding: 24px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.03); margin-bottom: 20px; height: 100%;
            border: 1px solid #F0F2F5;
        }
        .step-item { display: flex; align-items: flex-start; margin-bottom: 20px; position: relative; }
        .step-icon {
            width: 32px; height: 32px; border-radius: 50%; display: flex; 
            align-items: center; justify-content: center; color: white; 
            font-weight: bold; z-index: 2; margin-right: 15px; flex-shrink: 0;
            font-size: 14px;
        }
        .step-line {
            position: absolute; left: 15px; top: 32px; bottom: -25px; width: 2px;
            background-color: #E0E0E0; z-index: 1;
        }
        .step-last .step-line { display: none; }
        .color-card {
            border-radius: 16px; padding: 20px; color: white;
            box-shadow: 0 8px 15px rgba(0,0,0,0.05); display: flex;
            align-items: center; justify-content: space-between; margin-bottom: 15px;
            transition: transform 0.2s;
        }
        .color-card:hover { transform: translateY(-2px); }
        .cc-icon {
            background-color: rgba(255,255,255,0.25); width: 48px; height: 48px;
            border-radius: 12px; display: flex; align-items: center; justify-content: center;
            font-size: 22px;
        }
        .bg-blue { background: linear-gradient(135deg, #2D9CDB 0%, #2F80ED 100%); }
        .bg-green { background: linear-gradient(135deg, #27AE60 0%, #219653 100%); }
        .bg-red { background: linear-gradient(135deg, #EB5757 0%, #C0392B 100%); }
        .bg-purple { background: linear-gradient(135deg, #9B51E0 0%, #8E44AD 100%); }
        .val-big { font-size: 24px; font-weight: 800; }
        .lbl-small { font-size: 13px; opacity: 0.9; font-weight: 500; }
        .js-plotly-plot .plotly .modebar { display: none !important; }
        div[data-testid="stDataFrame"] { border-radius: 10px; overflow: hidden; border: 1px solid #eee; }
        div.stButton > button:first-child {
            background-color: #2D9CDB; color: white; border: none; border-radius: 8px;
        }
        </style>
    """, unsafe_allow_html=True)

inject_custom_css()

# --- DATABASE ---
DB_FILE = 'finance_final_v4.json'

def init_db():
    if not os.path.exists(DB_FILE):
        default_db = {
            "transactions": [],
            "cards": [
                {"name": "Nubank", "closing_day": 20, "due_day": 27, "limit": 5000},
                {"name": "Inter", "closing_day": 10, "due_day": 17, "limit": 3000}
            ],
            "goals": [
                {"name": "Reserva", "target": 10000, "current": 1000, "color": "#27AE60"}
            ]
        }
        with open(DB_FILE, 'w') as f: json.dump(default_db, f)

def load_db():
    init_db()
    try:
        with open(DB_FILE, 'r') as f: return json.load(f)
    except:
        return {"transactions": [], "cards": [], "goals": []}

def save_db(data):
    with open(DB_FILE, 'w') as f: json.dump(data, f, indent=4)

# --- PROCESSAMENTO ---
def process_data(db, selected_date):
    txs = db.get('transactions', [])
    cards_list = db.get('cards', []) 
    cards = {c['name']: c for c in cards_list}
    
    # DEFINIR COLUNAS PADRÃO (Isso evita o KeyError)
    cols = ['id', 'date', 'type', 'amount', 'account', 'category', 'status', 'desc', 'competencia', 'comp_mes', 'comp_ano']
    
    # Se não houver transações, retorna DataFrames vazios mas COM COLUNAS
    if not txs:
        empty_df = pd.DataFrame(columns=cols)
        return empty_df, empty_df, 0.0

    df = pd.DataFrame(txs)
    
    # Verificação de segurança
    if 'date' not in df.columns or 'amount' not in df.columns:
         empty_df = pd.DataFrame(columns=cols)
         return empty_df, empty_df, 0.0

    df['date'] = pd.to_datetime(df['date'])
    df['amount'] = df['amount'].astype(float)
    
    def get_competence_date(row):
        if row.get('account') in cards and row.get('type') == 'Despesa':
            card_info = cards[row['account']]
            closing_day = int(card_info['closing_day'])
            if row['date'].day >= closing_day:
                return row['date'] + relativedelta(months=1)
        return row['date']

    df['competencia'] = df.apply(get_competence_date, axis=1)
    df['comp_mes'] = df['competencia'].dt.month
    df['comp_ano'] = df['competencia'].dt.year

    # 1. Filtro Mês Atual
    df_mes = df[(df['comp_mes'] == selected_date.month) & (df['comp_ano'] == selected_date.year)]
    
    # 2. Saldo Anterior
    mask_anterior = (df['competencia'] < datetime(selected_date.year, selected_date.month, 1))
    df_anterior = df[mask_anterior]
    
    rec_ant = df_anterior[(df_anterior['type'] == 'Receita') & (df_anterior['status'] == 'Pago')]['amount'].sum()
    desp_ant = df_anterior[(df_anterior['type'] == 'Despesa') & (df_anterior['status'] == 'Pago')]['amount'].sum()
    saldo_inicial = rec_ant - desp_ant

    return df, df_mes, saldo_inicial

# --- SIDEBAR ---
db_data = load_db()

with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/10543/10543268.png", width=60)
    st.markdown("### FinSaaS")
    
    col_mes, col_ano = st.columns(2)
    with col_mes:
        mes_nomes = {1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril", 5: "Maio", 6: "Junho", 
                     7: "Julho", 8: "Agosto", 9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"}
        sel_mes = st.selectbox("Mês", list(mes_nomes.keys()), index=datetime.now().month-1, format_func=lambda x: mes_nomes[x])
    with col_ano:
        sel_ano = st.number_input("Ano", value=datetime.now().year, step=1)
    
    ref_date = datetime(sel_ano, sel_mes, 1)
    st.markdown("---")
    
    selected = option_menu(
        menu_title=None,
        options=["Dashboard", "Extrato", "Cartões", "Metas", "Nova Transação"],
        icons=["columns-gap", "list-check", "credit-card", "trophy", "plus-circle-fill"],
        default_index=0,
        styles={
            "container": {"background-color": "transparent"},
            "nav-link-selected": {"background-color": "#2D9CDB", "font-weight": "600"},
        }
    )
    st.info(f"📅 **{mes_nomes[sel_mes]}/{sel_ano}**")

df_full, df_view, saldo_inicial = process_data(db_data, ref_date)

# --- DASHBOARD ---
if selected == "Dashboard":
    # Garante que as colunas existem antes de somar, mesmo se df_view estiver vazio
    if not df_view.empty:
        receitas_mes = df_view[df_view['type'] == 'Receita']['amount'].sum()
        despesas_mes = df_view[df_view['type'] == 'Despesa']['amount'].sum()
        rec_pago = df_view[(df_view['type'] == 'Receita') & (df_view['status'] == 'Pago')]['amount'].sum()
        desp_pago = df_view[(df_view['type'] == 'Despesa') & (df_view['status'] == 'Pago')]['amount'].sum()
        pendente_val = df_view[(df_view['type'] == 'Despesa') & (df_view['status'] == 'Pendente')]['amount'].sum()
    else:
        receitas_mes = 0.0
        despesas_mes = 0.0
        rec_pago = 0.0
        desp_pago = 0.0
        pendente_val = 0.0
    
    saldo_previsto = saldo_inicial + receitas_mes - despesas_mes
    saldo_atual = saldo_inicial + rec_pago - desp_pago

    col_main, col_side = st.columns([3, 1])

    with col_main:
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(f'<div class="color-card bg-green"><div><div class="lbl-small">Receitas</div><div class="val-big">R$ {receitas_mes:,.2f}</div></div><div class="cc-icon">↑</div></div>', unsafe_allow_html=True)
        with c2:
            st.markdown(f'<div class="color-card bg-red"><div><div class="lbl-small">Despesas</div><div class="val-big">R$ {despesas_mes:,.2f}</div></div><div class="cc-icon">↓</div></div>', unsafe_allow_html=True)
        with c3:
            st.markdown(f'<div class="color-card bg-blue"><div><div class="lbl-small">Balanço</div><div class="val-big">R$ {(receitas_mes - despesas_mes):,.2f}</div></div><div class="cc-icon">⚖️</div></div>', unsafe_allow_html=True)

        g1, g2 = st.columns([2, 1])
        with g1:
            st.markdown('<div class="white-card"><h5>Fluxo Diário</h5>', unsafe_allow_html=True)
            if not df_view.empty:
                daily = df_view.groupby('date')['amount'].sum().reset_index()
                fig = px.bar(daily, x='date', y='amount', color_discrete_sequence=['#2D9CDB'])
                fig.update_layout(height=200, margin=dict(l=0,r=0,t=0,b=0), paper_bgcolor='white', plot_bgcolor='white')
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Sem dados.")
            st.markdown('</div>', unsafe_allow_html=True)
            
        with g2:
            st.markdown('<div class="white-card"><h5>Categorias</h5>', unsafe_allow_html=True)
            if not df_view.empty:
                df_desp = df_view[df_view['type'] == 'Despesa']
                if not df_desp.empty:
                    fig = px.pie(df_desp, values='amount', names='category', hole=0.6, color_discrete_sequence=px.colors.qualitative.Pastel)
                    fig.update_layout(height=200, showlegend=False, margin=dict(l=0,r=0,t=0,b=0))
                    st.plotly_chart(fig, use_container_width=True)
                else: st.write("Sem despesas.")
            else: st.write("Sem dados.")
            st.markdown('</div>', unsafe_allow_html=True)

    with col_side:
        st.markdown(f"""
        <div class="white-card">
            <h4>Evolução</h4>
            <div class="step-item"><div class="step-line"></div><div class="step-icon bg-blue">1</div><div><div style="font-weight:700">R$ {saldo_inicial:,.2f}</div><div style="font-size:12px;color:#888">Inicial</div></div></div>
            <div class="step-item"><div class="step-line"></div><div class="step-icon bg-green">2</div><div><div style="font-weight:700">R$ {saldo_atual:,.2f}</div><div style="font-size:12px;color:#888">Atual</div></div></div>
            <div class="step-item step-last"><div class="step-icon bg-purple">3</div><div><div style="font-weight:700">R$ {saldo_previsto:,.2f}</div><div style="font-size:12px;color:#888">Previsto</div></div></div>
            <hr>
            <div style="background:#FEF3C7;padding:10px;border-radius:8px;border:1px solid #FCD34D;">
                <div style="font-weight:700;color:#D97706;font-size:12px;">⚠️ Pendente</div>
                <div style="color:#B45309;">R$ {pendente_val:,.2f}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

# --- EXTRATO ---
elif selected == "Extrato":
    st.markdown("### 📝 Extrato")
    if df_full.empty:
        st.warning("Sem dados.")
    else:
        df_edit = df_full.sort_values(by='date', ascending=False).copy()
        df_edit['Excluir'] = False
        
        edited_df = st.data_editor(
            df_edit,
            column_config={
                "Excluir": st.column_config.CheckboxColumn(help="Deletar?", default=False),
                "id": None, "competencia": None, "comp_mes": None, "comp_ano": None,
                "date": st.column_config.DateColumn("Data", format="DD/MM/YYYY"),
                "amount": st.column_config.NumberColumn("Valor", format="R$ %.2f"),
                "type": st.column_config.SelectboxColumn("Tipo", options=["Receita", "Despesa"], required=True),
                "account": st.column_config.SelectboxColumn("Conta", options=["Carteira"] + [c['name'] for c in db_data['cards']]),
                "status": st.column_config.SelectboxColumn("Status", options=["Pago", "Pendente"]),
            },
            hide_index=True, use_container_width=True, num_rows="dynamic"
        )
        
        if st.button("💾 Salvar"):
            final_df = edited_df[edited_df['Excluir'] == False].drop(columns=['Excluir', 'competencia', 'comp_mes', 'comp_ano'], errors='ignore')
            final_df['date'] = final_df['date'].apply(lambda x: x.strftime('%Y-%m-%d') if isinstance(x, (datetime, date)) else x)
            db_data['transactions'] = final_df.to_dict(orient='records')
            save_db(db_data)
            st.success("Salvo!")
            st.rerun()

# --- CARTÕES ---
elif selected == "Cartões":
    st.markdown("### 💳 Cartões")
    c1, c2 = st.columns([1, 2])
    with c1:
        with st.container(border=True):
            with st.form("add_card"):
                c_nome = st.text_input("Nome")
                c_lim = st.number_input("Limite", min_value=0.0)
                d1, d2 = st.columns(2)
                cf = d1.number_input("Fechamento", 1, 31, 20)
                cv = d2.number_input("Vencimento", 1, 31, 27)
                if st.form_submit_button("Adicionar"):
                    db_data['cards'].append({"name": c_nome, "limit": c_lim, "closing_day": cf, "due_day": cv})
                    save_db(db_data)
                    st.rerun()
    with c2:
        if not db_data['cards']: st.info("Sem cartões.")
        for card in db_data['cards']:
            if not df_view.empty:
                gasto = df_view[(df_view['account'] == card['name']) & (df_view['type'] == 'Despesa')]['amount'].sum()
            else: gasto = 0.0
            pct = (gasto / card['limit'] * 100) if card['limit'] > 0 else 0
            st.markdown(f"""
            <div class="white-card" style="padding:15px; margin-bottom:10px;">
                <div style="display:flex;justify-content:space-between"><b>{card['name']}</b><span style="font-size:12px;background:#eee;padding:2px 6px;border-radius:4px">Vence dia {card['due_day']}</span></div>
                <div style="display:flex;justify-content:space-between;margin-top:10px"><span>Fatura Atual</span><b style="color:#EB5757">R$ {gasto:,.2f}</b></div>
                <div style="background:#eee;height:6px;border-radius:3px;margin-top:5px"><div style="width:{min(pct,100)}%;background:#2D9CDB;height:100%;border-radius:3px"></div></div>
                <div style="font-size:11px;color:#999;margin-top:5px">Limite: R$ {card['limit']:,.2f}</div>
            </div>
            """, unsafe_allow_html=True)

# --- METAS ---
elif selected == "Metas":
    st.markdown("### 🎯 Metas")
    with st.expander("Nova Meta"):
        with st.form("ng"):
            mn = st.text_input("Nome")
            mt = st.number_input("Alvo", min_value=0.0)
            mc = st.number_input("Atual", min_value=0.0)
            mco = st.color_picker("Cor", "#27AE60")
            if st.form_submit_button("Criar"):
                db_data['goals'].append({"name": mn, "target": mt, "current": mc, "color": mco})
                save_db(db_data)
                st.rerun()
    
    cols = st.columns(3)
    for i, g in enumerate(db_data['goals']):
        pct = (g['current'] / g['target'] * 100) if g['target'] > 0 else 0
        with cols[i%3]:
            st.markdown(f"""
            <div class="white-card">
                <b>{g['name']}</b>
                <h3 style="color:{g['color']}">R$ {g['current']:,.0f} <small style="font-size:12px;color:#ccc">/ {g['target']:,.0f}</small></h3>
                <div style="background:#eee;height:8px;border-radius:4px"><div style="width:{min(pct,100)}%;background:{g['color']};height:100%;border-radius:4px"></div></div>
            </div>
            """, unsafe_allow_html=True)

# --- NOVA TRANSAÇÃO ---
elif selected == "Nova Transação":
    st.markdown("### ➕ Movimentação")
    c_main = st.columns([1,2,1])
    with c_main[1]:
        with st.container(border=True):
            with st.form("nt"):
                tipo = st.selectbox("Tipo", ["Despesa", "Receita"])
                valor = st.number_input("Valor", min_value=0.0, step=10.0)
                c1, c2 = st.columns(2)
                dt = c1.date_input("Data", datetime.now())
                ct = c2.selectbox("Conta", ["Carteira"] + [c['name'] for c in db_data['cards']])
                cat = st.selectbox("Categoria", ["Alimentação", "Moradia", "Lazer", "Transporte", "Saúde", "Salário", "Outros"])
                stt = st.radio("Status", ["Pago", "Pendente"], horizontal=True)
                desc = st.text_input("Descrição")
                
                if st.form_submit_button("Salvar"):
                    nt = {
                        "id": int(datetime.now().timestamp()),
                        "date": dt.strftime("%Y-%m-%d"),
                        "type": tipo, "amount": valor, "account": ct,
                        "category": cat, "status": stt, "desc": desc
                    }
                    db_data['transactions'].append(nt)
                    save_db(db_data)
                    st.success("Salvo!")
