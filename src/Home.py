import streamlit as st

st.set_page_config(
    page_title="SuppleMentor",
    page_icon="🧬",
)

st.image("./src/logo.png")
st.title("SuppleMentor: Revolutionize Your Health")

st.sidebar.success("Select a page above")

st.markdown(
    """
    The Smart Way to Customize Your Supplement Journey! Get expert advice on dosages, avoid interactions, and tailor your regimen for sharper focus, better sleep, and optimal fitness.
    """
)
