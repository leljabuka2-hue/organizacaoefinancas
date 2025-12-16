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

# --- CSS ESTILO MOBILLS / NUBANK ---
def inject_custom_css():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700&display=swap');
        
        .stApp { background-color: #F4F7FC; font-family: 'Nunito', sans-serif; }
        
        /* Containers e Cards */
        .block-container { padding-top: 1.5rem; padding-bottom: 3rem; }
        .white-card {
            background-color: #FFFFFF; border-radius: 16px; padding: 24px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.03); margin-bottom: 20px; height: 100%;
            border: 1px solid #F0F2F5;
        }
        
        /* Stepper (Linha do Tempo de Saldo) */
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
        
        /* Widgets Coloridos */
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
        
        /* Cores Utilitárias */
        .bg-blue { background: linear-gradient(135deg, #2D9CDB 0%, #2F80ED 100%); }
        .bg-green { background: linear-gradient(135deg, #27AE60 0%, #219653 100%); }
        .bg-red { background: linear-gradient(135deg, #EB5757 0%, #C0392B 100%); }
        .bg-purple { background: linear-gradient(135deg, #9B51E0 0%, #8E44AD 100%); }
        
        /* Tipografia */
        .val-big { font-size: 24px; font-weight: 800; }
        .lbl-small { font-size: 13px; opacity: 0.9; font-weight: 500; }
        h1, h2, h3, h4 { color: #333; font-weight: 700; }
        
        /* Ajustes Plotly e Tabelas */
        .js-plotly-plot .plotly .modebar { display: none !important; }
        div[data-testid="stDataFrame"] { border-radius: 10px; overflow: hidden; border: 1px solid #eee; }
        
        /* Botão Salvar */
        div.stButton > button:first-child {
            background-color: #2D9CDB;
            color: white;
            border: none;
            border-radius: 8px;
        }
        </style>
    """, unsafe_allow_html=True)

inject_custom_css()

# --- GERENCIAMENTO DE DADOS (JSON) ---
DB_FILE = 'finance_full_v3.json'

def init_db():
    # Cria o arquivo se não existir
    if not os.path.exists(DB_FILE):
        default_db = {
            "transactions": [],
            "cards": [
                {"name": "Nubank", "closing_day": 20, "due_day": 27, "limit": 5000},
                {"name": "Inter", "closing_day": 10, "due_day": 17, "limit": 3000}
            ],
            "goals": [
                {"name": "Reserva de Emergência", "target": 10000, "current": 2500, "color": "#27AE60"}
            ]
        }
        with open(DB_FILE, 'w') as f: json.dump(default_db, f)

def load_db():
    init_db()
    try:
        with open(DB_FILE, 'r') as f: return json.load(f)
    except:
        # Se der erro de leitura (arquivo corrompido), recria
        os.remove(DB_FILE)
        init_db()
        with open(DB_FILE, 'r') as f: return json.load(f)

def save_db(data):
    with open(DB_FILE, 'w') as f: json.dump(data, f, indent=4)

# --- ENGINE LÓGICA (O CÉREBRO) ---
def process_data(db, selected_date):
    """
    Processa todas as transações e aplica a lógica de cartão de crédito.
    """
    txs = db.get('transactions', [])
    cards_list = db.get('cards', []) 
    cards = {c['name']: c for c in cards_list}
    
    # CORREÇÃO CRÍTICA: Retorna 3 valores vazios se não houver dados
    if not txs:
        return pd.DataFrame(), pd.DataFrame(), 0.0

    df = pd.DataFrame(txs)
    
    # Verificação de colunas obrigatórias
    if 'date' not in df.columns or 'amount' not in df.columns:
         return pd.DataFrame(), pd.DataFrame(), 0.0

    # Conversão de tipos
    df['date'] = pd.to_datetime(df['date'])
    df['amount'] = df['amount'].astype(float)
    
    # Lógica de Competência (Virada de Fatura)
    def get_competence_date(row):
        # Se for despesa de cartão de crédito
        if row.get('account') in cards and row.get('type') == 'Despesa':
            card_info = cards[row['account']]
            closing_day = int(card_info['closing_day'])
            
            # Se a compra foi feita DEPOIS ou NO dia do fechamento, cai no mês seguinte
            if row['date'].day >= closing_day:
                return row['date'] + relativedelta(months=1)
        
        return row['date']

    df['competencia'] = df.apply(get_competence_date, axis=1)
    df['comp_mes'] = df['competencia'].dt.month
    df['comp_ano'] = df['competencia'].dt.year

    # 1. Filtra dados do Mês Selecionado (Visão de Caixa/Competência)
    df_mes = df[(df['comp_mes'] == selected_date.month) & (df['comp_ano'] == selected_date.year)]
    
    # 2. Calcula Saldo Inicial (Tudo que aconteceu antes deste mês)
    mask_anterior = (df['competencia'] < datetime(selected_date.year, selected_date.month, 1))
    df_anterior = df[mask_anterior]
    
    # Saldo acumulado (Receitas Pagas - Despesas Pagas)
    rec_ant = df_anterior[(df_anterior['type'] == 'Receita') & (df_anterior['status'] == 'Pago')]['amount'].sum()
    desp_ant = df_anterior[(df_anterior['type'] == 'Despesa') & (df_anterior['status'] == 'Pago')]['amount'].sum()
    saldo_inicial = rec_ant - desp_ant

    return df, df_mes, saldo_inicial

# --- SIDEBAR GLOBAL ---
db_data = load_db()

with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/10543/10543268.png", width=60)
    st.markdown("### FinSaaS")
    
    # MÁQUINA DO TEMPO (FILTRO)
    col_mes, col_ano = st.columns(2)
    with col_mes:
        mes_nomes = {1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril", 5: "Maio", 6: "Junho", 
                     7: "Julho", 8: "Agosto", 9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"}
        sel_mes = st.selectbox("Mês", list(mes_nomes.keys()), index=datetime.now().month-1, format_func=lambda x: mes_nomes[x])
    with col_ano:
        sel_ano = st.number_input("Ano", value=datetime.now().year, step=1)
    
    # Data de Referência Global
    ref_date = datetime(sel_ano, sel_mes, 1)

    st.markdown("---")
    
    # MENU DE NAVEGAÇÃO
    selected = option_menu(
        menu_title=None,
        options=["Dashboard", "Extrato / Edição", "Cartões", "Metas", "Nova Transação"],
        icons=["columns-gap", "list-check", "credit-card", "trophy", "plus-circle-fill"],
        default_index=0,
        styles={
            "container": {"background-color": "transparent"},
            "nav-link": {"font-size": "14px", "text-align": "left", "margin":"5px", "--hover-color": "#eee"},
            "nav-link-selected": {"background-color": "#2D9CDB", "font-weight": "600"},
        }
    )
    
    st.markdown("---")
    st.info(f"📅 Visualizando: **{mes_nomes[sel_mes]}/{sel_ano}**")

# PROCESSA DADOS GLOBAIS
df_full, df_view, saldo_inicial = process_data(db_data, ref_date)

# ==================================================================================================
# PÁGINA 1: DASHBOARD (VISÃO GERENCIAL)
# ==================================================================================================
if selected == "Dashboard":
    # CÁLCULOS DO MÊS
    receitas_mes = df_view[df_view['type'] == 'Receita']['amount'].sum()
    despesas_mes = df_view[df_view['type'] == 'Despesa']['amount'].sum()
    
    # Saldo Previsto (Considera tudo, pago e pendente do mês)
    saldo_previsto = saldo_inicial + receitas_mes - despesas_mes
    
    # Saldo Atual (Considera apenas PAGOS do mês + Saldo Inicial)
    rec_pago = df_view[(df_view['type'] == 'Receita') & (df_view['status'] == 'Pago')]['amount'].sum()
    desp_pago = df_view[(df_view['type'] == 'Despesa') & (df_view['status'] == 'Pago')]['amount'].sum()
    saldo_atual = saldo_inicial + rec_pago - desp_pago

    col_main, col_side = st.columns([3, 1])

    with col_main:
        # 1. CARDS DE DESTAQUE
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(f"""
            <div class="color-card bg-green">
                <div>
                    <div class="lbl-small">Receitas</div>
                    <div class="val-big">R$ {receitas_mes:,.2f}</div>
                </div>
                <div class="cc-icon">↑</div>
            </div>
            """, unsafe_allow_html=True)
        with c2:
            st.markdown(f"""
            <div class="color-card bg-red">
                <div>
                    <div class="lbl-small">Despesas</div>
                    <div class="val-big">R$ {despesas_mes:,.2f}</div>
                </div>
                <div class="cc-icon">↓</div>
            </div>
            """, unsafe_allow_html=True)
        with c3:
            st.markdown(f"""
            <div class="color-card bg-blue">
                <div>
                    <div class="lbl-small">Balanço do Mês</div>
                    <div class="val-big">R$ {(receitas_mes - despesas_mes):,.2f}</div>
                </div>
                <div class="cc-icon">⚖️</div>
            </div>
            """, unsafe_allow_html=True)

        # 2. GRÁFICO DE FLUXO E CATEGORIAS
        g1, g2 = st.columns([2, 1])
        with g1:
            st.markdown('<div class="white-card">', unsafe_allow_html=True)
            st.markdown("##### Fluxo de Caixa (Diário)")
            if not df_view.empty:
                daily = df_view.groupby('date')['amount'].sum().reset_index()
                fig = px.bar(daily, x='date', y='amount', color_discrete_sequence=['#2D9CDB'])
                fig.update_layout(height=250, margin=dict(l=0,r=0,t=0,b=0), paper_bgcolor='white', plot_bgcolor='white')
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Sem dados neste período.")
            st.markdown('</div>', unsafe_allow_html=True)
            
        with g2:
            st.markdown('<div class="white-card">', unsafe_allow_html=True)
            st.markdown("##### Categorias")
            if not df_view.empty:
                df_desp = df_view[df_view['type'] == 'Despesa']
                if not df_desp.empty:
                    fig_pie = px.pie(df_desp, values='amount', names='category', hole=0.6, color_discrete_sequence=px.colors.qualitative.Pastel)
                    fig_pie.update_layout(height=250, showlegend=False, margin=dict(l=0,r=0,t=0,b=0))
                    st.plotly_chart(fig_pie, use_container_width=True)
                else:
                    st.write("Sem despesas.")
            else:
                st.write("Sem dados.")
            st.markdown('</div>', unsafe_allow_html=True)

    with col_side:
        # 3. STEPPER DE SALDO (VERTICAL)
        st.markdown(f"""
        <div class="white-card">
            <h4 style="margin-bottom: 20px;">Evolução Patrimonial</h4>
            
            <div class="step-item">
                <div class="step-line"></div>
                <div class="step-icon bg-blue">1</div>
                <div>
                    <div style="font-size: 16px; font-weight: 700; color: #333;">R$ {saldo_inicial:,.2f}</div>
                    <div style="font-size: 12px; color: #888;">Saldo Inicial</div>
                </div>
            </div>
            
            <div class="step-item">
                <div class="step-line"></div>
                <div class="step-icon bg-green">2</div>
                <div>
                    <div style="font-size: 16px; font-weight: 700; color: #333;">R$ {saldo_atual:,.2f}</div>
                    <div style="font-size: 12px; color: #888;">Saldo Hoje</div>
                </div>
            </div>
            
            <div class="step-item step-last">
                <div class="step-icon bg-purple">3</div>
                <div>
                    <div style="font-size: 16px; font-weight: 700; color: #333;">R$ {saldo_previsto:,.2f}</div>
                    <div style="font-size: 12px; color: #888;">Previsto (Fim do Mês)</div>
                </div>
            </div>
            
            <hr style="margin: 20px 0; border: 0; border-top: 1px solid #eee;">
            
            <div style="background-color: #FEF3C7; padding: 15px; border-radius: 12px; border: 1px solid #FCD34D;">
                <div style="font-weight: 700; color: #D97706; font-size: 13px;">⚠️ Contas a Pagar</div>
                <div style="font-size: 12px; color: #B45309;">
                    R$ {df_view[(df_view['type'] == 'Despesa') & (df_view['status'] == 'Pendente')]['amount'].sum():,.2f} pendentes.
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

# ==================================================================================================
# PÁGINA 2: EXTRATO COMPLETO (CRUD)
# ==================================================================================================
elif selected == "Extrato / Edição":
    st.markdown("### 📝 Extrato Detalhado")
    
    if df_full.empty:
        st.warning("Nenhum dado encontrado.")
    else:
        # Prepara dataframe para o Data Editor
        df_edit = df_full.sort_values(by='date', ascending=False).copy()
        df_edit['Excluir'] = False # Checkbox para deletar
        
        # Configuração do Editor
        edited_df = st.data_editor(
            df_edit,
            column_config={
                "Excluir": st.column_config.CheckboxColumn(help="Marque para deletar permanentemente", default=False),
                "id": None, "competencia": None, "comp_mes": None, "comp_ano": None,
                "date": st.column_config.DateColumn("Data", format="DD/MM/YYYY"),
                "amount": st.column_config.NumberColumn("Valor", format="R$ %.2f"),
                "type": st.column_config.SelectboxColumn("Tipo", options=["Receita", "Despesa"], required=True),
                "category": st.column_config.SelectboxColumn("Categoria", options=["Alimentação", "Moradia", "Lazer", "Transporte", "Saúde", "Salário", "Investimentos", "Outros"]),
                "account": st.column_config.SelectboxColumn("Conta", options=["Carteira"] + [c['name'] for c in db_data['cards']]),
                "status": st.column_config.SelectboxColumn("Status", options=["Pago", "Pendente"]),
                "desc": st.column_config.TextColumn("Descrição"),
            },
            hide_index=True,
            use_container_width=True,
            num_rows="dynamic",
            height=500
        )
        
        if st.button("💾 Salvar Alterações", type="primary"):
            # Filtra removidos
            final_df = edited_df[edited_df['Excluir'] == False].drop(columns=['Excluir', 'competencia', 'comp_mes', 'comp_ano'], errors='ignore')
            
            # Converte datas para string de forma segura para o JSON
            def date_to_str(val):
                if isinstance(val, (datetime, date)):
                    return val.strftime('%Y-%m-%d')
                return val

            final_df['date'] = final_df['date'].apply(date_to_str)
            
            # Salva
            db_data['transactions'] = final_df.to_dict(orient='records')
            save_db(db_data)
            st.success("Dados atualizados!")
            st.rerun()

# ==================================================================================================
# PÁGINA 3: CARTÕES DE CRÉDITO
# ==================================================================================================
elif selected == "Cartões":
    st.markdown("### 💳 Meus Cartões")
    
    col_c1, col_c2 = st.columns([1, 2])
    
    with col_c1:
        st.markdown('<div class="white-card">', unsafe_allow_html=True)
        st.markdown("##### Cadastrar Novo Cartão")
        with st.form("add_card"):
            c_nome = st.text_input("Nome do Cartão (Ex: Nubank)")
            c_limite = st.number_input("Limite (R$)", min_value=0.0)
            c1, c2 = st.columns(2)
            c_fech = c1.number_input("Dia Fechamento", 1, 31, 20)
            c_venc = c2.number_input("Dia Vencimento", 1, 31, 27)
            
            if st.form_submit_button("Adicionar Cartão"):
                new_card = {"name": c_nome, "limit": c_limite, "closing_day": c_fech, "due_day": c_venc}
                db_data['cards'].append(new_card)
                save_db(db_data)
                st.success("Cartão criado!")
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
        
    with col_c2:
        if not db_data['cards']:
            st.info("Nenhum cartão cadastrado.")
        else:
            for card in db_data['cards']:
                # Calcula fatura do MÊS SELECIONADO na sidebar
                gasto_fatura = df_view[(df_view['account'] == card['name']) & (df_view['type'] == 'Despesa')]['amount'].sum()
                pct_limit = (gasto_fatura / card['limit'] * 100) if card['limit'] > 0 else 0
                
                st.markdown(f"""
                <div class="white-card" style="margin-bottom: 15px; padding: 15px;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div style="font-weight: bold; font-size: 18px;">{card['name']}</div>
                        <div style="font-size: 12px; background: #eee; padding: 4px 8px; border-radius: 4px;">Vence dia {card['due_day']}</div>
                    </div>
                    <div style="margin-top: 10px; display: flex; justify-content: space-between;">
                        <span style="color: #666;">Fatura Atual ({ref_date.strftime('%B')})</span>
                        <span style="font-weight: bold; color: #EB5757;">R$ {gasto_fatura:,.2f}</span>
                    </div>
                    <div style="width: 100%; background-color: #eee; height: 8px; border-radius: 4px; margin-top: 8px;">
                        <div style="width: {min(pct_limit, 100)}%; background-color: #2D9CDB; height: 100%; border-radius: 4px;"></div>
                    </div>
                    <div style="font-size: 11px; color: #999; margin-top: 4px;">Disponível: R$ {(card['limit'] - gasto_fatura):,.2f}</div>
                </div>
                """, unsafe_allow_html=True)

# ==================================================================================================
# PÁGINA 4: METAS
# ==================================================================================================
elif selected == "Metas":
    st.markdown("### 🎯 Objetivos Financeiros")
    
    with st.expander("➕ Nova Meta"):
        with st.form("new_goal"):
            g_nome = st.text_input("Nome da Meta (Ex: Viagem Disney)")
            g_target = st.number_input("Valor Alvo", min_value=0.0)
            g_current = st.number_input("Já guardado", min_value=0.0)
            g_color = st.color_picker("Cor", "#27AE60")
            if st.form_submit_button("Criar Meta"):
                db_data['goals'].append({"name": g_nome, "target": g_target, "current": g_current, "color": g_color})
                save_db(db_data)
                st.rerun()

    cols = st.columns(3)
    if not db_data['goals']:
        st.info("Nenhuma meta criada.")
    
    for i, goal in enumerate(db_data['goals']):
        pct = (goal['current'] / goal['target']) * 100 if goal['target'] > 0 else 0
        with cols[i % 3]:
            st.markdown(f"""
            <div class="white-card">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <h4 style="margin:0;">{goal['name']}</h4>
                    <span style="font-size:20px;">🏆</span>
                </div>
                <h2 style="color: {goal['color']}; margin: 10px 0;">R$ {goal['current']:,.0f} <span style="font-size:14px; color:#999;">/ {goal['target']:,.0f}</span></h2>
                
                <div style="width: 100%; background-color: #eee; height: 10px; border-radius: 5px;">
                    <div style="width: {min(pct, 100)}%; background-color: {goal['color']}; height: 100%; border-radius: 5px; transition: width 0.5s;"></div>
                </div>
                <div style="text-align: right; font-size: 12px; margin-top: 5px; color: #666;">{pct:.1f}% concluído</div>
            </div>
            """, unsafe_allow_html=True)

# ==================================================================================================
# PÁGINA 5: NOVA TRANSAÇÃO
# ==================================================================================================
elif selected == "Nova Transação":
    st.markdown("### ➕ Adicionar Movimentação")
    
    col_center = st.columns([1, 2, 1])
    with col_center[1]:
        st.markdown('<div class="white-card">', unsafe_allow_html=True)
        
        with st.form("main_form", clear_on_submit=True):
            tipo = st.selectbox("Tipo", ["Despesa", "Receita"])
            valor = st.number_input("Valor R$", min_value=0.0, step=10.0, format="%.2f")
            
            c1, c2 = st.columns(2)
            data_t = c1.date_input("Data", datetime.now())
            
            # Carrega opções de contas atualizadas
            opcoes_contas = ["Carteira"] + [c['name'] for c in db_data['cards']]
            conta = c2.selectbox("Conta / Cartão", opcoes_contas)
            
            cat = st.selectbox("Categoria", ["Alimentação", "Moradia", "Transporte", "Lazer", "Saúde", "Educação", "Salário", "Investimento", "Outros"])
            desc = st.text_input("Descrição (Opcional)")
            status = st.radio("Situação", ["Pago", "Pendente"], horizontal=True)
            
            if st.form_submit_button("Confirmar Lançamento"):
                new_trans = {
                    "id": int(datetime.now().timestamp()),
                    "date": data_t.strftime("%Y-%m-%d"),
                    "type": tipo,
                    "amount": valor,
                    "account": conta,
                    "category": cat,
                    "status": status,
                    "desc": desc
                }
                db_data['transactions'].append(new_trans)
                save_db(db_data)
                
                st.markdown(f"""
                <div style="padding: 10px; background-color: #D1FAE5; color: #065F46; border-radius: 8px; text-align: center; margin-top: 10px;">
                    ✅ Lançamento de <b>R$ {valor:.2f}</b> salvo com sucesso!
                </div>
                """, unsafe_allow_html=True)
                
        st.markdown('</div>', unsafe_allow_html=True)
