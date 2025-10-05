from PIL import Image
import streamlit as st
import os
import io
import base64

def render_img_html(image_path, s):
    # Garante path absoluto
    abs_path = os.path.join(os.path.dirname(__file__), image_path)

    if not os.path.exists(abs_path):
        st.error(f"Imagem não encontrada: {abs_path}")
        return

    # Abre imagem com PIL
    image = Image.open(abs_path)

    # Converte para bytes em PNG
    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    encoded_image = base64.b64encode(buffered.getvalue()).decode("utf-8")

    # Exibe no Streamlit como HTML
    st.markdown(
        f"<img style='max-width: {s}%; max-height: {s}%;' src='data:image/png;base64,{encoded_image}'/>",
        unsafe_allow_html=True
    )
