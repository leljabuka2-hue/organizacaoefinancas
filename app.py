import streamlit as st
import pandas as pd
import json
import os
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import time
from streamlit_option_menu import option_menu

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Minhas Finanças", page_icon="💰", layout="wide")

# --- CSS PERSONALIZADO (STYLE INJECTION) ---
def inject_custom_css():
    st.markdown("""
        <style>
        /* IMPORT FONTE */
        @import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700&display=swap');

        /* GERAL */
        .stApp {
            background-color: #F4F7FC; /* Fundo cinza azulado bem claro */
            font-family: 'Nunito', sans-serif;
        }

        /* REMOVER PADDING PADRÃO */
        .block-container {
            padding-top: 1.5rem;
            padding-bottom: 2rem;
        }

        /* SIDEBAR */
        section[data-testid="stSidebar"] {
            background-color: #FFFFFF;
            box-shadow: 2px 0 5px rgba(0,0,0,0.05);
        }

        /* CARDS GERAIS (CONTAINERS BRANCOS) */
        .white-card {
            background-color: #FFFFFF;
            border-radius: 15px;
            padding: 20px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.05);
            margin-bottom: 20px;
            height: 100%;
        }

        /* CARD STEPPER (Saldo Inicial -> Atual) */
        .step-item {
            display: flex;
            align-items: flex-start;
            margin-bottom: 15px;
            position: relative;
        }
        .step-icon {
            width: 30px; 
            height: 30px; 
            border-radius: 50%;
            display: flex; 
            align-items: center; 
            justify-content: center;
            color: white;
            font-weight: bold;
            z-index: 2;
            margin-right: 15px;
            flex-shrink: 0;
        }
        .step-line {
            position: absolute;
            left: 14px;
            top: 30px;
            bottom: -20px;
            width: 2px;
            background-color: #E0E0E0;
            z-index: 1;
        }
        .step-last .step-line { display: none; }
        
        /* CARDS COLORIDOS (VISÃO GERAL) */
        .color-card {
            border-radius: 15px;
            padding: 20px;
            color: white;
            box-shadow: 0 4px 10px rgba(0,0,0,0.1);
            display: flex;
            align-items: center;
            margin-bottom: 10px;
        }
        .cc-icon {
            background-color: rgba(255,255,255,0.2);
            width: 45px; height: 45px;
            border-radius: 50%;
            display: flex; align-items: center; justify-content: center;
            font-size: 20px;
            margin-right: 15px;
        }
        
        /* TABELA CUSTOMIZADA */
        .custom-table {
            width: 100%;
            border-collapse: collapse;
        }
        .custom-table th {
            text-align: left;
            color: #888;
            font-weight: 600;
            padding: 10px;
            border-bottom: 1px solid #eee;
        }
        .custom-table td {
            padding: 15px 10px;
            border-bottom: 1px solid #f9f9f9;
            color: #333;
            font-weight: 600;
        }
        
        /* CORES ESPECÍFICAS DA IMAGEM */
        .bg-blue { background-color: #2D9CDB; } /* Azul */
        .bg-green { background-color: #27AE60; } /* Verde */
        .bg-red { background-color: #EB5757; }   /* Vermelho */
        .bg-yellow { background-color: #F2C94C; } /* Amarelo */

        .text-blue { color: #2D9CDB; }
        .text-gray { color: #828282; font-size: 13px; }
        .val-big { font-size: 22px; font-weight: 700; color: #333; }
        
        /* AJUSTES PLOTLY */
        .js-plotly-plot .plotly .modebar { display: none !important; }

        </style>
    """, unsafe_allow_html=True)

inject_custom_css()

