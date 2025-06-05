import streamlit as st
import pandas as pd
from datetime import datetime
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from PIL import Image
import json  # Alterado de ast para json
import os

st.set_page_config(page_title="Diário de Obra - RDV", layout="centered")

# Leitura de arquivos auxiliares com tratamento de erro
try:
    colab_df = pd.read_csv("colaboradores.csv")
    colaboradores_lista = colab_df["Nome"].tolist()
except FileNotFoundError:
    st.error("Arquivo 'colaboradores.csv' não encontrado")
    colaboradores_lista = []

try:
    obras_df = pd.read_csv("obras.csv")
    obras_lista = [""] + obras_df["Nome"].tolist()
except FileNotFoundError:
    st.error("Arquivo 'obras.csv' não encontrado")
    obras_lista = [""]

try:
    contratos_df = pd.read_csv("contratos.csv")
    contratos_lista = [""] + contratos_df["Nome"].tolist()
except FileNotFoundError:
    st.error("Arquivo 'contratos.csv' não encontrado")
    contratos_lista = [""]

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
        funcao_sugerida = colab_df.loc[colab_df["Nome"] == nome, "Função"].values[0] if not colab_df.empty else ""
        funcao = st.text_input(f"Função", value=funcao_sugerida, key=f"funcao_{i}")
        ent1 = st.time_input("Entrada", value=None, key=f"ent1_{i}")
        sai1 = st.time_input("Saída", value=None, key=f"sai1_{i}")

        efetivo_lista.append({
            "Nome": nome,
            "Função": funcao,
            "Entrada": ent1.strftime("%H:%M") if ent1 else "Não informado",
            "Saída": sai1.strftime("%H:%M") if sai1 else "Não informado"
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

# Função para gerar PDF
def gerar_pdf(registro):
    try:
        Path("relatorios").mkdir(parents=True, exist_ok=True)
        
        # Nome do arquivo mais seguro
        nome_obra = registro['Obra'].replace(' ', '_').replace('/', '-').replace('\\', '-')
        nome_pdf = f"relatorios/Diario_{nome_obra}_{registro['Data'].replace('/', '-')}.pdf"
        
        c = canvas.Canvas(nome_pdf, pagesize=A4)
        largura, altura = A4
        y = altura - 50

        # Cabeçalho
        c.setFont("Helvetica-Bold", 16)
        c.drawString(50, y, "📋 Diário de Obra - RDV Engenharia")
        y -= 30
        c.setFont("Helvetica", 12)

        # Informações gerais
        campos_gerais = ["Obra", "Local", "Data", "Contrato", "Clima", "Máquinas", "Serviços"]
        for campo in campos_gerais:
            valor = str(registro.get(campo, "")).strip()
            if valor.lower() == 'nan' or not valor:
                valor = "Não informado"
            c.drawString(50, y, f"{campo}: {valor}")
            y -= 20

        # Efetivo - usando json em vez de ast
        c.drawString(50, y, "Efetivo:")
        y -= 20
        try:
            efetivo_data = json.loads(registro["Efetivo"].replace("'", '"'))
            for item in efetivo_data:
                linha = f"- {item['Nome']} ({item['Função']}): {item['Entrada']} - {item['Saída']}"
                c.drawString(60, y, linha)
                y -= 20
                if y < 100:  # Verifica se está no final da página
                    c.showPage()
                    y = altura - 50
        except Exception as e:
            c.drawString(60, y, f"Erro ao processar efetivo: {str(e)}")
            y -= 20

        # Rodapé
        c.drawString(50, y, f"Ocorrências: {registro.get('Ocorrências', 'Não informado')}")
        y -= 20
        c.drawString(50, y, f"Responsável Empresa: {registro.get('Responsável Empresa', 'Não informado')}")
        y -= 20
        if registro.get('Fiscalização'):
            c.drawString(50, y, f"Fiscalização: {registro['Fiscalização']}")
            y -= 20

        # Fotos
        if registro.get("Fotos"):
            fotos_list = [f.strip() for f in registro["Fotos"].split(",") if f.strip()]
            for foto_path in fotos_list:
                try:
                    c.showPage()
                    c.drawString(50, altura - 50, f"📷 Foto: {Path(foto_path).name}")
                    img = Image.open(foto_path)
                    img.thumbnail((500, 500))  # Redimensiona mantendo proporção
                    c.drawImage(ImageReader(img), 50, altura / 2 - 100, width=400, preserveAspectRatio=True)
                except Exception as e:
                    c.drawString(50, altura - 100, f"Erro ao carregar imagem: {Path(foto_path).name}")
                    continue

        c.save()
        st.success(f"📄 PDF gerado com sucesso: {nome_pdf}")
        with open(nome_pdf, "rb") as f:
            st.download_button("📥 Baixar PDF", f, file_name=Path(nome_pdf).name)
    except Exception as e:
        st.error(f"Erro ao gerar PDF: {str(e)}")

# Botão de salvar
if st.button("💾 Salvar Registro"):
    registro = {
        "Obra": obra if obra else "Não informado",
        "Local": local if local else "Não informado",
        "Data": data.strftime("%d/%m/%Y"),
        "Contrato": contrato if contrato else "Não informado",
        "Clima": clima,
        "Máquinas": maquinas if maquinas else "Não informado",
        "Serviços": servicos if servicos else "Não informado",
        "Efetivo": json.dumps(efetivo_lista, ensure_ascii=False),  # Usando json.dumps
        "Ocorrências": ocorrencias if ocorrencias else "Não informado",
        "Responsável Empresa": nome_empresa if nome_empresa else "Não informado",
        "Fiscalização": nome_fiscal if nome_fiscal else ""
    }

    # Tratamento de fotos
    fotos_dir = Path("fotos")
    fotos_dir.mkdir(parents=True, exist_ok=True)
    nomes_arquivos = []
    
    if fotos:
        for i, foto in enumerate(fotos):
            try:
                nome_foto = f"{obra}_{data.strftime('%Y-%m-%d')}_foto{i+1}.jpg".replace(" ", "_").replace("/", "-")
                caminho_foto = fotos_dir / nome_foto
                with open(caminho_foto, "wb") as f:
                    f.write(foto.getbuffer())
                nomes_arquivos.append(str(caminho_foto))
            except Exception as e:
                st.warning(f"Erro ao salvar foto {i+1}: {str(e)}")
                continue
        
        registro["Fotos"] = ", ".join(nomes_arquivos)
    else:
        registro["Fotos"] = ""

    # Salvando registro
    try:
        df = pd.DataFrame([registro])
        df.to_csv("registros_diario_obra.csv", mode='a', 
                 header=not Path("registros_diario_obra.csv").exists(), 
                 index=False, encoding='utf-8')
        
        st.success("✅ Registro salvo com sucesso!")
        gerar_pdf(registro)
    except Exception as e:
        st.error(f"Erro ao salvar registro: {str(e)}")