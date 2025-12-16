import streamlit as st
import pandas as pd
import json
import os
import plotly.express as px
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from streamlit_option_menu import option_menu
import time

# --- CONFIGURAÇÃO INICIAL ---
st.set_page_config(page_title="FinSaaS Seguro", page_icon="🔐", layout="wide")

# --- CSS PERSONALIZADO ---
def inject_custom_css():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700&display=swap');
        .stApp { background-color: #F4F7FC; font-family: 'Nunito', sans-serif; }
        
        .block-container { padding-top: 1.5rem; padding-bottom: 3rem; }
        
        /* Cards e Containers */
        .white-card {
            background-color: #FFFFFF; border-radius: 16px; padding: 24px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.03); margin-bottom: 20px;
            border: 1px solid #F0F2F5;
        }
        
        /* Login Box */
        .login-card {
            max-width: 400px; margin: 0 auto; background: white; 
            padding: 40px; border-radius: 20px; box-shadow: 0 10px 30px rgba(0,0,0,0.08);
            text-align: center;
        }
        
        /* Elementos UI */
        .color-card {
            border-radius: 16px; padding: 20px; color: white;
            box-shadow: 0 8px 15px rgba(0,0,0,0.05); display: flex;
            align-items: center; justify-content: space-between; margin-bottom: 15px;
        }
        .cc-icon {
            background-color: rgba(255,255,255,0.25); width: 48px; height: 48px;
            border-radius: 12px; display: flex; align-items: center; justify-content: center; font-size: 22px;
        }
        
        .bg-blue { background: linear-gradient(135deg, #2D9CDB 0%, #2F80ED 100%); }
        .bg-green { background: linear-gradient(135deg, #27AE60 0%, #219653 100%); }
        .bg-red { background: linear-gradient(135deg, #EB5757 0%, #C0392B 100%); }
        
        /* Botões */
        div.stButton > button:first-child {
            background-color: #2D9CDB; color: white; border: none; border-radius: 8px; font-weight: 600; width: 100%;
        }
        div.stButton > button:hover { background-color: #1B85C4; }
        
        /* Dataframes e Plotly */
        div[data-testid="stDataFrame"] { border-radius: 10px; overflow: hidden; border: 1px solid #eee; }
        .js-plotly-plot .plotly .modebar { display: none !important; }
        </style>
    """, unsafe_allow_html=True)

inject_custom_css()

# --- GESTÃO DE DADOS (JSON MULTI-USER) ---
DB_FILE = 'finsaas_secure_db.json'

def init_db():
    if not os.path.exists(DB_FILE):
        # Estrutura: 'users' guarda credenciais, 'data' guarda os dados financeiros por usuario
        db_structure = {
            "users": {}, # { "email": { "name": "Nome", "password": "123" } }
            "data": {}   # { "email": { "transactions": [], ... } }
        }
        with open(DB_FILE, 'w') as f: json.dump(db_structure, f)

def load_full_db():
    init_db()
    try:
        with open(DB_FILE, 'r') as f: return json.load(f)
    except:
        return {"users": {}, "data": {}}

def save_full_db(data):
    with open(DB_FILE, 'w') as f: json.dump(data, f, indent=4)

# --- SISTEMA DE AUTENTICAÇÃO ---
if 'user_email' not in st.session_state: st.session_state['user_email'] = None
if 'user_name' not in st.session_state: st.session_state['user_name'] = None

def login_user(email, password):
    db = load_full_db()
    user = db['users'].get(email)
    if user and user['password'] == password:
        st.session_state['user_email'] = email
        st.session_state['user_name'] = user['name']
        return True
    return False

def register_user(name, email, password):
    db = load_full_db()
    if email in db['users']:
        return False # Usuário já existe
    
    # Cria Usuário
    db['users'][email] = {"name": name, "password": password}
    
    # Cria Template de Dados Vazio para o Usuário
    db['data'][email] = {
        "transactions": [],
        "cards": [],
        "accounts": ["Carteira"],
        "goals": []
    }
    save_full_db(db)
    return True

def get_user_data():
    email = st.session_state['user_email']
    db = load_full_db()
    # Retorna os dados do usuário logado ou template vazio se der erro
    return db['data'].get(email, {"transactions": [], "cards": [], "accounts": [], "goals": []})

def save_user_data(user_data):
    email = st.session_state['user_email']
    db = load_full_db()
    db['data'][email] = user_data
    save_full_db(db)

# --- TELAS DE LOGIN / CADASTRO ---
if not st.session_state['user_email']:
    col1, col2, col3 = st.columns([1,1,1])
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("""
        <div class="login-card">
            <h1>🔐 FinSaaS</h1>
            <p>Gerencie suas finanças com segurança.</p>
        </div>
        """, unsafe_allow_html=True)
        
        tab_login, tab_register = st.tabs(["Entrar", "Criar Conta"])
        
        with tab_login:
            email_l = st.text_input("E-mail", key="l_email")
            pass_l = st.text_input("Senha", type="password", key="l_pass")
            if st.button("Acessar Sistema"):
                if login_user(email_l, pass_l):
                    st.rerun()
                else:
                    st.error("E-mail ou senha incorretos.")

        with tab_register:
            name_r = st.text_input("Seu Nome")
            email_r = st.text_input("E-mail", key="r_email")
            pass_r = st.text_input("Senha", type="password", key="r_pass")
            if st.button("Cadastrar"):
                if name_r and email_r and pass_r:
                    if register_user(name_r, email_r, pass_r):
                        st.success("Conta criada! Faça login.")
                    else:
                        st.error("E-mail já cadastrado.")
                else:
                    st.warning("Preencha todos os campos.")
    
    st.stop() # Para a execução aqui se não estiver logado

# ==================================================================================================
# APLICAÇÃO PRINCIPAL (SÓ CARREGA SE LOGADO)
# ==================================================================================================

# Carrega dados APENAS do usuário logado
db_data = get_user_data()
user_name = st.session_state['user_name']

# --- FUNÇÃO DE PROCESSAMENTO (ENGINE) ---
def process_data(user_db, selected_date):
    txs = user_db.get('transactions', [])
    cards_list = user_db.get('cards', [])
    cards = {c['name']: c for c in cards_list}
    
    cols = ['id', 'date', 'type', 'amount', 'account', 'category', 'status', 'desc', 'competencia', 'comp_mes', 'comp_ano']
    
    if not txs:
        empty = pd.DataFrame(columns=cols)
        return empty, empty, 0.0

    df = pd.DataFrame(txs)
    if 'date' not in df.columns or 'amount' not in df.columns:
        empty = pd.DataFrame(columns=cols)
        return empty, empty, 0.0

    df['date'] = pd.to_datetime(df['date'])
    df['amount'] = df['amount'].astype(float)
    
    def get_competence(row):
        if row.get('account') in cards and row.get('type') == 'Despesa':
            try:
                closing = int(cards[row['account']]['closing_day'])
                if row['date'].day >= closing:
                    return row['date'] + relativedelta(months=1)
            except: pass
        return row['date']

    df['competencia'] = df.apply(get_competence, axis=1)
    df['comp_mes'] = df['competencia'].dt.month
    df['comp_ano'] = df['competencia'].dt.year

    df_view = df[(df['comp_mes'] == selected_date.month) & (df['comp_ano'] == selected_date.year)]
    
    mask_ant = df['competencia'] < datetime(selected_date.year, selected_date.month, 1)
    df_ant = df[mask_ant]
    
    rec = df_ant[(df_ant['type'] == 'Receita') & (df_ant['status'] == 'Pago')]['amount'].sum()
    desp = df_ant[(df_ant['type'] == 'Despesa') & (df_ant['status'] == 'Pago')]['amount'].sum()
    
    return df, df_view, (rec - desp)

# --- SIDEBAR ---
with st.sidebar:
    st.markdown(f"### Olá, {user_name} 👋")
    
    # Filtro Data
    c1, c2 = st.columns(2)
    meses = {1:"Jan",2:"Fev",3:"Mar",4:"Abr",5:"Mai",6:"Jun",7:"Jul",8:"Ago",9:"Set",10:"Out",11:"Nov",12:"Dez"}
    sel_mes = c1.selectbox("Mês", list(meses.keys()), index=datetime.now().month-1, format_func=lambda x: meses[x])
    sel_ano = c2.number_input("Ano", value=datetime.now().year)
    ref_date = datetime(sel_ano, sel_mes, 1)
    
    st.markdown("---")
    selected = option_menu(
        menu_title=None,
        options=["Dashboard", "Extrato", "Cadastros", "Metas", "Nova Transação"],
        icons=["grid", "table", "wallet", "trophy", "plus-circle"],
        default_index=0,
    )
    st.markdown("---")
    if st.button("Sair / Logout"):
        st.session_state['user_email'] = None
        st.rerun()

# Processa dados
df_full, df_view, saldo_inicial = process_data(db_data, ref_date)

# --- PÁGINAS ---

if selected == "Dashboard":
    if not df_view.empty:
        rec = df_view[df_view['type']=='Receita']['amount'].sum()
        desp = df_view[df_view['type']=='Despesa']['amount'].sum()
        saldo_mes = rec - desp
    else:
        rec = 0.0; desp = 0.0; saldo_mes = 0.0

    c1, c2, c3 = st.columns(3)
    c1.markdown(f'<div class="color-card bg-green"><div><div class="lbl-small">Receitas</div><div class="val-big">R$ {rec:,.2f}</div></div><div class="cc-icon">↑</div></div>', unsafe_allow_html=True)
    c2.markdown(f'<div class="color-card bg-red"><div><div class="lbl-small">Despesas</div><div class="val-big">R$ {desp:,.2f}</div></div><div class="cc-icon">↓</div></div>', unsafe_allow_html=True)
    c3.markdown(f'<div class="color-card bg-blue"><div><div class="lbl-small">Balanço</div><div class="val-big">R$ {saldo_mes:,.2f}</div></div><div class="cc-icon">⚖️</div></div>', unsafe_allow_html=True)

    g1, g2 = st.columns([2,1])
    with g1:
        st.markdown('<div class="white-card"><h5>Fluxo Diário</h5>', unsafe_allow_html=True)
        if not df_view.empty:
            daily = df_view.groupby('date')['amount'].sum().reset_index()
            fig = px.bar(daily, x='date', y='amount')
            fig.update_layout(height=250, margin=dict(l=0,r=0,t=0,b=0))
            st.plotly_chart(fig, use_container_width=True)
        else: st.info("Sem dados.")
        st.markdown('</div>', unsafe_allow_html=True)

    with g2:
        st.markdown('<div class="white-card"><h5>Categorias</h5>', unsafe_allow_html=True)
        if not df_view.empty:
            df_pie = df_view[df_view['type']=='Despesa']
            if not df_pie.empty:
                fig = px.pie(df_pie, values='amount', names='category', hole=0.6)
                fig.update_layout(height=250, showlegend=False, margin=dict(l=0,r=0,t=0,b=0))
                st.plotly_chart(fig, use_container_width=True)
            else: st.info("Sem despesas.")
        else: st.info("Sem dados.")
        st.markdown('</div>', unsafe_allow_html=True)

elif selected == "Extrato":
    st.markdown("### 📝 Extrato")
    if df_full.empty:
        st.warning("Sem transações.")
    else:
        df_edit = df_full.sort_values('date', ascending=False).copy()
        df_edit['Excluir'] = False
        contas = db_data.get('accounts', []) + [c['name'] for c in db_data.get('cards', [])]
        
        edited = st.data_editor(
            df_edit,
            column_config={
                "Excluir": st.column_config.CheckboxColumn(default=False),
                "id": None, "competencia": None, "comp_mes": None, "comp_ano": None,
                "date": st.column_config.DateColumn("Data", format="DD/MM/YYYY"),
                "amount": st.column_config.NumberColumn("Valor", format="R$ %.2f"),
                "type": st.column_config.SelectboxColumn("Tipo", options=["Receita", "Despesa"]),
                "account": st.column_config.SelectboxColumn("Conta", options=contas),
                "category": st.column_config.SelectboxColumn("Categoria", options=["Alimentação", "Moradia", "Lazer", "Transporte", "Saúde", "Salário", "Outros"]),
                "status": st.column_config.SelectboxColumn("Status", options=["Pago", "Pendente"]),
            },
            hide_index=True, use_container_width=True, num_rows="dynamic"
        )
        if st.button("Salvar Extrato"):
            final = edited[edited['Excluir']==False].drop(columns=['Excluir', 'competencia', 'comp_mes', 'comp_ano'], errors='ignore')
            final['date'] = final['date'].apply(lambda x: x.strftime('%Y-%m-%d') if isinstance(x, (datetime, date)) else x)
            db_data['transactions'] = final.to_dict(orient='records')
            save_user_data(db_data)
            st.success("Salvo!")
            st.rerun()

elif selected == "Cadastros":
    st.markdown("### ⚙️ Cadastros")
    tab1, tab2 = st.tabs(["Cartões", "Contas"])
    
    with tab1:
        cdf = pd.DataFrame(db_data.get('cards', []))
        if cdf.empty: cdf = pd.DataFrame(columns=["name", "limit", "closing_day", "due_day"])
        cdf['Excluir'] = False
        ed_cards = st.data_editor(cdf, num_rows="dynamic", use_container_width=True, hide_index=True, column_config={"Excluir": st.column_config.CheckboxColumn(default=False)})
        if st.button("Salvar Cartões"):
            new_c = ed_cards[ed_cards['Excluir']==False].drop(columns=['Excluir'])
            db_data['cards'] = new_c.to_dict(orient='records')
            save_user_data(db_data)
            st.success("Atualizado!")
            st.rerun()

    with tab2:
        adf = pd.DataFrame({"Nome": db_data.get('accounts', ["Carteira"])})
        adf['Excluir'] = False
        ed_acc = st.data_editor(adf, num_rows="dynamic", use_container_width=True, hide_index=True, column_config={"Excluir": st.column_config.CheckboxColumn(default=False)})
        if st.button("Salvar Contas"):
            valid = ed_acc[ed_acc['Excluir']==False]['Nome'].tolist()
            db_data['accounts'] = [x for x in valid if str(x).strip()]
            save_user_data(db_data)
            st.success("Atualizado!")
            st.rerun()

elif selected == "Metas":
    st.markdown("### 🎯 Metas")
    
    # --- NOVIDADE: EDIÇÃO DE METAS ---
    st.info("Você pode editar os valores das metas diretamente na tabela abaixo.")

    current_goals = db_data.get('goals', [])
    
    if not current_goals:
        # Se vazio, cria estrutura para o usuário começar
        gdf = pd.DataFrame(columns=["name", "target", "current", "color"])
    else:
        gdf = pd.DataFrame(current_goals)

    # Adiciona coluna de exclusão
    gdf['Excluir'] = False

    # Editor de Dados para Metas
    edited_goals = st.data_editor(
        gdf,
        column_config={
            "Excluir": st.column_config.CheckboxColumn(help="Remover meta", default=False),
            "name": st.column_config.TextColumn("Nome da Meta", required=True),
            "target": st.column_config.NumberColumn("Valor Alvo (R$)", min_value=0.0, format="R$ %.2f"),
            "current": st.column_config.NumberColumn("Valor Atual (R$)", min_value=0.0, format="R$ %.2f"),
            "color": st.column_config.TextColumn("Cor (Hex)", help="Ex: #FF0000"),
        },
        num_rows="dynamic",
        use_container_width=True,
        hide_index=True
    )

    if st.button("💾 Salvar Metas"):
        # Filtra excluídos e salva
        valid_goals = edited_goals[edited_goals['Excluir'] == False].drop(columns=['Excluir'])
        db_data['goals'] = valid_goals.to_dict(orient='records')
        save_user_data(db_data)
        st.success("Metas atualizadas com sucesso!")
        st.rerun()

    # Visualização de Progresso (Read-Only)
    if db_data.get('goals'):
        st.markdown("---")
        st.markdown("#### Progresso Visual")
        cols = st.columns(3)
        for i, g in enumerate(db_data['goals']):
            if not g.get('target'): g['target'] = 1 # Evita div por zero
            pct = (g.get('current',0) / g['target'] * 100)
            color = g.get('color', '#2D9CDB')
            
            with cols[i%3]:
                st.markdown(f"""
                <div class="white-card" style="padding: 15px;">
                    <b>{g.get('name', 'Meta')}</b>
                    <h3 style="color:{color}">R$ {g.get('current',0):,.0f} <small style="color:#ccc; font-size:12px">/ {g['target']:,.0f}</small></h3>
                    <div style="background:#eee;height:8px;border-radius:4px"><div style="width:{min(pct,100)}%;background:{color};height:100%;border-radius:4px"></div></div>
                    <div style="text-align:right;font-size:11px;color:#999;margin-top:5px">{pct:.1f}%</div>
                </div>
                """, unsafe_allow_html=True)

elif selected == "Nova Transação":
    st.markdown("### ➕ Nova Transação")
    with st.container():
        st.markdown('<div class="white-card">', unsafe_allow_html=True)
        with st.form("nt"):
            tipo = st.selectbox("Tipo", ["Despesa", "Receita"])
            val = st.number_input("Valor", min_value=0.0, step=10.0)
            c1, c2 = st.columns(2)
            dt = c1.date_input("Data", datetime.now())
            contas = db_data.get('accounts', []) + [c['name'] for c in db_data.get('cards', [])]
            acc = c2.selectbox("Conta", contas)
            cat = st.selectbox("Categoria", ["Alimentação", "Moradia", "Transporte", "Lazer", "Outros"])
            stt = st.radio("Status", ["Pago", "Pendente"], horizontal=True)
            desc = st.text_input("Descrição")
            if st.form_submit_button("Salvar"):
                nt = {"id": int(datetime.now().timestamp()), "date": dt.strftime("%Y-%m-%d"), "type": tipo, "amount": val, "account": acc, "category": cat, "status": stt, "desc": desc}
                db_data['transactions'].append(nt)
                save_user_data(db_data)
                st.success("Salvo!")
        st.markdown('</div>', unsafe_allow_html=True)
