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

# --- CSS PERSONALIZADO (DESIGN MODERNO) ---
def inject_custom_css():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700&display=swap');
        
        .stApp { background-color: #F4F7FC; font-family: 'Nunito', sans-serif; }
        
        /* Containers */
        .block-container { padding-top: 1.5rem; padding-bottom: 3rem; }
        .white-card {
            background-color: #FFFFFF; border-radius: 16px; padding: 24px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.03); margin-bottom: 20px; height: 100%;
            border: 1px solid #F0F2F5;
        }
        
        /* Stepper Vertical */
        .step-item { display: flex; align-items: flex-start; margin-bottom: 20px; position: relative; }
        .step-icon {
            width: 32px; height: 32px; border-radius: 50%; display: flex; 
            align-items: center; justify-content: center; color: white; 
            font-weight: bold; z-index: 2; margin-right: 15px; flex-shrink: 0; font-size: 14px;
        }
        .step-line {
            position: absolute; left: 15px; top: 32px; bottom: -25px; width: 2px;
            background-color: #E0E0E0; z-index: 1;
        }
        .step-last .step-line { display: none; }
        
        /* Cards Coloridos */
        .color-card {
            border-radius: 16px; padding: 20px; color: white;
            box-shadow: 0 8px 15px rgba(0,0,0,0.05); display: flex;
            align-items: center; justify-content: space-between; margin-bottom: 15px;
            transition: transform 0.2s;
        }
        .color-card:hover { transform: translateY(-2px); }
        .cc-icon {
            background-color: rgba(255,255,255,0.25); width: 48px; height: 48px;
            border-radius: 12px; display: flex; align-items: center; justify-content: center; font-size: 22px;
        }
        
        /* Cores */
        .bg-blue { background: linear-gradient(135deg, #2D9CDB 0%, #2F80ED 100%); }
        .bg-green { background: linear-gradient(135deg, #27AE60 0%, #219653 100%); }
        .bg-red { background: linear-gradient(135deg, #EB5757 0%, #C0392B 100%); }
        .bg-purple { background: linear-gradient(135deg, #9B51E0 0%, #8E44AD 100%); }
        
        /* Tipografia e Ajustes */
        .val-big { font-size: 24px; font-weight: 800; }
        .lbl-small { font-size: 13px; opacity: 0.9; font-weight: 500; }
        .js-plotly-plot .plotly .modebar { display: none !important; }
        div[data-testid="stDataFrame"] { border-radius: 10px; overflow: hidden; border: 1px solid #eee; }
        
        /* Botões Primários */
        div.stButton > button:first-child {
            background-color: #2D9CDB; color: white; border: none; border-radius: 8px; font-weight: 600;
        }
        div.stButton > button:hover { background-color: #1B85C4; }
        </style>
    """, unsafe_allow_html=True)

inject_custom_css()

# --- BANCO DE DADOS (JSON) ---
DB_FILE = 'finance_saas_v5.json'

def init_db():
    # Estrutura padrão se o arquivo não existir
    if not os.path.exists(DB_FILE):
        default_db = {
            "transactions": [],
            "cards": [
                {"name": "Nubank", "closing_day": 20, "due_day": 27, "limit": 5000}
            ],
            "accounts": ["Carteira", "Conta Corrente"],
            "goals": [
                {"name": "Reserva", "target": 5000, "current": 1000, "color": "#27AE60"}
            ]
        }
        with open(DB_FILE, 'w') as f: json.dump(default_db, f)

def load_db():
    init_db()
    try:
        with open(DB_FILE, 'r') as f: return json.load(f)
    except:
        # Recuperação de falha: recria se corrompido
        return {"transactions": [], "cards": [], "accounts": ["Carteira"], "goals": []}

def save_db(data):
    with open(DB_FILE, 'w') as f: json.dump(data, f, indent=4)

# --- ENGINE DE PROCESSAMENTO ---
def process_data(db, selected_date):
    txs = db.get('transactions', [])
    cards_list = db.get('cards', []) 
    # Cria dicionário para busca rápida de cartões
    cards = {c['name']: c for c in cards_list}
    
    # Colunas obrigatórias (Evita KeyError se vazio)
    required_cols = ['id', 'date', 'type', 'amount', 'account', 'category', 'status', 'desc', 'competencia', 'comp_mes', 'comp_ano']
    
    # Se não houver transações, retorna DataFrames vazios estruturados
    if not txs:
        empty_df = pd.DataFrame(columns=required_cols)
        return empty_df, empty_df, 0.0

    df = pd.DataFrame(txs)
    
    # Segurança extra: se faltar colunas críticas
    if 'date' not in df.columns or 'amount' not in df.columns:
         empty_df = pd.DataFrame(columns=required_cols)
         return empty_df, empty_df, 0.0

    # Conversões
    df['date'] = pd.to_datetime(df['date'])
    df['amount'] = df['amount'].astype(float)
    
    # Lógica de Cartão de Crédito (Competência)
    def get_competence_date(row):
        # Se for Despesa em uma conta que é Cartão de Crédito
        if row.get('account') in cards and row.get('type') == 'Despesa':
            card_info = cards[row['account']]
            try:
                closing_day = int(card_info['closing_day'])
                # Se compra feita após/no fechamento, joga pro mês seguinte
                if row['date'].day >= closing_day:
                    return row['date'] + relativedelta(months=1)
            except:
                pass # Em caso de erro nos dados do cartão, mantém data original
        return row['date']

    df['competencia'] = df.apply(get_competence_date, axis=1)
    df['comp_mes'] = df['competencia'].dt.month
    df['comp_ano'] = df['competencia'].dt.year

    # 1. Dados do Mês Selecionado (Baseado na Competência)
    df_mes = df[(df['comp_mes'] == selected_date.month) & (df['comp_ano'] == selected_date.year)]
    
    # 2. Saldo Inicial (Acumulado até o mês anterior)
    mask_anterior = (df['competencia'] < datetime(selected_date.year, selected_date.month, 1))
    df_anterior = df[mask_anterior]
    
    # Cálculo simples de caixa realizado anteriormente
    rec_ant = df_anterior[(df_anterior['type'] == 'Receita') & (df_anterior['status'] == 'Pago')]['amount'].sum()
    desp_ant = df_anterior[(df_anterior['type'] == 'Despesa') & (df_anterior['status'] == 'Pago')]['amount'].sum()
    saldo_inicial = rec_ant - desp_ant

    return df, df_mes, saldo_inicial

# --- SIDEBAR (NAVEGAÇÃO E FILTROS) ---
db_data = load_db()

with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/10543/10543268.png", width=60)
    st.markdown("### FinSaaS")
    
    # Filtro Global de Data
    col_mes, col_ano = st.columns(2)
    with col_mes:
        mes_nomes = {1: "Jan", 2: "Fev", 3: "Mar", 4: "Abr", 5: "Mai", 6: "Jun", 
                     7: "Jul", 8: "Ago", 9: "Set", 10: "Out", 11: "Nov", 12: "Dez"}
        sel_mes = st.selectbox("Mês", list(mes_nomes.keys()), index=datetime.now().month-1, format_func=lambda x: mes_nomes[x])
    with col_ano:
        sel_ano = st.number_input("Ano", value=datetime.now().year, step=1)
    
    ref_date = datetime(sel_ano, sel_mes, 1)
    st.markdown("---")
    
    # Menu Principal
    selected = option_menu(
        menu_title=None,
        options=["Dashboard", "Extrato", "Cadastros", "Metas", "Nova Transação"],
        icons=["grid-1x2", "table", "wallet2", "trophy", "plus-circle-fill"],
        default_index=0,
        styles={
            "container": {"background-color": "transparent"},
            "nav-link-selected": {"background-color": "#2D9CDB", "font-weight": "600"},
        }
    )
    
    st.info(f"📅 Visualizando: **{mes_nomes[sel_mes]}/{sel_ano}**")

# Executa processamento global
df_full, df_view, saldo_inicial = process_data(db_data, ref_date)

# ==================================================================================================
# PÁGINA 1: DASHBOARD
# ==================================================================================================
if selected == "Dashboard":
    # Garante valores float mesmo se vazio
    if not df_view.empty:
        receitas_mes = df_view[df_view['type'] == 'Receita']['amount'].sum()
        despesas_mes = df_view[df_view['type'] == 'Despesa']['amount'].sum()
        
        # Para saldo atual (apenas pagos)
        rec_pago = df_view[(df_view['type'] == 'Receita') & (df_view['status'] == 'Pago')]['amount'].sum()
        desp_pago = df_view[(df_view['type'] == 'Despesa') & (df_view['status'] == 'Pago')]['amount'].sum()
        
        pendente_val = df_view[(df_view['type'] == 'Despesa') & (df_view['status'] == 'Pendente')]['amount'].sum()
    else:
        receitas_mes = 0.0; despesas_mes = 0.0; rec_pago = 0.0; desp_pago = 0.0; pendente_val = 0.0
    
    saldo_previsto = saldo_inicial + receitas_mes - despesas_mes
    saldo_atual = saldo_inicial + rec_pago - desp_pago

    # Layout Principal
    col_main, col_side = st.columns([3, 1])

    with col_main:
        # Cards Topo
        c1, c2, c3 = st.columns(3)
        with c1: st.markdown(f'<div class="color-card bg-green"><div><div class="lbl-small">Receitas</div><div class="val-big">R$ {receitas_mes:,.2f}</div></div><div class="cc-icon">↑</div></div>', unsafe_allow_html=True)
        with c2: st.markdown(f'<div class="color-card bg-red"><div><div class="lbl-small">Despesas</div><div class="val-big">R$ {despesas_mes:,.2f}</div></div><div class="cc-icon">↓</div></div>', unsafe_allow_html=True)
        with c3: st.markdown(f'<div class="color-card bg-blue"><div><div class="lbl-small">Balanço</div><div class="val-big">R$ {(receitas_mes - despesas_mes):,.2f}</div></div><div class="cc-icon">⚖️</div></div>', unsafe_allow_html=True)

        # Gráficos
        g1, g2 = st.columns([2, 1])
        with g1:
            st.markdown('<div class="white-card"><h5>Fluxo Diário</h5>', unsafe_allow_html=True)
            if not df_view.empty:
                daily = df_view.groupby('date')['amount'].sum().reset_index()
                fig = px.bar(daily, x='date', y='amount', color_discrete_sequence=['#2D9CDB'])
                fig.update_layout(height=220, margin=dict(l=0,r=0,t=0,b=0), paper_bgcolor='white', plot_bgcolor='white')
                st.plotly_chart(fig, use_container_width=True)
            else: st.info("Sem movimentações.")
            st.markdown('</div>', unsafe_allow_html=True)
            
        with g2:
            st.markdown('<div class="white-card"><h5>Por Categoria</h5>', unsafe_allow_html=True)
            if not df_view.empty:
                df_desp = df_view[df_view['type'] == 'Despesa']
                if not df_desp.empty:
                    fig = px.pie(df_desp, values='amount', names='category', hole=0.6, color_discrete_sequence=px.colors.qualitative.Pastel)
                    fig.update_layout(height=220, showlegend=False, margin=dict(l=0,r=0,t=0,b=0))
                    st.plotly_chart(fig, use_container_width=True)
                else: st.write("Sem despesas.")
            else: st.write("Sem dados.")
            st.markdown('</div>', unsafe_allow_html=True)

    with col_side:
        # Stepper Lateral
        st.markdown(f"""
        <div class="white-card">
            <h4>Evolução</h4>
            <div class="step-item"><div class="step-line"></div><div class="step-icon bg-blue">1</div><div><div style="font-weight:700">R$ {saldo_inicial:,.2f}</div><div style="font-size:12px;color:#888">Inicial</div></div></div>
            <div class="step-item"><div class="step-line"></div><div class="step-icon bg-green">2</div><div><div style="font-weight:700">R$ {saldo_atual:,.2f}</div><div style="font-size:12px;color:#888">Atual</div></div></div>
            <div class="step-item step-last"><div class="step-icon bg-purple">3</div><div><div style="font-weight:700">R$ {saldo_previsto:,.2f}</div><div style="font-size:12px;color:#888">Previsto</div></div></div>
            <hr>
            <div style="background:#FEF3C7;padding:10px;border-radius:8px;border:1px solid #FCD34D;">
                <div style="font-weight:700;color:#D97706;font-size:12px;">⚠️ A Pagar</div>
                <div style="color:#B45309;">R$ {pendente_val:,.2f}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

# ==================================================================================================
# PÁGINA 2: EXTRATO (CRUD)
# ==================================================================================================
elif selected == "Extrato":
    st.markdown("### 📝 Extrato Completo")
    if df_full.empty:
        st.warning("Nenhum dado lançado.")
    else:
        # Prepara DF para edição
        df_edit = df_full.sort_values(by='date', ascending=False).copy()
        df_edit['Excluir'] = False
        
        # Pega lista de contas atualizada para o dropdown
        all_accounts = db_data.get('accounts', []) + [c['name'] for c in db_data.get('cards', [])]
        
        edited_df = st.data_editor(
            df_edit,
            column_config={
                "Excluir": st.column_config.CheckboxColumn(help="Marque para deletar", default=False),
                "id": None, "competencia": None, "comp_mes": None, "comp_ano": None,
                "date": st.column_config.DateColumn("Data", format="DD/MM/YYYY"),
                "amount": st.column_config.NumberColumn("Valor", format="R$ %.2f"),
                "type": st.column_config.SelectboxColumn("Tipo", options=["Receita", "Despesa"], required=True),
                "account": st.column_config.SelectboxColumn("Conta", options=all_accounts),
                "category": st.column_config.SelectboxColumn("Categoria", options=["Alimentação", "Moradia", "Lazer", "Transporte", "Saúde", "Salário", "Investimentos", "Outros"]),
                "status": st.column_config.SelectboxColumn("Status", options=["Pago", "Pendente"]),
                "desc": st.column_config.TextColumn("Descrição"),
            },
            hide_index=True, use_container_width=True, num_rows="dynamic"
        )
        
        if st.button("💾 Salvar Alterações", type="primary"):
            # 1. Filtra removidos
            final_df = edited_df[edited_df['Excluir'] == False].drop(columns=['Excluir', 'competencia', 'comp_mes', 'comp_ano'], errors='ignore')
            
            # 2. Converte datas para string
            def date_to_str(val):
                if isinstance(val, (datetime, date)): return val.strftime('%Y-%m-%d')
                return val
            final_df['date'] = final_df['date'].apply(date_to_str)
            
            # 3. Salva
            db_data['transactions'] = final_df.to_dict(orient='records')
            save_db(db_data)
            st.success("Extrato atualizado!")
            st.rerun()

# ==================================================================================================
# PÁGINA 3: CADASTROS (CARTÕES E CONTAS)
# ==================================================================================================
elif selected == "Cadastros":
    st.markdown("### ⚙️ Gerenciar Carteiras")
    
    tab1, tab2 = st.tabs(["💳 Cartões de Crédito", "🏦 Contas Bancárias"])
    
    # --- TAB 1: CARTÕES ---
    with tab1:
        st.info("Defina aqui seus cartões e dias de fechamento para o cálculo automático de fatura.")
        
        cards_df = pd.DataFrame(db_data.get('cards', []))
        if cards_df.empty:
             cards_df = pd.DataFrame(columns=["name", "limit", "closing_day", "due_day"])
        
        cards_df["Excluir"] = False
        
        edited_cards = st.data_editor(
            cards_df,
            column_config={
                "Excluir": st.column_config.CheckboxColumn(default=False),
                "name": st.column_config.TextColumn("Nome", required=True),
                "limit": st.column_config.NumberColumn("Limite", format="R$ %.2f"),
                "closing_day": st.column_config.NumberColumn("Fechamento (Dia)", min_value=1, max_value=31),
                "due_day": st.column_config.NumberColumn("Vencimento (Dia)", min_value=1, max_value=31),
            },
            num_rows="dynamic", use_container_width=True, hide_index=True
        )
        
        if st.button("💾 Salvar Cartões"):
            new_cards = edited_cards[edited_cards["Excluir"] == False].drop(columns=["Excluir"])
            db_data['cards'] = new_cards.to_dict(orient="records")
            save_db(db_data)
            st.success("Cartões salvos!")
            st.rerun()

        # Preview Faturas
        if db_data.get('cards'):
            st.markdown("---")
            st.caption(f"Faturas em: {ref_date.strftime('%B/%Y')}")
            cols = st.columns(3)
            for i, card in enumerate(db_data['cards']):
                # Calcula gasto filtrado
                if not df_view.empty:
                    gasto = df_view[(df_view['account'] == card['name']) & (df_view['type'] == 'Despesa')]['amount'].sum()
                else: gasto = 0.0
                
                pct = (gasto / card['limit'] * 100) if card['limit'] > 0 else 0
                
                with cols[i % 3]:
                    st.markdown(f"""
                    <div class="white-card" style="padding:15px;">
                        <div style="display:flex;justify-content:space-between"><b>{card['name']}</b></div>
                        <h4 style="color:#EB5757">R$ {gasto:,.2f}</h4>
                        <div style="background:#eee;height:6px;border-radius:3px;"><div style="width:{min(pct,100)}%;background:#2D9CDB;height:100%;border-radius:3px"></div></div>
                        <small style="color:#999">Limite: R$ {card['limit']:,.2f}</small>
                    </div>
                    """, unsafe_allow_html=True)

    # --- TAB 2: CONTAS ---
    with tab2:
        st.info("Cadastre contas de débito, dinheiro ou poupança.")
        
        acc_list = db_data.get('accounts', ["Carteira"])
        acc_df = pd.DataFrame({"Nome da Conta": acc_list})
        acc_df["Excluir"] = False
        
        edited_accs = st.data_editor(
            acc_df,
            column_config={
                "Excluir": st.column_config.CheckboxColumn(default=False),
                "Nome da Conta": st.column_config.TextColumn(required=True)
            },
            num_rows="dynamic", use_container_width=True, hide_index=True
        )
        
        if st.button("💾 Salvar Contas"):
            valid_accs = edited_accs[edited_accs["Excluir"] == False]["Nome da Conta"].tolist()
            # Remove vazios e duplicados
            valid_accs = list(set([a for a in valid_accs if str(a).strip() != ""]))
            db_data['accounts'] = valid_accs
            save_db(db_data)
            st.success("Contas salvas!")
            st.rerun()

# ==================================================================================================
# PÁGINA 4: METAS
# ==================================================================================================
elif selected == "Metas":
    st.markdown("### 🎯 Objetivos")
    with st.expander("➕ Criar Nova Meta"):
        with st.form("new_goal"):
            n = st.text_input("Nome")
            t = st.number_input("Valor Alvo", min_value=0.0)
            c = st.number_input("Valor Atual", min_value=0.0)
            cor = st.color_picker("Cor", "#27AE60")
            if st.form_submit_button("Salvar"):
                db_data['goals'].append({"name": n, "target": t, "current": c, "color": cor})
                save_db(db_data)
                st.rerun()
    
    cols = st.columns(3)
    for i, g in enumerate(db_data.get('goals', [])):
        pct = (g['current'] / g['target'] * 100) if g['target'] > 0 else 0
        with cols[i%3]:
            st.markdown(f"""
            <div class="white-card">
                <div style="display:flex;justify-content:space-between"><b>{g['name']}</b><span>🏆</span></div>
                <h3 style="color:{g['color']}">R$ {g['current']:,.0f} <small style="font-size:12px;color:#ccc">/ {g['target']:,.0f}</small></h3>
                <div style="background:#eee;height:8px;border-radius:4px"><div style="width:{min(pct,100)}%;background:{g['color']};height:100%;border-radius:4px"></div></div>
                <div style="text-align:right;font-size:11px;color:#999;margin-top:5px">{pct:.1f}%</div>
            </div>
            """, unsafe_allow_html=True)

# ==================================================================================================
# PÁGINA 5: NOVA TRANSAÇÃO
# ==================================================================================================
elif selected == "Nova Transação":
    st.markdown("### ➕ Lançamento")
    
    col_center = st.columns([1, 2, 1])
    with col_center[1]:
        st.markdown('<div class="white-card">', unsafe_allow_html=True)
        
        with st.form("trans_form", clear_on_submit=True):
            tipo = st.selectbox("Tipo", ["Despesa", "Receita"])
            val = st.number_input("Valor (R$)", min_value=0.0, step=10.0)
            
            c1, c2 = st.columns(2)
            dt = c1.date_input("Data", datetime.now())
            
            # Combina Contas e Cartões no Dropdown
            opcoes = db_data.get('accounts', ["Carteira"]) + [c['name'] for c in db_data.get('cards', [])]
            conta = c2.selectbox("Conta / Cartão", opcoes)
            
            cat = st.selectbox("Categoria", ["Alimentação", "Moradia", "Lazer", "Transporte", "Saúde", "Educação", "Salário", "Investimento", "Outros"])
            stt = st.radio("Status", ["Pago", "Pendente"], horizontal=True)
            desc = st.text_input("Descrição")
            
            if st.form_submit_button("Confirmar", type="primary"):
                nt = {
                    "id": int(datetime.now().timestamp()),
                    "date": dt.strftime("%Y-%m-%d"),
                    "type": tipo, "amount": val, "account": conta,
                    "category": cat, "status": stt, "desc": desc
                }
                db_data['transactions'].append(nt)
                save_db(db_data)
                st.balloons()
                st.success("Lançamento salvo!")
        st.markdown('</div>', unsafe_allow_html=True)
