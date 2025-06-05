import streamlit as st
import pandas as pd
from datetime import datetime
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Paragraph, Frame, KeepInFrame, Image as ReportLabImage
from reportlab.lib.units import inch, mm
from reportlab.lib.colors import HexColor
from PIL import Image as PILImage
import json
import io
import textwrap

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
        ent = st.time_input("Entrada", key=f"ent_{i}")
        sai = st.time_input("Saída", key=f"sai_{i}")

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

def gerar_pdf(registro, fotos_paths=None):
    try:
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4
        
        # Configurações de layout
        margin_left = 20 * mm
        margin_right = 20 * mm
        margin_top = 20 * mm
        margin_bottom = 20 * mm
        content_width = width - margin_left - margin_right
        
        # Estilos
        styles = getSampleStyleSheet()
        
        # Estilo para título centralizado
        estilo_titulo = ParagraphStyle(
            'TituloCentralizado',
            parent=styles['Heading1'],
            textColor=HexColor("#0F2A4D"),
            alignment=1,  # 0=esquerda, 1=centro, 2=direita
            spaceAfter=14
        )
        
        estilo_normal = ParagraphStyle(
            'Normal',
            parent=styles['Normal'],
            fontSize=12,
            leading=14,
            spaceAfter=6,
            spaceBefore=6
        )
        
        estilo_destaque = ParagraphStyle(
            'Destaque',
            parent=styles['Normal'],
            fontSize=12,
            leading=14,
            fontName='Helvetica-Bold',
            spaceAfter=6
        )
        
        # Função para adicionar parágrafos com controle de página
        def add_paragraph(text, style, y_pos):
            p = Paragraph(text, style)
            w, h = p.wrap(content_width, height)
            if y_pos - h < margin_bottom:
                c.showPage()
                y_pos = height - margin_top
                # Redefine o estilo da fonte após quebra de página
                c.setFont("Helvetica", 12)
            p.drawOn(c, margin_left, y_pos - h)
            return y_pos - h - 6
        
        y_pos = height - margin_top
        
        # Título centralizado
        p_titulo = Paragraph("<b>DIÁRIO DE OBRA - RDV ENGENHARIA</b>", estilo_titulo)
        w, h = p_titulo.wrap(content_width, height)
        p_titulo.drawOn(c, (width - w) / 2, y_pos - h)  # Centraliza horizontalmente
        y_pos -= h + 10 * mm
        
        # Informações básicas
        campos = ["Obra", "Local", "Data", "Contrato", "Clima", "Máquinas"]
        for campo in campos:
            valor = str(registro.get(campo, "")).strip()
            if valor.lower() == 'nan' or not valor:
                valor = "Não informado"
            
            texto = f"<b>{campo}:</b> {valor}"
            y_pos = add_paragraph(texto, estilo_normal, y_pos)
        
        # Serviços Executados
        y_pos = add_paragraph("<b>Serviços Executados:</b>", estilo_destaque, y_pos)
        
        servicos_texto = registro.get("Serviços", "Não informado").strip()
        for linha in textwrap.wrap(servicos_texto, width=100):
            y_pos = add_paragraph(linha, estilo_normal, y_pos)
        
        # Efetivo de Pessoal (sem o número 5)
        y_pos = add_paragraph("<b>Efetivo de Pessoal:</b>", estilo_destaque, y_pos)
        
        try:
            efetivo_data = json.loads(registro.get("Efetivo", "[]"))
            for item in efetivo_data:
                texto = f"- {item.get('Nome', 'Não informado')} ({item.get('Função', 'Não informado')}): " \
                       f"{item.get('Entrada', 'Não informado')} - {item.get('Saída', 'Não informado')}"
                y_pos = add_paragraph(texto, estilo_normal, y_pos)
        except Exception as e:
            y_pos = add_paragraph(f"Erro ao carregar efetivo: {str(e)}", estilo_normal, y_pos)
        
        # Outras Ocorrências
        y_pos = add_paragraph("<b>Outras Ocorrências:</b>", estilo_destaque, y_pos)
        y_pos = add_paragraph(registro.get("Ocorrências", "Nenhuma ocorrência registrada"), estilo_normal, y_pos)
        
        # Assinaturas
        y_pos = add_paragraph("<b>Assinaturas:</b>", estilo_destaque, y_pos)
        y_pos = add_paragraph(f"Responsável Empresa: {registro.get('Responsável Empresa', 'Não informado')}", estilo_normal, y_pos)
        
        if registro.get("Fiscalização"):
            y_pos = add_paragraph(f"Fiscalização: {registro['Fiscalização']}", estilo_normal, y_pos)
        
        # Adicionar fotos se existirem
        if fotos_paths:
            for foto_path in fotos_paths:
                try:
                    # Nova página para cada foto
                    c.showPage()
                    y_pos = height - margin_top
                    
                    # Título da foto
                    y_pos = add_paragraph(f"<b>Foto: {Path(foto_path).name}</b>", estilo_destaque, y_pos)
                    y_pos -= 10  # Espaço adicional
                    
                    # Carrega e redimensiona a imagem
                    img = PILImage.open(foto_path)
                    img_width, img_height = img.size
                    aspect = img_height / float(img_width)
                    
                    # Define o tamanho máximo da imagem
                    max_width = content_width
                    max_height = height - margin_top - margin_bottom - 50  # Deixa espaço para legenda
                    
                    if img_width > max_width:
                        img_height = int(max_width * aspect)
                        img_width = max_width
                        if img_height > max_height:
                            img_width = int(max_height / aspect)
                            img_height = max_height
                    
                    # Centraliza a imagem
                    x_pos = (width - img_width) / 2
                    
                    # Desenha a imagem
                    c.drawImage(foto_path, x_pos, y_pos - img_height, width=img_width, height=img_height)
                    
                except Exception as e:
                    # Se houver erro, mostra mensagem no PDF
                    c.showPage()
                    y_pos = height - margin_top
                    y_pos = add_paragraph(f"Erro ao carregar imagem: {Path(foto_path).name}", estilo_normal, y_pos)
                    continue
        
        c.save()
        buffer.seek(0)
        return buffer
        
    except Exception as e:
        st.error(f"Erro na geração do PDF: {str(e)}")
        return None

