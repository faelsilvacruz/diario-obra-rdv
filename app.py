import streamlit as st
import pandas as pd
from datetime import datetime
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from PIL import Image

st.set_page_config(page_title="Diário de Obra - RDV", layout="centered")

# Título
st.title("📋 Diário de Obra - RDV Engenharia")

# Seção: Identificação da obra
st.header("Informações da Obra")
obra = st.text_input("Obra")
local = st.text_input("Local")
data = st.date_input("Data", value=datetime.today())
contrato = st.text_input("Contrato")

# Seção: Horários
st.header("Horários de Trabalho")
entrada_1 = st.time_input("1ª Entrada")
saida_1 = st.time_input("1ª Saída")
entrada_2 = st.time_input("2ª Entrada")
saida_2 = st.time_input("2ª Saída")

# Seção: Clima
st.header("Condições Climáticas")
clima = st.selectbox("Condições do dia", ["Bom", "Chuva", "Garoa", "Impraticável", "Feriado"])

# Seção: Máquinas e Equipamentos
st.header("Máquinas e Equipamentos")
maquinas = st.text_area("Descreva as máquinas e equipamentos utilizados")

# Seção: Serviços Executados
st.header("Serviços Executados")
servicos = st.text_area("Descreva os serviços executados no dia")

# Seção: Efetivo
st.header("Efetivo de Pessoal")
efetivo = st.text_area("Informe nomes e funções dos colaboradores")

# Seção: Outras Ocorrências
st.header("Outras Ocorrências")
ocorrencias = st.text_area("Observações adicionais")

# Seção: Assinaturas
st.header("Assinaturas")
nome_empresa = st.text_input("Nome do responsável pela empresa")
nome_fiscal = st.text_input("Nome da fiscalização")

# Seção: Upload de Fotos
st.header("Fotos do Dia")
fotos = st.file_uploader("Envie uma ou mais fotos do serviço", accept_multiple_files=True, type=["png", "jpg", "jpeg"])

# Botão para salvar registro
if st.button("💾 Salvar Registro"):
    registro = {
        "Obra": obra,
        "Local": local,
        "Data": data.strftime("%d/%m/%Y"),
        "Contrato": contrato,
        "1ª Entrada": entrada_1.strftime("%H:%M"),
        "1ª Saída": saida_1.strftime("%H:%M"),
        "2ª Entrada": entrada_2.strftime("%H:%M"),
        "2ª Saída": saida_2.strftime("%H:%M"),
        "Clima": clima,
        "Máquinas": maquinas,
        "Serviços": servicos,
        "Efetivo": efetivo,
        "Ocorrências": ocorrencias,
        "Responsável Empresa": nome_empresa,
        "Fiscalização": nome_fiscal
    }

    # Criar pasta de fotos
    fotos_dir = Path("fotos")
    fotos_dir.mkdir(exist_ok=True)

    # Salvar fotos
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

    # Salvar no CSV
    df = pd.DataFrame([registro])
    df.to_csv("registros_diario_obra.csv", mode='a', header=not Path("registros_diario_obra.csv").exists(), index=False)

    st.success("✅ Registro salvo com sucesso!")

# Função para gerar PDF
def gerar_pdf():
    try:
        df = pd.read_csv("registros_diario_obra.csv")
        ultimo = df.iloc[-1]

        Path("relatorios").mkdir(exist_ok=True)
        nome_pdf = f"relatorios/{str(ultimo['Obra']).replace(' ', '_')}_{str(ultimo['Data']).replace('/', '-')}.pdf"
        c = canvas.Canvas(nome_pdf, pagesize=A4)
        largura, altura = A4
        y = altura - 50

        c.setFont("Helvetica-Bold", 16)
        c.drawString(50, y, "📋 Diário de Obra - RDV Engenharia")
        y -= 30
        c.setFont("Helvetica", 12)

        for campo in [
            "Obra", "Local", "Data", "Contrato",
            "1ª Entrada", "1ª Saída", "2ª Entrada", "2ª Saída",
            "Clima", "Máquinas", "Serviços", "Efetivo",
            "Ocorrências", "Responsável Empresa", "Fiscalização"
        ]:
            texto = f"{campo}: {str(ultimo[campo])}"
            for linha in texto.split('\n'):
                c.drawString(50, y, linha)
                y -= 20
                if y < 100:
                    c.showPage()
                    y = altura - 50

        # Inserir imagens
        if "Fotos" in ultimo and pd.notna(ultimo["Fotos"]):
            fotos = str(ultimo["Fotos"]).split(", ")
            for foto_path in fotos:
                try:
                    c.showPage()
                    c.drawString(50, altura - 50, f"📷 Foto: {Path(foto_path).name}")
                    img = Image.open(foto_path)
                    img.thumbnail((500, 500))
                    c.drawImage(ImageReader(img), 50, altura / 2 - 100)
                except Exception as e:
                    c.drawString(50, altura - 100, f"Erro ao carregar imagem: {foto_path}")
                    continue

        c.save()
        st.success(f"📄 PDF gerado com sucesso: {nome_pdf}")
    except Exception as e:
        st.error(f"❌ Erro ao gerar PDF: {e}")

# Botão para gerar PDF
if st.button("📄 Gerar PDF do último registro"):
    gerar_pdf()

