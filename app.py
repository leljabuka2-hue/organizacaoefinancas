import streamlit as st
import json
import pandas as pd
import os
from datetime import datetime, timedelta
import time
import plotly.express as px

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="FinSaaS AI", page_icon="💳", layout="centered")

# --- CSS ESTILO IPHONE / IOS (ATUALIZADO) ---
def inject_ios_css():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=San+Francisco&display=swap');
        
        .stApp {
            background-color: #F2F2F7;
            font-family: -apple-system, BlinkMacSystemFont, sans-serif;
        }
        header, footer {visibility: hidden;}

        /* Cards Gerais */
        div[data-testid="stMetric"], .css-card {
            background-color: #FFFFFF;
            border-radius: 20px;
            padding: 15px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.03);
        }

        /* Botões */
        .stButton > button {
            width: 100%;
            border-radius: 14px;
            height: 50px;
            background-color: #007AFF;
            color: white;
            border: none;
            font-weight: 600;
            font-size: 16px;
            box-shadow: 0 4px 6px rgba(0,122,255,0.2);
        }
        .stButton > button:hover {
            background-color: #0056b3;
            transform: scale(0.99);
        }

        /* Títulos */
        h1, h2, h3 { color: #1C1C1E; font-weight: 700; letter-spacing: -0.5px; }
        
        /* Ajuste do Plotly para parecer nativo */
        .js-plotly-plot .plotly .modebar { display: none; }

        .block-container {
            padding-top: 2rem;
            padding-bottom: 5rem;
            max-width: 500px;
        }
        </style>
    """, unsafe_allow_html=True)

inject_ios_css()

# --- BANCO DE DADOS (JSON) ---
DB_FILE = 'finance_db.json'

def load_data():
    if not os.path.exists(DB_FILE):
        return {"users": {}, "transactions": []}
    with open(DB_FILE, 'r') as f:
        return json.load(f)

def save_data(data):
    with open(DB_FILE, 'w') as f:
        json.dump(data, f, indent=4)

db = load_data()

# --- ESTADO DA SESSÃO ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'user_email' not in st.session_state:
    st.session_state['user_email'] = None

# --- FUNÇÕES LÓGICAS ---
def login_google_mock():
    st.session_state['logged_in'] = True
    st.session_state['user_email'] = "usuario@demo.com"
    st.rerun()

def add_transaction(tipo, valor, categoria, descricao):
    new_trans = {
        "id": int(time.time()),
        "user": st.session_state['user_email'],
        "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "type": tipo,
        "amount": float(valor),
        "category": categoria,
        "desc": descricao
    }
    db['transactions'].append(new_trans)
    save_data(db)
    st.toast("Salvo!", icon="💾")
    time.sleep(0.5)
    st.rerun()

# --- LÓGICA DE INSIGHTS ---
def get_smart_insights(df):
    if df.empty:
        return None
    
    # Converter data
    df['date_dt'] = pd.to_datetime(df['date'])
    df_despesas = df[df['type'] == 'Despesa']
    
    insights = []
    
    # 1. Insight de Maior Categoria (Vilão do Gasto)
    if not df_despesas.empty:
        cat_sum = df_despesas.groupby('category')['amount'].sum().sort_values(ascending=False)
        top_cat = cat_sum.index[0]
        top_val = cat_sum.values[0]
        total_desp = df_despesas['amount'].sum()
        pct = (top_val / total_desp) * 100
        
        msg = f"<b>{top_cat}</b> consome {pct:.0f}% das suas saídas."
        cor = "#FF3B30" if pct > 40 else "#FF9500" # Vermelho se > 40%, Laranja se menos
        insights.append({"titulo": "Foco de Atenção", "msg": msg, "cor": cor, "icon": "⚠️"})

    # 2. Comparativo Mês Atual vs Anterior (Simulado para MVP)
    # Num cenário real, filtrariamos por mês. Aqui vamos simular com base na média.
    media_gasto = df_despesas['amount'].mean()
    ultimo_gasto = df_despesas.iloc[-1]['amount'] if not df_despesas.empty else 0
    
    if ultimo_gasto > media_gasto * 1.5:
        insights.append({
            "titulo": "Gasto Atípico", 
            "msg": f"O último gasto foi 50% acima da sua média.", 
            "cor": "#5856D6", # Roxo Apple
            "icon": "📊"
        })
    elif ultimo_gasto == 0:
        pass
    else:
        insights.append({
            "titulo": "No Controle", 
            "msg": "Seus gastos recentes estão dentro da média.", 
            "cor": "#34C759", # Verde Apple
            "icon": "✅"
        })

    return insights

# --- UI LOGIN ---
if not st.session_state['logged_in']:
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("<h1 style='text-align: center;'>FinSaaS</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #8E8E93;'>Inteligência para o seu dinheiro.</p>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1,10,1])
    with col2:
        if st.button(" Entrar com Google"):
            login_google_mock()

# --- UI APP PRINCIPAL ---
else:
    # 1. Header
    c1, c2 = st.columns([8, 2])
    with c1: st.markdown(f"### Olá, Usuário")
    with c2: 
        if st.button("Sair", key="logout"):
            st.session_state['logged_in'] = False
            st.rerun()

    # 2. Processamento de Dados
    user_txs = [t for t in db['transactions'] if t['user'] == st.session_state['user_email']]
    df = pd.DataFrame(user_txs)
    
    saldo, receitas, despesas = 0, 0, 0
    if not df.empty:
        receitas = df[df['type'] == 'Receita']['amount'].sum()
        despesas = df[df['type'] == 'Despesa']['amount'].sum()
        saldo = receitas - despesas

    # 3. Card de Saldo
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #007AFF 0%, #5856D6 100%); padding: 25px; border-radius: 24px; color: white; margin-bottom: 20px; box-shadow: 0 10px 20px rgba(0,122,255,0.3);">
        <p style="margin:0; font-size: 14px; opacity: 0.9;">Saldo Disponível</p>
        <h1 style="margin:5px 0; font-size: 42px; color: white; letter-spacing: -1px;">R$ {saldo:,.2f}</h1>
        <div style="display: flex; margin-top: 15px; opacity: 0.9; font-size: 13px;">
            <div style="margin-right: 20px;">↓ Saídas: R$ {despesas:,.2f}</div>
            <div>↑ Entradas: R$ {receitas:,.2f}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 4. ÁREA DE SMART INSIGHTS (NOVO)
    if not df.empty and despesas > 0:
        st.markdown("##### 🧠 Insights")
        
        # Gera insights lógicos
        insights_list = get_smart_insights(df)
        
        # Mostra Cards de Texto
        cols = st.columns(len(insights_list))
        for idx, item in enumerate(insights_list):
            with cols[idx]:
                st.markdown(f"""
                <div style="background-color: white; padding: 15px; border-radius: 18px; height: 120px; border-left: 5px solid {item['cor']}; box-shadow: 0 2px 8px rgba(0,0,0,0.05);">
                    <div style="font-size: 24px; margin-bottom: 5px;">{item['icon']}</div>
                    <div style="font-weight: 700; font-size: 13px; color: #8E8E93; text-transform: uppercase;">{item['titulo']}</div>
                    <div style="font-size: 14px; color: #1C1C1E; line-height: 1.4;">{item['msg']}</div>
                </div>
                """, unsafe_allow_html=True)
        
        # Gráfico Donut (Estilo Apple)
        st.markdown("<br>", unsafe_allow_html=True)
        df_desp = df[df['type'] == 'Despesa']
        fig = px.pie(df_desp, values='amount', names='category', hole=0.6, 
                     color_discrete_sequence=px.colors.qualitative.Pastel)
        fig.update_layout(showlegend=False, margin=dict(t=0, b=0, l=0, r=0), height=200, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        fig.update_traces(textinfo='percent+label', textposition='inside')
        
        st.markdown("<div style='background: white; padding: 20px; border-radius: 20px; box-shadow: 0 4px 12px rgba(0,0,0,0.03);'>", unsafe_allow_html=True)
        st.markdown("<h5 style='text-align: center; margin-bottom: 0;'>Distribuição de Gastos</h5>", unsafe_allow_html=True)
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        st.markdown("</div>", unsafe_allow_html=True)

    # 5. Nova Transação (Formulário Otimizado)
    st.markdown("<br>##### Adicionar Movimento", unsafe_allow_html=True)
    with st.container():
        c_tipo, c_cat = st.columns(2)
        with c_tipo:
            tipo = st.selectbox("Tipo", ["Despesa", "Receita"])
        with c_cat:
            categoria = st.selectbox("Categoria", ["Alimentação", "Transporte", "Casa", "Lazer", "Investimento", "Salário", "Outros"])
        
        valor = st.number_input("Valor (R$)", min_value=0.0, step=10.0)
        desc = st.text_input("Descrição", placeholder="Ex: Uber para o trabalho")
        
        if st.button("Confirmar Transação"):
            if valor > 0:
                add_transaction(tipo, valor, categoria, desc)

    # 6. Lista Simples
    st.markdown("<br>##### Histórico", unsafe_allow_html=True)
    if not df.empty:
        for i, row in df.sort_values(by='id', ascending=False).head(5).iterrows():
            color = "#FF3B30" if row['type'] == 'Despesa' else "#34C759"
            sinal = "-" if row['type'] == 'Despesa' else "+"
            st.markdown(f"""
            <div style="background: white; margin-bottom: 10px; padding: 15px; border-radius: 16px; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #F2F2F7;">
                <div>
                    <div style="font-weight: 600; color: #1C1C1E;">{row['category']}</div>
                    <div style="font-size: 12px; color: #8E8E93;">{row['desc']} • {row['date'][5:]}</div>
                </div>
                <div style="font-weight: 700; color: {color}; font-size: 15px;">
                    {sinal} R$ {row['amount']:.2f}
                </div>
            </div>
            """, unsafe_allow_html=True)