if st.button("💾 Salvar Registro"):
    # Pré-processamento do efetivo
    efetivo_para_salvar = []
    for colaborador in efetivo_lista:
        efetivo_para_salvar.append({
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
        "Efetivo": json.dumps(efetivo_para_salvar, ensure_ascii=False),
        "Ocorrências": ocorrencias if ocorrencias else "Nenhuma ocorrência registrada",
        "Responsável Empresa": nome_empresa if nome_empresa else "Não informado",
        "Fiscalização": nome_fiscal if nome_fiscal else ""
    }

    # Processamento de fotos
    fotos_dir = Path("fotos")
    fotos_dir.mkdir(parents=True, exist_ok=True)
    fotos_paths = []
    
    if fotos:
        for i, foto in enumerate(fotos):
            try:
                nome_foto = f"{obra}_{data.strftime('%Y-%m-%d')}_foto{i+1}.jpg".replace(" ", "_").replace("/", "-")
                caminho_foto = fotos_dir / nome_foto
                with open(caminho_foto, "wb") as f:
                    f.write(foto.getbuffer())
                fotos_paths.append(str(caminho_foto))
            except Exception as e:
                st.warning(f"Erro ao salvar foto {i+1}: {str(e)}")
                continue

    # Geração do PDF com as fotos
    pdf_buffer = gerar_pdf(registro, fotos_paths if fotos_paths else None)
    if pdf_buffer:
        nome_pdf = f"Diario_{obra.replace(' ', '_')}_{data.strftime('%Y-%m-%d')}.pdf"
        st.download_button(
            label="📥 Baixar PDF",
            data=pdf_buffer,
            file_name=nome_pdf,
            mime="application/pdf"
        )
        st.success("PDF gerado com sucesso!")