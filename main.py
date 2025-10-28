import streamlit as st
from PIL import Image, ImageDraw
import io

st.set_page_config(page_title="Gerador de Layout de Fotos", layout="wide")

st.title("📸 Gerador de Layout de Fotos para Impressão")
st.markdown("Configure e visualize seu layout de fotos antes de imprimir!")

# === SIDEBAR: CONFIGURAÇÕES ===
with st.sidebar:
    st.header("⚙️ Configurações")
    
    # Canvas Settings
    st.subheader("📐 Tamanho do Canvas")
    canvas_preset = st.selectbox(
        "Predefinições",
        ["Personalizado", "10x15 cm", "A4 (21x29.7 cm)", "A5 (14.8x21 cm)"],
        index=1
    )
    
    if canvas_preset == "10x15 cm":
        default_w, default_h = 15, 10
    elif canvas_preset == "A4 (21x29.7 cm)":
        default_w, default_h = 21, 29.7
    elif canvas_preset == "A5 (14.8x21 cm)":
        default_w, default_h = 14.8, 21
    else:
        default_w, default_h = 15, 10
    
    col1, col2 = st.columns(2)
    with col1:
        canvas_width = st.number_input("Largura (cm)", min_value=5.0, max_value=50.0, value=float(default_w), step=0.1)
    with col2:
        canvas_height = st.number_input("Altura (cm)", min_value=5.0, max_value=50.0, value=float(default_h), step=0.1)
    
    # DPI
    dpi = st.select_slider("DPI (qualidade)", options=[150, 200, 300, 600], value=300)
    
    st.divider()
    
    # Photo Settings
    st.subheader("📷 Dimensões das Fotos")
    photo_preset = st.selectbox(
        "Tamanho padrão",
        ["3x4 cm", "2.5x3.5 cm (Passport US)", "5x7 cm", "Personalizado"],
        index=0
    )
    
    if photo_preset == "3x4 cm":
        default_pw, default_ph = 3.0, 4.0
    elif photo_preset == "2.5x3.5 cm (Passport US)":
        default_pw, default_ph = 2.5, 3.5
    elif photo_preset == "5x7 cm":
        default_pw, default_ph = 5.0, 7.0
    else:
        default_pw, default_ph = 3.0, 4.0
    
    col1, col2 = st.columns(2)
    with col1:
        photo_width = st.number_input("Largura foto (cm)", min_value=1.0, max_value=20.0, value=default_pw, step=0.1)
    with col2:
        photo_height = st.number_input("Altura foto (cm)", min_value=1.0, max_value=30.0, value=default_ph, step=0.1)
    
    st.divider()
    
    # Layout Settings
    st.subheader("📊 Layout")
    col1, col2 = st.columns(2)
    with col1:
        cols = st.number_input("Colunas", min_value=1, max_value=10, value=4, step=1)
    with col2:
        rows = st.number_input("Linhas", min_value=1, max_value=15, value=2, step=1)
    
    total_photos = cols * rows
    st.info(f"**Total: {total_photos} fotos**")
    
    margin_cm = st.slider("Margem entre fotos (cm)", min_value=0.0, max_value=2.0, value=0.5, step=0.05)
    
    st.divider()
    
    # Guide Lines Settings
    st.subheader("✂️ Linhas Guiadoras")
    show_guides = st.checkbox("Mostrar linhas guiadoras", value=True)
    
    if show_guides:
        guide_len_cm = st.slider("Comprimento guia externa (cm)", min_value=0.1, max_value=1.0, value=0.35, step=0.05)
        mini_guide_len_cm = st.slider("Comprimento guia interna (cm)", min_value=0.05, max_value=0.5, value=0.1, step=0.05)
        gap_cm = st.slider("Distância da foto (cm)", min_value=0.0, max_value=0.5, value=0.05, step=0.01)
        
        guide_color = st.color_picker("Cor das linhas", value="#000000")
        guide_opacity = st.slider("Opacidade", min_value=0, max_value=255, value=160, step=5)
        line_width = st.slider("Espessura", min_value=1, max_value=5, value=2, step=1)
    
    st.divider()
    
    # Output Settings
    st.subheader("💾 Saída")
    output_format = st.selectbox("Formato", ["PNG (sem perdas)", "JPEG (menor arquivo)"])
    output_quality = st.slider("Qualidade JPEG", min_value=80, max_value=100, value=100, step=5)

