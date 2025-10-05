import cv2
import base64
import streamlit as st

def render_img_html(image_path, s):
    image = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)
    
    _, encoded_image = cv2.imencode(".png", image)
    base64_image = base64.b64encode(encoded_image.tobytes()).decode("utf-8")
    
    st.markdown(f"<img style='max-width: {s}%;max-height: {s}%;' src='data:image/png;base64, {base64_image}'/>", unsafe_allow_html=True)
