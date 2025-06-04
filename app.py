import streamlit as st
import pandas as pd
from datetime import datetime
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from PIL import Image

st.set_page_config(page_title="Diário de Obra - RDV", layout="centered")

# Leitura da lista de colaboradores
colab_df = pd.read_csv("colaboradores.csv")
colaboradores_lista = colab_df["Nome"].tolist()

# Leitura da lista de obras
obras_df = pd.read_csv("obras.csv")
obras_lista = [""] + obras_df["Nome"].dropna().tolist()

# Leitura da lista de contratos
contratos_df = pd.read_csv("contratos.csv")
contratos_lista = [""] + contratos_df["Nome"].dropna().tolist()

# Título
st.title("📋 Diário de Obra - RDV Engenharia")

# Informações da Obra
st.header("1. Informações da Obra")
obra = st.selectbox("Obra", obras_lista)
local = st.text_input("Local")
data = st.date_input("Data", value=datetime.today())
contrato = st.selectbox("Contrato", contratos_lista)

# Condições Climáticas
st.header("2. Condições Climáticas")
clima = st.selectbox("Condições do dia", ["Bom", "Chuva", "Garoa", "Impraticável", "Feriado"])

# Máquinas e equipamentos
st.header("3. Máquinas e Equipamentos")
maquinas = st.text_area("Descreva as máquinas e equipamentos utilizados")

# Serviços Executados
st.header("4. Serviços Executados")
servicos = st.text_area("Descreva os serviços executados no dia")

# Efetivo de Pessoal
st.header("5. Efetivo de Pessoal")
qtd_colaboradores = st.number_input("Quantos colaboradores hoje?", min_value=1, max_value=10, step=1)
efetivo_lista = []

for i in range(qtd_colaboradores):
    with st.expander(f"👷 Colaborador {i+1}"):
        nome = st.selectbox(f"Nome", colaboradores_lista, key=f"nome_{i}")
        funcao_sugerida = colab_df.loc[colab_df["Nome"] == nome, "Função"].values[0] if nome else ""
        funcao = st.text_input(f"Função", value=funcao_sugerida, key=f"funcao_{i}")
        ent1 = st.time_input("1ª Entrada", key=f"ent1_{i}")
        sai1 = st.time_input("1ª Saída", key=f"sai1_{i}")
        ent2 = st.time_input("2ª Entrada", key=f"ent2_{i}")
        sai2 = st.time_input("2ª Saída", key=f"sai2_{i}")

        efetivo_lista.append({
            "Nome": nome,
            "Função": funcao,
            "1ª Entrada": ent1.strftime("%H:%M"),
            "1ª Saída": sai1.strftime("%H:%M"),
            "2ª Entrada": ent2.strftime("%H:%M"),
            "2ª Saída": sai2.strftime("%H:%M")
        })

# Outras ocorrências
st.header("6. Outras Ocorrências")
ocorrencias = st.text_area("Observações adicionais")

# Assinaturas
st.header("7. Assinaturas")
nome_empresa = st.text_input("Nome do responsável pela empresa")
nome_fiscal = st.text_input("Nome da fiscalização")

# Upload de fotos
tf = "8. Fotos do Dia"
st.header(tf)
fotos = st.file_uploader("Envie uma ou mais fotos do serviço", accept_multiple_files=True, type=["png", "jpg", "jpeg"])

# Botão de salvar
if st.button("📂 Salvar Registro"):
    registro = {
        "Obra": obra,
        "Local": local,
        "Data": data.strftime("%d/%m/%Y"),
        "Contrato": contrato,
        "Clima": clima,
        "Máquinas": maquinas,
        "Serviços": servicos,
        "Efetivo": str(efetivo_lista),
        "Ocorrências": ocorrencias,
        "Responsável Empresa": nome_empresa,
        "Fiscalização": nome_fiscal
    }

    fotos_dir = Path("fotos")
    fotos_dir.mkdir(exist_ok=True)

    nomes_arquivos = []
    if fotos:
        for i, foto in enumerate(fotos):
            nome_foto = f"{obra}_{data.strftime('%Y-%m-%d')}_foto{i+1}.jpg".replace(" ", "_")
            caminho_foto = fotos_dir / nome_foto
            with open(caminho_foto, "wb") as f:
                f.write(foto.getbuffer())
            nomes_arquivos.append(str(caminho_foto))
        registro["Fotos"] = ", ".join(nomes_arquivos)
    else:
        registro["Fotos"] = ""

    df = pd.DataFrame([registro])
    df.to_csv("registros_diario_obra.csv", mode='a', header=not Path("registros_diario_obra.csv").exists(), index=False)

    st.success("✅ Registro salvo com sucesso!")