# === MAIN AREA: UPLOAD AND PREVIEW ===
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("📤 Upload das Fotos")
    uploaded_files = st.file_uploader(
        "Selecione suas fotos (JPG, PNG)",
        type=["jpg", "jpeg", "png"],
        accept_multiple_files=True,
        help="Você pode fazer upload de múltiplas fotos"
    )
    
    if uploaded_files:
        st.success(f"✅ {len(uploaded_files)} foto(s) carregada(s)")
        
        # Preview das fotos
        with st.expander("Ver miniaturas das fotos"):
            preview_cols = st.columns(min(4, len(uploaded_files)))
            for idx, file in enumerate(uploaded_files[:8]):  # Max 8 previews
                with preview_cols[idx % 4]:
                    img = Image.open(file)
                    st.image(img, caption=file.name, use_container_width=True)

# === PROCESSING FUNCTIONS ===
def cm_to_px(cm, dpi_val):
    return int(cm / 2.54 * dpi_val)

def load_photo(file):
    """Carrega foto com suporte a JPG, JPEG e PNG"""
    img = Image.open(file)
    if img.mode in ('RGBA', 'LA', 'P'):
        background = Image.new('RGB', img.size, (255, 255, 255))
        if img.mode == 'P':
            img = img.convert('RGBA')
        background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
        img = background
    return img.convert("RGB")

def prepare_photo(img, target_w, target_h):
    """Prepara foto mantendo proporção"""
    img_ratio = img.width / img.height
    target_ratio = target_w / target_h
    
    if img_ratio > target_ratio:
        new_w = int(img.height * target_ratio)
        offset = (img.width - new_w) // 2
        img = img.crop((offset, 0, offset + new_w, img.height))
    else:
        new_h = int(img.width / target_ratio)
        offset = (img.height - new_h) // 2
        img = img.crop((0, offset, img.width, offset + new_h))
    
    return img.resize((target_w, target_h), Image.Resampling.LANCZOS)

def generate_layout(photos, config):
    """Gera o layout com as fotos"""
    # Conversões
    photo_w = cm_to_px(config['photo_width'], config['dpi'])
    photo_h = cm_to_px(config['photo_height'], config['dpi'])
    canvas_w = cm_to_px(config['canvas_width'], config['dpi'])
    canvas_h = cm_to_px(config['canvas_height'], config['dpi'])
    margin = cm_to_px(config['margin_cm'], config['dpi'])
    
    # Prepara fotos
    prepared_photos = []
    for photo in photos:
        img = load_photo(photo)
        img = prepare_photo(img, photo_w, photo_h)
        prepared_photos.append(img)
    
    # Cria canvas
    canvas = Image.new("RGB", (canvas_w, canvas_h), "white")
    
    # Calcula posição centralizada
    total_w = config['cols'] * photo_w + (config['cols'] - 1) * margin
    total_h = config['rows'] * photo_h + (config['rows'] - 1) * margin
    offset_x = (canvas_w - total_w) // 2
    offset_y = (canvas_h - total_h) // 2
    
    # Cola as fotos
    total_slots = config['rows'] * config['cols']
    for i in range(total_slots):
        row, col = divmod(i, config['cols'])
        x = offset_x + col * (photo_w + margin)
        y = offset_y + row * (photo_h + margin)
        
        # Usa fotos ciclicamente
        photo_idx = i % len(prepared_photos)
        canvas.paste(prepared_photos[photo_idx], (x, y))
    
    # Adiciona linhas guiadoras
    if config['show_guides']:
        overlay = Image.new('RGBA', canvas.size, (255, 255, 255, 0))
        draw = ImageDraw.Draw(overlay)
        
        guide_len = cm_to_px(config['guide_len_cm'], config['dpi'])
        mini_guide_len = cm_to_px(config['mini_guide_len_cm'], config['dpi'])
        gap = cm_to_px(config['gap_cm'], config['dpi'])
        
        # Converte cor hex para RGB
        color_rgb = tuple(int(config['guide_color'][i:i+2], 16) for i in (1, 3, 5))
        color = color_rgb + (config['guide_opacity'],)
        lw = config['line_width']
        
        for i in range(total_slots):
            row, col = divmod(i, config['cols'])
            x = offset_x + col * (photo_w + margin)
            y = offset_y + row * (photo_h + margin)
            
            left, right = x, x + photo_w
            top, bottom = y, y + photo_h
            
            # Superior Esquerdo
            v_len = guide_len if row == 0 else mini_guide_len
            h_len = guide_len if col == 0 else mini_guide_len
            draw.line([(left, top - gap - v_len), (left, top - gap)], fill=color, width=lw)
            draw.line([(left - gap - h_len, top), (left - gap, top)], fill=color, width=lw)
            
            # Superior Direito
            h_len = guide_len if col == config['cols'] - 1 else mini_guide_len
            draw.line([(right, top - gap - v_len), (right, top - gap)], fill=color, width=lw)
            draw.line([(right + gap, top), (right + gap + h_len, top)], fill=color, width=lw)
            
            # Inferior Esquerdo
            v_len = guide_len if row == config['rows'] - 1 else mini_guide_len
            h_len = guide_len if col == 0 else mini_guide_len
            draw.line([(left, bottom + gap), (left, bottom + gap + v_len)], fill=color, width=lw)
            draw.line([(left - gap - h_len, bottom), (left - gap, bottom)], fill=color, width=lw)
            
            # Inferior Direito
            h_len = guide_len if col == config['cols'] - 1 else mini_guide_len
            draw.line([(right, bottom + gap), (right, bottom + gap + v_len)], fill=color, width=lw)
            draw.line([(right + gap, bottom), (right + gap + h_len, bottom)], fill=color, width=lw)
        
        canvas = canvas.convert('RGBA')
        canvas = Image.alpha_composite(canvas, overlay)
        canvas = canvas.convert('RGB')
    
    return canvas

