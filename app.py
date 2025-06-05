import streamlit as st
import pandas as pd
from datetime import datetime
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph
from PIL import Image
import json
import os

# Configuração da página
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
        ent1 = st.time_input("Entrada", value=None, key=f"ent1_{i}")
        sai1 = st.time_input("Saída", value=None, key=f"sai1_{i}")

        efetivo_lista.append({
            "Nome": nome,
            "Função": funcao,
            "Entrada": ent1.strftime("%H:%M") if ent1 else "Não informado",
            "Saída": sai1.strftime("%H:%M") if sai1 else "Não informado"
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

# Função para gerar PDF com todas as correções
def gerar_pdf(registro):
    try:
        # Configurações iniciais
        Path("relatorios").mkdir(parents=True, exist_ok=True)
        nome_pdf = f"relatorios/Diario_{registro['Obra'].replace(' ', '_')}_{registro['Data'].replace('/', '-')}.pdf"
        c = canvas.Canvas(nome_pdf, pagesize=A4)
        largura, altura = A4
        
        # Configurações de layout
        margem_esquerda = 50
        margem_direita = 50
        margem_superior = 50
        margem_inferior = 50
        largura_util = largura - margem_esquerda - margem_direita
        
        # Estilos
        estilo_normal = ParagraphStyle(
            name='Normal',
            fontName='Helvetica',
            fontSize=12,
            leading=14,
            alignment=4,  # Justificado
            wordWrap='LTR'
        )
        
        estilo_titulo = ParagraphStyle(
            name='Titulo',
            fontName='Helvetica-Bold',
            fontSize=16,
            leading=18,
            alignment=0,  # Esquerda
            spaceAfter=20
        )

        estilo_destaque = ParagraphStyle(
            name='Destaque',
            fontName='Helvetica-Bold',
            fontSize=12,
            leading=14,
            alignment=0,
            spaceAfter=10
        )

        y = altura - margem_superior

        # Título
        p_titulo = Paragraph("<b>DIÁRIO DE OBRA - RDV ENGENHARIA</b>", estilo_titulo)
        w, h = p_titulo.wrap(largura_util, altura)
        p_titulo.drawOn(c, margem_esquerda, y - h)
        y -= h + 20

        # Informações básicas
        campos = ["Obra", "Local", "Data", "Contrato", "Clima", "Máquinas"]
        for campo in campos:
            valor = str(registro.get(campo, '')).strip()
            if valor.lower() == 'nan' or not valor:
                valor = "Não informado"
            
            texto = f"<b>{campo}:</b> {valor}"
            p = Paragraph(texto, estilo_normal)
            w, h = p.wrap(largura_util, altura)
            
            if y - h < margem_inferior:
                c.showPage()
                y = altura - margem_superior
            
            p.drawOn(c, margem_esquerda, y - h)
            y -= h + 5

        # Serviços Executados
        p_serv = Paragraph("<b>Serviços Executados:</b>", estilo_destaque)
        w, h = p_serv.wrap(largura_util, altura)
        if y - h < margem_inferior:
            c.showPage()
            y = altura - margem_superior
        p_serv.drawOn(c, margem_esquerda, y - h)
        y -= h + 5

        servicos_texto = str(registro.get('Serviços', '')).strip()
        if servicos_texto.lower() == 'nan' or not servicos_texto:
            servicos_texto = "Não informado"
        
        p = Paragraph(servicos_texto, estilo_normal)
        w, h = p.wrap(largura_util, altura)
        
        if y - h < margem_inferior:
            c.showPage()
            y = altura - margem_superior
        
        p.drawOn(c, margem_esquerda, y - h)
        y -= h + 15

        # Efetivo de Pessoal
        p_efetivo = Paragraph("<b>Efetivo de Pessoal:</b>", estilo_destaque)
        w, h = p_efetivo.wrap(largura_util, altura)
        if y - h < margem_inferior:
            c.showPage()
            y = altura - margem_superior
        p_efetivo.drawOn(c, margem_esquerda, y - h)
        y -= h + 5

        try:
            efetivo_data = json.loads(registro["Efetivo"])
            if efetivo_data:
                for item in efetivo_data:
                    texto_colab = f"- {item.get('Nome', 'Não informado')} ({item.get('Função', 'Não informado')}): " \
                                f"{item.get('Entrada', 'Não informado')} - {item.get('Saída', 'Não informado')}"
                    
                    p = Paragraph(texto_colab, estilo_normal)
                    w, h = p.wrap(largura_util, altura)
                    
                    if y - h < margem_inferior:
                        c.showPage()
                        y = altura - margem_superior
                    
                    p.drawOn(c, margem_esquerda + 10, y - h)
                    y -= h + 5
            else:
                p = Paragraph("Nenhum colaborador registrado", estilo_normal)
                w, h = p.wrap(largura_util, altura)
                p.drawOn(c, margem_esquerda, y - h)
                y -= h + 5
        except Exception as e:
            p = Paragraph(f"Erro ao processar efetivo: {str(e)}", estilo_normal)
            w, h = p.wrap(largura_util, altura)
            p.drawOn(c, margem_esquerda, y - h)
            y -= h + 5

        # Outras Ocorrências
        p_ocorrencias = Paragraph("<b>Outras Ocorrências:</b>", estilo_destaque)
        w, h = p_ocorrencias.wrap(largura_util, altura)
        if y - h < margem_inferior:
            c.showPage()
            y = altura - margem_superior
        p_ocorrencias.drawOn(c, margem_esquerda, y - h)
        y -= h + 5

        ocorrencias_texto = str(registro.get('Ocorrências', '')).strip()
        if ocorrencias_texto.lower() == 'nan' or not ocorrencias_texto:
            ocorrencias_texto = "Nenhuma ocorrência registrada"
        
        p = Paragraph(ocorrencias_texto, estilo_normal)
        w, h = p.wrap(largura_util, altura)
        
        if y - h < margem_inferior:
            c.showPage()
            y = altura - margem_superior
        
        p.drawOn(c, margem_esquerda, y - h)
        y -= h + 15

        # Assinaturas
        p_assinaturas = Paragraph("<b>Assinaturas:</b>", estilo_destaque)
        w, h = p_assinaturas.wrap(largura_util, altura)
        if y - h < margem_inferior:
            c.showPage()
            y = altura - margem_superior
        p_assinaturas.drawOn(c, margem_esquerda, y - h)
        y -= h + 10

        # Responsável
        texto_resp = f"Responsável pela Empresa: {registro.get('Responsável Empresa', 'Não informado')}"
        p = Paragraph(texto_resp, estilo_normal)
        w, h = p.wrap(largura_util, altura)
        p.drawOn(c, margem_esquerda, y - h)
        y -= h + 10

        # Fiscalização
        if registro.get('Fiscalização'):
            texto_fiscal = f"Fiscalização: {registro['Fiscalização']}"
            p = Paragraph(texto_fiscal, estilo_normal)
            w, h = p.wrap(largura_util, altura)
            p.drawOn(c, margem_esquerda, y - h)
            y -= h + 10

        # Fotos (se houver)
        if registro.get("Fotos"):
            fotos_list = [f.strip() for f in registro["Fotos"].split(",") if f.strip()]
            for foto_path in fotos_list:
                try:
                    c.showPage()
                    y = altura - margem_superior
                    
                    # Título da foto
                    p = Paragraph(f"<b>Foto: {Path(foto_path).name}</b>", estilo_destaque)
                    w, h = p.wrap(largura_util, altura)
                    p.drawOn(c, margem_esquerda, y - h)
                    y -= h + 20
                    
                    # Imagem
                    img = Image.open(foto_path)
                    img.thumbnail((500, 500))
                    c.drawImage(ImageReader(img), margem_esquerda, y - 300, width=400, preserveAspectRatio=True)
                except Exception as e:
                    c.showPage()
                    y = altura - margem_superior
                    p = Paragraph(f"Erro ao carregar imagem: {Path(foto_path).name}", estilo_normal)
                    w, h = p.wrap(largura_util, altura)
                    p.drawOn(c, margem_esquerda, y - h)
                    y -= h + 10

        c.save()
        st.success(f"📄 PDF gerado com sucesso: {nome_pdf}")
        with open(nome_pdf, "rb") as f:
            st.download_button("📥 Baixar PDF", f, file_name=Path(nome_pdf).name)

    except Exception as e:
        st.error(f"Erro ao gerar PDF: {str(e)}")

# Botão de salvar registro
if st.button("💾 Salvar Registro"):
    # Pré-processamento do efetivo
    efetivo_formatado = []
    for colaborador in efetivo_lista:
        efetivo_formatado.append({
            "Nome": colaborador.get("Nome", "Não informado"),
            "Função": colaborador.get("Função", "Não informado"),
            "Entrada": colaborador.get("Entrada", "Não informado"),
            "Saída": colaborador.get("Saída", "Não informado")
        })
    
    # Criação do registro
    registro = {
        "Obra": obra if obra else "Não informado",
        "Local": local if local else "Não informado",
        "Data": data.strftime("%d/%m/%Y"),
        "Contrato": contrato if contrato else "Não informado",
        "Clima": clima,
        "Máquinas": maquinas if maquinas else "Não informado",
        "Serviços": servicos if servicos else "Não informado",
        "Efetivo": json.dumps(efetivo_formatado, ensure_ascii=False),
        "Ocorrências": ocorrencias if ocorrencias else "Nenhuma ocorrência registrada",
        "Responsável Empresa": nome_empresa if nome_empresa else "Não informado",
        "Fiscalização": nome_fiscal if nome_fiscal else ""
    }

    # Processamento de fotos
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
        
        registro["Fotos"] = ",".join(nomes_arquivos)
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