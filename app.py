import streamlit as st
import pandas as pd
from datetime import datetime
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from PIL import Image
import ast

st.set_page_config(page_title="Diário de Obra - RDV", layout="centered")

# Leitura da lista de colaboradores
colab_df = pd.read_csv("colaboradores.csv")
colaboradores_lista = colab_df["Nome"].tolist()

# Leitura da lista de obras e contratos
obras_df = pd.read_csv("obras.csv")
obras_lista = [""].__add__(obras_df["Nome"].tolist())
contratos_df = pd.read_csv("contratos.csv")
contratos_lista = [""].__add__(contratos_df["Nome"].tolist())

# Título
st.title("📋 Diário de Obra - RDV Engenharia")

# Informações da Obra
st.header("1. Informações da Obra")
obra = st.selectbox("Obra", obras_lista)
local = st.text_input("Local")
data = st.date_input("Data", value=datetime.today())
contrato = st.selectbox("Contrato", contratos_lista)

# Clima
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
        funcao_sugerida = colab_df.loc[colab_df["Nome"] == nome, "Função"].values[0]
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
st.header("8. Fotos do Dia")
fotos = st.file_uploader("Envie uma ou mais fotos do serviço", accept_multiple_files=True, type=["png", "jpg", "jpeg"])

# Botão de salvar
if st.button("💾 Salvar Registro"):
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

    # Gerar PDF automaticamente
    try:
        Path("relatorios").mkdir(exist_ok=True)
        nome_pdf = f"relatorios/{str(registro['Obra']).replace(' ', '_')}_{registro['Data'].replace('/', '-')}.pdf"
        c = canvas.Canvas(nome_pdf, pagesize=A4)
        largura, altura = A4
        y = altura - 50

        c.setFont("Helvetica-Bold", 16)
        c.drawString(50, y, "📋 Diário de Obra - RDV Engenharia")
        y -= 30
        c.setFont("Helvetica", 12)

        campos = ["Obra", "Local", "Data", "Contrato", "Clima", "Máquinas"]
        for campo in campos:
            texto = f"{campo}: {registro[campo]}"
            c.drawString(50, y, texto)
            y -= 20

        c.drawString(50, y, "Serviços:")
        y -= 20
        for linha in registro["Serviços"].split("\n"):
            c.drawString(60, y, linha)
            y -= 20

        c.drawString(50, y, "Efetivo:")
        y -= 20
        efetivo = ast.literal_eval(registro["Efetivo"])
        for item in efetivo:
            linha = f"- {item['Nome']} ({item['Função']}): {item['1ª Entrada']} - {item['1ª Saída']} | {item['2ª Entrada']} - {item['2ª Saída']}"
            c.drawString(60, y, linha)
            y -= 20

        c.drawString(50, y, f"Ocorrências: {registro['Ocorrências']}")
        y -= 20
        c.drawString(50, y, f"Responsável Empresa: {registro['Responsável Empresa']}")
        y -= 20
        if registro['Fiscalização'].strip():
            c.drawString(50, y, f"Fiscalização: {registro['Fiscalização']}")
            y -= 20

        if registro["Fotos"]:
            fotos = registro["Fotos"].split(", ")
            for foto_path in fotos:
                try:
                    c.showPage()
                    c.drawString(50, altura - 50, f"📷 Foto: {Path(foto_path).name}")
                    img = Image.open(foto_path)
                    img.thumbnail((500, 500))
                    c.drawImage(ImageReader(img), 50, altura / 2 - 100)
                except Exception:
                    c.drawString(50, altura - 100, f"Erro ao carregar imagem: {foto_path}")
                    continue

        c.save()
        st.success(f"📄 PDF gerado com sucesso: {nome_pdf}")
    except Exception as e:
        st.error(f"❌ Erro ao gerar PDF: {e}")
