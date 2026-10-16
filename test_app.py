import streamlit as st

st.set_page_config(page_title="CIRCULO Test", layout="wide")

st.title("CIRCULO ♻️")
st.subheader("Smart Recycling Assistant")

st.success("The application is displaying correctly!")

col1, col2, col3 = st.columns(3)

col1.metric("Items Recorded", 1)
col2.metric("Items Recycled", 0)
col3.metric("Waste Weight", "0.5 kg")

st.write("If you can see this text, Streamlit rendering works.")