# === GENERATE BUTTON ===
with col2:
    st.subheader("🖼️ Preview & Download")
    
    if uploaded_files:
        if st.button("🎨 Gerar Layout", type="primary", use_container_width=True):
            with st.spinner("Gerando layout..."):
                config = {
                    'photo_width': photo_width,
                    'photo_height': photo_height,
                    'canvas_width': canvas_width,
                    'canvas_height': canvas_height,
                    'margin_cm': margin_cm,
                    'cols': cols,
                    'rows': rows,
                    'dpi': dpi,
                    'show_guides': show_guides,
                    'guide_len_cm': guide_len_cm if show_guides else 0,
                    'mini_guide_len_cm': mini_guide_len_cm if show_guides else 0,
                    'gap_cm': gap_cm if show_guides else 0,
                    'guide_color': guide_color if show_guides else "#000000",
                    'guide_opacity': guide_opacity if show_guides else 0,
                    'line_width': line_width if show_guides else 1,
                }
                
                try:
                    result_image = generate_layout(uploaded_files, config)
                    st.session_state['result_image'] = result_image
                    st.success("✅ Layout gerado com sucesso!")
                except Exception as e:
                    st.error(f"Erro ao gerar layout: {str(e)}")
        
        # Display result
        if 'result_image' in st.session_state:
            result_img = st.session_state['result_image']
            
            # Preview
            st.image(result_img, caption="Preview do Layout", use_container_width=True)
            
            # Download button
            buf = io.BytesIO()
            if output_format == "PNG (sem perdas)":
                result_img.save(buf, format='PNG', dpi=(dpi, dpi), optimize=False)
                file_ext = "png"
                mime_type = "image/png"
            else:
                result_img.save(buf, format='JPEG', dpi=(dpi, dpi), quality=output_quality, subsampling=0)
                file_ext = "jpg"
                mime_type = "image/jpeg"
            
            buf.seek(0)
            
            st.download_button(
                label=f"⬇️ Download {output_format.split()[0]}",
                data=buf,
                file_name=f"layout_fotos_{cols}x{rows}.{file_ext}",
                mime=mime_type,
                use_container_width=True
            )
            
            # Info
            st.info(f"""
            **Informações do Layout:**
            - Resolução: {result_img.width}x{result_img.height}px
            - Tamanho físico: {canvas_width}x{canvas_height} cm
            - DPI: {dpi}
            - Total de fotos: {total_photos}
            - Layout: {rows} linhas × {cols} colunas
            """)
    else:
        st.info("👆 Faça upload de fotos para começar")

# === FOOTER ===
st.divider()
st.markdown("""
### 💡 Dicas de Impressão
- Use **papel fotográfico** para melhor qualidade
- Configure a impressora para **modo "Alta Qualidade"**
- Desabilite qualquer **redimensionamento automático**
- Para impressão sem bordas, selecione **"Borderless"** na impressora
- Use **DPI 300** para impressão profissional (600 para qualidade máxima)
""")