import streamlit as st
import pandas as pd
from datetime import datetime
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from PIL import Image
import ast
import textwrap

st.set_page_config(page_title="Diário de Obra - RDV", layout="centered")

# Leitura da lista de colaboradores
colab_df = pd.read_csv("colaboradores.csv")
colaboradores_lista = colab_df["Nome"].tolist()

# Título
st.title("📋 Diário de Obra - RDV Engenharia")

# Informações da Obra
st.header("1. Informações da Obra")
obra = st.text_input("Obra")
local = st.text_input("Local")
data = st.date_input("Data", value=datetime.today())
contrato = st.text_input("Contrato")

# Máquinas e equipamentos
st.header("2. Máquinas e Equipamentos")
maquinas = st.text_area("Descreva as máquinas e equipamentos utilizados")

# Serviços Executados
st.header("3. Serviços Executados")
servicos = st.text_area("Descreva os serviços executados no dia")

# Efetivo de Pessoal
st.header("4. Efetivo de Pessoal")
qtd_colaboradores = st.number_input("Quantos colaboradores hoje?", min_value=1, max_value=10, step=1)
efetivo_lista = []

for i in range(qtd_colaboradores):
    with st.expander(f"👷 Colaborador {i+1}"):
        nome = st.selectbox(f"Nome", colaboradores_lista, key=f"nome_{i}")
        funcao_sugerida = colab_df.loc[colab_df["Nome"] == nome, "Função"].values[0]
        funcao = st.text_input(f"Função", value=funcao_sugerida, key=f"funcao_{i}")
        ent1 = st.time_input("Entrada", key=f"ent1_{i}")
        sai1 = st.time_input("Saída", key=f"sai1_{i}")

        efetivo_lista.append({
            "Nome": nome,
            "Função": funcao,
            "Entrada": ent1.strftime("%H:%M"),
            "Saída": sai1.strftime("%H:%M")
        })
