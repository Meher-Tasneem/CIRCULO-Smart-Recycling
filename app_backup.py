import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="CIRCULO | Smart Recycling Assistant",
    page_icon="♻️",
    layout="wide"
)

# Store recycling records during the current session
if "records" not in st.session_state:
    st.session_state.records = []

# Header
st.title("♻️ CIRCULO")
st.subheader("Smart Recycling Assistant")
st.write(
    "Give waste a second life. Identify materials, "
    "track recycling, and understand environmental impact."
)

st.divider()

# Navigation
page = st.sidebar.radio(
    "NAVIGATION",
    ["Dashboard", "Waste Scanner", "Material Passport", "Impact Lab"]
)

st.sidebar.divider()
st.sidebar.caption("CIRCULO | Circular Waste Intelligence")

# Dashboard
if page == "Dashboard":
    st.header("Your Recycling Dashboard")
    st.write("An overview of your recycling activity.")

    total_items = len(st.session_state.records)
    recycled_items = sum(
        1 for item in st.session_state.records
        if item["Status"] == "Recycled"
    )
    total_weight = sum(
        item["Weight (kg)"] for item in st.session_state.records
    )

    col1, col2, col3 = st.columns(3)

    col1.metric("Items Recorded", total_items)
    col2.metric("Items Recycled", recycled_items)
    col3.metric("Total Weight", f"{total_weight:.1f} kg")

    st.divider()
    st.subheader("How CIRCULO Works")

    a, b, c = st.columns(3)

    with a:
        st.markdown("### 1. Scan")
        st.write("Upload a photo of a waste item.")

    with b:
        st.markdown("### 2. Track")
        st.write("Record the material and its recycling status.")

    with c:
        st.markdown("### 3. Improve")
        st.write("Review recorded waste and recycling progress.")

    if st.session_state.records:
        st.subheader("Recent Material Records")
        st.dataframe(
            pd.DataFrame(st.session_state.records),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No material records yet. Open Material Passport to add one.")

# Waste Scanner
elif page == "Waste Scanner":
    st.header("Waste Scanner")
    st.write("Upload a photo of a waste item to begin.")

    photo = st.file_uploader(
        "Choose a waste photo",
        type=["png", "jpg", "jpeg"]
    )

    if photo is not None:
        st.image(photo, caption="Uploaded waste item", width=400)
        st.info(
            "Photo upload is working. AI identification is not connected yet; "
            "the team will integrate the tested classifier here."
        )

# Material Passport
elif page == "Material Passport":
    st.header("Material Passport")
    st.write("Create a record and track the item's recycling journey.")

    with st.form("material_form"):
        item_name = st.text_input("Item name")

        material = st.selectbox(
            "Material type",
            ["Plastic", "Paper", "Glass", "Metal", "Organic", "Other"]
        )

        status = st.selectbox(
            "Current status",
            ["Detected", "Collected", "Sorted", "Processed", "Recycled"]
        )

        weight = st.number_input(
            "Estimated weight (kg)",
            min_value=0.0,
            max_value=10000.0,
            value=0.5,
            step=0.1
        )

        submitted = st.form_submit_button("Save Material Record")

    if submitted:
        if not item_name.strip():
            st.warning("Please enter an item name.")
        else:
            st.session_state.records.append({
                "Item": item_name.strip(),
                "Material": material,
                "Status": status,
                "Weight (kg)": weight
            })
            st.success(f"Record saved for {item_name.strip()}!")

    if st.session_state.records:
        st.subheader("All Material Records")
        st.dataframe(
            pd.DataFrame(st.session_state.records),
            use_container_width=True,
            hide_index=True
        )

        csv_data = pd.DataFrame(
            st.session_state.records
        ).to_csv(index=False).encode("utf-8")

        st.download_button(
            "Download Records as CSV",
            data=csv_data,
            file_name="circulo_material_records.csv",
            mime="text/csv"
        )

# Impact Lab
elif page == "Impact Lab":
    st.header("Impact Lab")
    st.write("Explore the amount of waste you plan to recycle.")

    weight = st.number_input(
        "Waste to recycle (kg)",
        min_value=0.0,
        max_value=10000.0,
        value=1.0,
        step=0.5
    )

    st.metric("Planned Recycling Weight", f"{weight:.1f} kg")

    st.caption(
        "This is a weight estimate, not a verified environmental impact "
        "calculation. Reliable impact factors will be added after validation."
    )

st.divider()
st.caption("CIRCULO | Smart Recycling Assistant | Prototype")