import streamlit as st
import pandas as pd
import os

from media import render_img_html
from analytics_page import analytics_page
from cabinet_allocation_page import cabinet_allocation_page

import streamlit_authenticator as stauth
from streamlit_authenticator.utilities.hasher import Hasher

st.set_page_config(
    page_title= "📊 Case Vammo",
    layout="wide",
    initial_sidebar_state="expanded")

st.markdown("""
<style>
    [data-testid=stSidebar] {
        background-color: #2EC2FF;
    }
</style>
""", unsafe_allow_html=True)

def main():
    credentials = {
        "usernames": {
            "vammo.client": {
                "name": "Vammo", 
                "password": stauth.Hasher(["vammo_case"]).generate()[0],
            }
        }
    }
    
    authenticator = stauth.Authenticate(
        credentials=credentials,
        cookie_name="some_cookie_name",
        cookie_key="some_signature_key",
        cookie_expiry_days=30,
    )

    with st.sidebar:
        col1, col2, col3 = st.columns([1, 3, 1])
        img_path = os.path.join(os.path.dirname(__file__), '..', 'imgs', 'client_logo.png')
        render_img_html(img_path, 60)
        st.write('')

        authenticator.login(
            location="sidebar",
            fields={'Form name': 'Login', 'Username': 'Usuário', 'Password': 'Senha'}
        )

    if st.session_state["authentication_status"]:
        name = st.session_state["name"]
        username = st.session_state["username"]
        st.sidebar.success(f"Bem-vindo(a), {name}!")
        
        paginas = ["Controle de Estações", "Alocação de Cabinets"]
        page = st.sidebar.radio("Selecione a Página", paginas)
        
        if page == "Controle de Estações":
            analytics_page()
        if page == "Alocação de Cabinets":
            cabinet_allocation_page()
        
        authenticator.logout("Logout", "sidebar")
        
    elif st.session_state["authentication_status"] is False:
        st.sidebar.error("Usuário/senha incorretos.")
        img_path = 'imgs/cover.png'
        render_img_html(img_path, 100)

    elif st.session_state["authentication_status"] is None:
        st.sidebar.warning("Por favor, insira seu nome de usuário e senha.")
        img_path = 'imgs/cover.png'
        render_img_html(img_path, 100)

if __name__ == "__main__":
    main()