# --- MOCK DB ---
def get_data():
    # Simulando dados iguais aos da imagem
    return {
        "saldo_inicial": 2041.11,
        "saldo_atual": 5120.23,
        "previsto": 3745.37,
        "contas": [
            {"banco": "Bradesco", "rec": 6609.73, "desp": 2273.94, "saldo": 4883.19, "prev": 4399.39, "img": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3f/Logo_Bradesco.svg/1200px-Logo_Bradesco.svg.png"},
            {"banco": "Nubank", "rec": 0.00, "desp": 2470.93, "saldo": 175.44, "prev": -715.62, "img": "https://logodownload.org/wp-content/uploads/2019/08/nubank-logo-3.png"}
        ],
        "despesas_pendentes": 17,
        "valor_pendente": 2080.86,
        "categorias": {"Moradia": 30, "Variaveis": 31, "Outros": 7, "Pagamentos": 8, "Demais": 24} # % fictícia
    }

data = get_data()

# --- SIDEBAR ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2910/2910768.png", width=50) # Logo genérico
    st.markdown("<h3 style='text-align: center; color: #333;'>Minhas Finanças</h3>", unsafe_allow_html=True)
    
    selected = option_menu(
        menu_title=None,
        options=["Visão Geral", "Contas", "Cartões", "Metas"],
        icons=["grid-fill", "bank", "credit-card", "bullseye"],
        default_index=0,
        styles={
            "container": {"padding": "0!important", "background-color": "white"},
            "icon": {"color": "#888", "font-size": "18px"}, 
            "nav-link": {"font-size": "15px", "text-align": "left", "margin":"5px", "color": "#555"},
            "nav-link-selected": {"background-color": "#E3F2FD", "color": "#2D9CDB"},
        }
    )

# --- CABEÇALHO SUPERIOR ---
c_top1, c_top2 = st.columns([6, 2])
with c_top1:
    st.markdown("##") # Espaço
with c_top2:
    # Simulando seletor de mês e botão +
    st.markdown("""
    <div style="display: flex; justify-content: flex-end; align-items: center; gap: 10px;">
        <div style="background: white; padding: 8px 15px; border-radius: 20px; color: #555; font-weight: 600; box-shadow: 0 2px 5px rgba(0,0,0,0.05);">‹ Junho ›</div>
        <div style="background: #2D9CDB; width: 40px; height: 40px; border-radius: 50%; color: white; display: flex; align-items: center; justify-content: center; font-size: 24px; cursor: pointer;">+</div>
        <div style="background: #ddd; width: 40px; height: 40px; border-radius: 50%;"></div>
    </div>
    """, unsafe_allow_html=True)

# --- LINHA 1: SALDOS & GRÁFICOS ---
c1, c2, c3 = st.columns([3, 4, 3])

# Card 1: Stepper Vertical (Saldo)
with c1:
    st.markdown(f"""
    <div class="white-card">
        <div class="step-item">
            <div class="step-line"></div>
            <div class="step-icon" style="background-color: #2D9CDB;">✓</div>
            <div>
                <div class="val-big" style="font-size: 16px; color: #888; font-weight: 400;">R$ {data['saldo_inicial']:,.2f}</div>
                <div class="text-gray">Inicial</div>
            </div>
        </div>
        <div class="step-item">
            <div class="step-line"></div>
            <div class="step-icon" style="background-color: #2D9CDB; box-shadow: 0 0 0 4px #D6EAF8;"></div>
            <div>
                <div class="val-big">R$ {data['saldo_atual']:,.2f}</div>
                <div class="text-gray">Saldo atual</div>
            </div>
        </div>
        <div class="step-item step-last">
            <div class="step-icon" style="background-color: #E0E0E0; color: #888;">🕒</div>
            <div>
                <div class="val-big" style="font-size: 18px; color: #888;">R$ {data['previsto']:,.2f}</div>
                <div class="text-gray">Previsto</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# Card 2: Gráfico de Área (Evolução)
with c2:
    st.markdown('<div class="white-card" style="padding: 10px;">', unsafe_allow_html=True)
    st.markdown("<p style='color:#555; font-weight:600; margin-left: 10px;'>Evolução das despesas</p>", unsafe_allow_html=True)
    
    # Mock data graph
    days = ['01/06', '02/06', '03/06', '04/06', '05/06', '06/06', '07/06']
    vals = [200, 1600, 100, 50, 120, 150, 100]
    
    fig_area = go.Figure()
    fig_area.add_trace(go.Scatter(x=days, y=vals, fill='tozeroy', mode='lines+markers', 
                                  line=dict(color='#EB5757', width=2),
                                  marker=dict(size=6, color='#EB5757')))
    
    fig_area.update_layout(
        margin=dict(l=20, r=20, t=10, b=20),
        height=180,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        showlegend=False,
        xaxis=dict(showgrid=False, tickfont=dict(size=10, color='#999')),
        yaxis=dict(showgrid=True, gridcolor='#f0f0f0', tickfont=dict(size=10, color='#999'))
    )
    st.plotly_chart(fig_area, use_container_width=True, config={'displayModeBar': False})
    st.markdown('</div>', unsafe_allow_html=True)

# Card 3: Pendências
with c3:
    st.markdown(f"""
    <div class="white-card" style="text-align: center; display: flex; flex-direction: column; justify-content: center; align-items: center;">
        <div style="font-weight: 600; color: #EB5757; margin-bottom: 10px;">Despesas</div>
        <div style="background-color: #FDEDEE; width: 60px; height: 60px; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin-bottom: 15px;">
            <span style="font-size: 24px; color: #EB5757;">🧾</span>
        </div>
        <p style="color: #555; font-size: 14px; margin-bottom: 15px;">
            Você tem <b>{data['despesas_pendentes']} despesas pendentes</b> no total de <br>
            <span style="font-size: 18px; font-weight: 700; color: #333;">R$ {data['valor_pendente']:,.2f}</span>
        </p>
        <button style="background: white; border: 1px solid #EB5757; color: #EB5757; padding: 5px 20px; border-radius: 20px; font-weight: 600; cursor: pointer;">Verificar</button>
    </div>
    """, unsafe_allow_html=True)

# --- LINHA 2: CARDS COLORIDOS (VISÃO GERAL) ---
st.markdown("<h4 style='color: #555; margin-bottom: 15px;'>Visão geral</h4>", unsafe_allow_html=True)
row2_1, row2_2, row2_3, row2_4 = st.columns(4)

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

with row2_1: st.markdown(card_html("bg-blue", "🏛️", "Contas", "R$ 5.125,23"), unsafe_allow_html=True)
with row2_2: st.markdown(card_html("bg-green", "➕", "Receitas", "R$ 5.903,73"), unsafe_allow_html=True)
with row2_3: st.markdown(card_html("bg-red", "➖", "Despesas", "R$ 2.774,61"), unsafe_allow_html=True)
with row2_4: st.markdown(card_html("bg-yellow", "⇄", "Balanço transf.", "R$ 50,00"), unsafe_allow_html=True)

# --- LINHA 3: TABELA E DONUT CHART ---
st.markdown("<br>", unsafe_allow_html=True)
c_bot1, c_bot2 = st.columns([2, 1])

# Tabela de Contas
with c_bot1:
    st.markdown('<div class="white-card">', unsafe_allow_html=True)
    st.markdown("<h4 style='color: #555;'>Contas</h4>", unsafe_allow_html=True)
    
    # Tabela HTML construída na mão para controle total do design
    table_html = """
    <table class="custom-table">
        <thead>
            <tr>
                <th>Descrição</th>
                <th>Receitas</th>
                <th>Despesas</th>
                <th>Saldo</th>
                <th>Previsto</th>
            </tr>
        </thead>
        <tbody>
    """
    
    for row in data['contas']:
        color_prev = "#EB5757" if row['prev'] < 0 else "#333"
        table_html += f"""
        <tr>
            <td style="display: flex; align-items: center; gap: 10px;">
                <img src="{row['img']}" width="30" style="border-radius: 4px;"> {row['banco']}
            </td>
            <td style="color: #27AE60;">R$ {row['rec']:,.2f}</td>
            <td style="color: #EB5757;">R$ {row['desp']:,.2f}</td>
            <td>R$ {row['saldo']:,.2f}</td>
            <td style="color: {color_prev};">R$ {row['prev']:,.2f}</td>
        </tr>
        """
    
    table_html += "</tbody></table></div>"
    st.markdown(table_html, unsafe_allow_html=True)

# Gráfico Donut (Despesas por Categoria)
with c_bot2:
    st.markdown('<div class="white-card">', unsafe_allow_html=True)
    c_h1, c_h2 = st.columns([8,1])
    with c_h1: st.markdown("<h4 style='color: #555;'>Despesas por categoria</h4>", unsafe_allow_html=True)
    
    cats = list(data['categorias'].keys())
    values = list(data['categorias'].values())
    
    # Cores inspiradas no gráfico da imagem (Roxo, Vermelho, Cinza)
    colors = ['#8E44AD', '#EB5757', '#95A5A6', '#F39C12', '#34495E']
    
    fig_donut = go.Figure(data=[go.Pie(labels=cats, values=values, hole=.6)])
    fig_donut.update_traces(
        marker=dict(colors=colors),
        textinfo='percent',
        textposition='inside',
        hoverinfo='label+value'
    )
    fig_donut.update_layout(
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
        margin=dict(t=0, b=0, l=0, r=0),
        height=250
    )
    
    # Texto Central no Donut
    fig_donut.add_annotation(text="<b>R$ 4.855,47</b>", showarrow=False, font=dict(size=16, color="#333"))
    
    st.plotly_chart(fig_donut, use_container_width=True, config={'displayModeBar': False})
    st.markdown('</div>', unsafe_allow_html=True)
