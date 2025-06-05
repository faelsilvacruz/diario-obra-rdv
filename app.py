import streamlit as st
import pandas as pd
from datetime import datetime
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph
from reportlab.lib.colors import HexColor
from PIL import Image
import json
import io

# Configuração da página
st.set_page_config(page_title="Diário de Obra - RDV", layout="centered")

# Leitura dos arquivos CSV
try:
    colab_df = pd.read_csv("colaboradores.csv")
    colaboradores_lista = colab_df["Nome"].tolist()
except Exception as e:
    st.error(f"Erro ao carregar colaboradores: {e}")
    colaboradores_lista = []

try:
    obras_df = pd.read_csv("obras.csv")
    obras_lista = [""] + obras_df["Nome"].tolist()
except Exception as e:
    st.error(f"Erro ao carregar obras: {e}")
    obras_lista = [""]

try:
    contratos_df = pd.read_csv("contratos.csv")
    contratos_lista = [""] + contratos_df["Nome"].tolist()
except Exception as e:
    st.error(f"Erro ao carregar contratos: {e}")
    contratos_lista = [""]

# Interface do usuário
st.title("📋 Diário de Obra - RDV Engenharia")

# Seção 1: Informações da Obra
st.header("1. Informações da Obra")
obra = st.selectbox("Obra", obras_lista)
local = st.text_input("Local")
data = st.date_input("Data", value=datetime.today())
contrato = st.selectbox("Contrato", contratos_lista)

# Seção 2: Condições Climáticas
st.header("2. Condições Climáticas")
clima = st.selectbox("Condições do dia", ["Bom", "Chuva", "Garoa", "Impraticável", "Feriado"])

# Seção 3: Máquinas e Equipamentos
st.header("3. Máquinas e Equipamentos")
maquinas = st.text_area("Descreva as máquinas e equipamentos utilizados")

# Seção 4: Serviços Executados
st.header("4. Serviços Executados")
servicos = st.text_area("Descreva os serviços executados no dia")

# Seção 5: Efetivo de Pessoal
st.header("5. Efetivo de Pessoal")
qtd_colaboradores = st.number_input("Quantos colaboradores hoje?", min_value=1, max_value=10, step=1)
efetivo_lista = []

for i in range(qtd_colaboradores):
    with st.expander(f"👷 Colaborador {i+1}"):
        nome = st.selectbox(f"Nome", colaboradores_lista, key=f"nome_{i}")
        funcao_sugerida = colab_df.loc[colab_df["Nome"] == nome, "Função"].values[0] if not colab_df.empty else ""
        funcao = st.text_input(f"Função", value=funcao_sugerida, key=f"funcao_{i}")
        ent = st.time_input("Entrada", value=None, key=f"ent_{i}")
        sai = st.time_input("Saída", value=None, key=f"sai_{i}")

        efetivo_lista.append({
            "Nome": nome,
            "Função": funcao,
            "Entrada": ent.strftime("%H:%M") if ent else "Não informado",
            "Saída": sai.strftime("%H:%M") if sai else "Não informado"
        })

# Seção 6: Outras Ocorrências
st.header("6. Outras Ocorrências")
ocorrencias = st.text_area("Observações adicionais")

# Seção 7: Assinaturas
st.header("7. Assinaturas")
nome_empresa = st.text_input("Nome do responsável pela empresa")
nome_fiscal = st.text_input("Nome da fiscalização")

# Seção 8: Fotos do Dia
st.header("8. Fotos do Dia")
fotos = st.file_uploader("Envie uma ou mais fotos do serviço", accept_multiple_files=True, type=["png", "jpg", "jpeg"])

def gerar_pdf(registro):
    try:
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        largura, altura = A4

        margem_esquerda = 50
        margem_direita = 50
        margem_superior = 50
        margem_inferior = 50
        largura_util = largura - margem_esquerda - margem_direita
        y = altura - margem_superior

        c.setFont("Helvetica-Bold", 16)
        c.setFillColor(HexColor("#0F2A4D"))  # Cor institucional
        c.drawCentredString(largura / 2, y, "Diário de Obra - RDV Engenharia")
        y -= 30
        c.setFillColor("black")  # Reset cor para texto comum
        c.setFont("Helvetica", 12)

        campos = ["Obra", "Local", "Data", "Contrato", "Clima", "Máquinas", "Serviços"]
        for campo in campos:
            valor = str(registro.get(campo, "")).strip()
            if valor.lower() == 'nan' or not valor:
                valor = "Não informado"
            c.drawString(margem_esquerda, y, f"{campo}: {valor}")
            y -= 20

        c.drawString(margem_esquerda, y, "5. Efetivo de Pessoal:")
        y -= 20

        try:
            efetivo_data = json.loads(registro.get("Efetivo", "[]"))
            if efetivo_data:
                for item in efetivo_data:
                    linha = f"- {item.get('Nome', 'Não informado')} ({item.get('Função', 'Não informado')}): " \
                            f"{item.get('Entrada', 'Não informado')} - {item.get('Saída', 'Não informado')}"
                    if y < margem_inferior + 20:
                        c.showPage()
                        y = altura - margem_superior
                        c.setFont("Helvetica", 12)
                    c.drawString(margem_esquerda + 10, y, linha)
                    y -= 15
            else:
                c.drawString(margem_esquerda + 10, y, "Nenhum colaborador registrado")
                y -= 15
        except Exception as e:
            c.drawString(margem_esquerda + 10, y, f"Erro ao carregar efetivo: {str(e)}")
            y -= 15

        c.save()
        buffer.seek(0)
        return buffer
    except Exception as e:
        st.error(f"Erro na geração do PDF: {str(e)}")
        return None

if st.button("💾 Salvar Registro"):
    efetivo_para_salvar = []
    for colaborador in efetivo_lista:
        efetivo_para_salvar.append({
            "Nome": colaborador.get("Nome", "Não informado"),
            "Função": colaborador.get("Função", "Não informado"),
            "Entrada": colaborador.get("Entrada", "Não informado"),
            "Saída": colaborador.get("Saída", "Não informado")
        })

    registro = {
        "Obra": obra if obra else "Não informado",
        "Local": local if local else "Não informado",
        "Data": data.strftime("%d/%m/%Y"),
        "Contrato": contrato if contrato else "Não informado",
        "Clima": clima,
        "Máquinas": maquinas if maquinas else "Não informado",
        "Serviços": servicos if servicos else "Não informado",
        "Efetivo": json.dumps(efetivo_para_salvar, ensure_ascii=False),
        "Ocorrências": ocorrencias if ocorrencias else "Nenhuma ocorrência registrada",
        "Responsável Empresa": nome_empresa if nome_empresa else "Não informado",
        "Fiscalização": nome_fiscal if nome_fiscal else ""
    }

    pdf_buffer = gerar_pdf(registro)
    if pdf_buffer:
        nome_pdf = f"Diario_{obra.replace(' ', '_')}_{data.strftime('%Y-%m-%d')}.pdf"
        st.download_button(
            label="📥 Baixar PDF",
            data=pdf_buffer,
            file_name=nome_pdf,
            mime="application/pdf"
        )
        st.success("PDF gerado com sucesso!")
