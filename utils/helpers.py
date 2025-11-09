import streamlit as st

def info_icon(label, description):
    st.markdown(
        f"""<span>{label} <span title='{description}' style='cursor: help;'>ℹ️</span></span>""", 
        unsafe_allow_html=True
    )