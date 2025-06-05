import streamlit as st
import pandas as pd
from datetime import datetime
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from PIL import Image
import json
import io

st.set_page_config(page_title="Diário de Obra - RDV", layout="centered")

colab_df = pd.read_csv("colaboradores.csv")
colaboradores_lista = colab_df["Nome"].tolist()

obras_df = pd.read_csv("obras.csv")
obras_lista = [""] + obras_df["Nome"].tolist()

contratos_df = pd.read_csv("contratos.csv")
contratos_lista = [""] + contratos_df["Nome"].tolist()

st.title("📋 Diário de Obra - RDV Engenharia")

st.header("1. Informações da Obra")
obra = st.selectbox("Obra", obras_lista)
local = st.text_input("Local")
data = st.date_input("Data", value=datetime.today())
contrato = st.selectbox("Contrato", contratos_lista)

st.header("2. Condições Climáticas")
clima = st.selectbox("Condições do dia", ["Bom", "Chuva", "Garoa", "Impraticável", "Feriado"])

st.header("3. Máquinas e Equipamentos")
maquinas = st.text_area("Descreva as máquinas e equipamentos utilizados")

st.header("4. Serviços Executados")
servicos = st.text_area("Descreva os serviços executados no dia")

st.header("5. Efetivo de Pessoal")
qtd_colaboradores = st.number_input("Quantos colaboradores hoje?", min_value=1, max_value=10, step=1)
efetivo_lista = []

for i in range(qtd_colaboradores):
    with st.expander(f"👷 Colaborador {i+1}"):
        nome = st.selectbox(f"Nome", colaboradores_lista, key=f"nome_{i}")
        funcao_sugerida = colab_df.loc[colab_df["Nome"] == nome, "Função"].values[0]
        funcao = st.text_input(f"Função", value=funcao_sugerida, key=f"funcao_{i}")
        ent = st.time_input("Entrada", value=None, key=f"ent_{i}")
        sai = st.time_input("Saída", value=None, key=f"sai_{i}")

        efetivo_lista.append({
            "Nome": nome,
            "Função": funcao,
            "Entrada": ent.strftime("%H:%M") if ent else "",
            "Saída": sai.strftime("%H:%M") if sai else ""
        })

st.header("6. Outras Ocorrências")
ocorrencias = st.text_area("Observações adicionais")

st.header("7. Assinaturas")
nome_empresa = st.text_input("Nome do responsável pela empresa")
nome_fiscal = st.text_input("Nome da fiscalização")

st.header("8. Fotos do Dia")
fotos = st.file_uploader("Envie uma ou mais fotos do serviço", accept_multiple_files=True, type=["png", "jpg", "jpeg"])

if st.button("💾 Salvar Registro"):
    registro = {
        "Obra": obra,
        "Local": local,
        "Data": data.strftime("%d/%m/%Y"),
        "Contrato": contrato,
        "Clima": clima,
        "Máquinas": maquinas,
        "Serviços": servicos,
        "Efetivo": json.dumps(efetivo_lista),
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

    try:
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        largura, altura = A4
        y = altura - 50

        c.setFont("Helvetica-Bold", 16)
        c.drawString(50, y, "📋 Diário de Obra - RDV Engenharia")
        y -= 30
        c.setFont("Helvetica", 12)

        campos_gerais = ["Obra", "Local", "Data", "Contrato", "Clima", "Máquinas", "Serviços"]
        for campo in campos_gerais:
            c.drawString(50, y, f"{campo}: {registro[campo]}")
            y -= 20

        c.drawString(50, y, "Efetivo:")
        y -= 20
        try:
            efetivo_data = json.loads(registro.get("Efetivo", "[]"))
            for item in efetivo_data:
                linha = f"- {item['Nome']} ({item['Função']}): {item['Entrada']} - {item['Saída']}"
                c.drawString(60, y, linha)
                y -= 20
        except Exception as e:
            c.drawString(60, y, f"Erro ao exibir efetivo: {e}")
            y -= 20

        c.drawString(50, y, f"Ocorrências: {registro['Ocorrências']}")
        y -= 20
        c.drawString(50, y, f"Responsável Empresa: {registro['Responsável Empresa']}")
        y -= 20
        if pd.notna(registro['Fiscalização']) and str(registro['Fiscalização']).strip():
            c.drawString(50, y, f"Fiscalização: {registro['Fiscalização']}")
            y -= 20

        if registro.get("Fotos"):
            fotos = str(registro["Fotos"]).split(", ")
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
        buffer.seek(0)
        nome_pdf = f"{registro['Obra'].replace(' ', '_')}__{registro['Data'].replace('/', '-')}.pdf"
        st.download_button("📥 Baixar PDF", buffer, file_name=nome_pdf)

    except Exception as e:
        st.error(f"Erro ao gerar PDF: {e}")
