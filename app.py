import base64
import pandas as pd
import streamlit as st
import folium
from streamlit_folium import st_folium

from snow_checker import load_forecast, to_table, will_it_snow_between


# --------------------------------------------------
# PAGE CONFIG (DESKTOP-FIRST)
# --------------------------------------------------
st.set_page_config(
    page_title="Laurins Schneevorhersage",
    page_icon="❄️",
    layout="wide",   # ← WICHTIG
)


# --------------------------------------------------
# DATA
# --------------------------------------------------
PLACES = {
    "Bettingen (BS)": (47.57, 7.66),
    "Basel SBB": (47.547, 7.589),
    "Davos": (46.802, 9.835),
    "Zermatt": (46.020, 7.749),
    "Zürich": (47.376, 8.541),
    "Flims / Laax": (46.838, 9.286),
    "Grindelwald": (46.624, 8.035),
    "Hasliberg": (46.757, 8.151),
    "Arosa": (46.777, 9.678),
    "St. Gallen": (47.424, 9.375),
    "Klosters": (46.9, 9.9),
    "Churwalden": (46.78, 9.54),
    "St. Moritz": (46.488, 9.835),
    "Innsbruck": (47.268, 11.393),
}


# --------------------------------------------------
# BACKGROUND
# --------------------------------------------------
def set_background(image_file: str) -> None:
    with open(image_file, "rb") as f:
        data = f.read()
    b64 = base64.b64encode(data).decode()

    st.markdown(
        f"""
        <style>
        .stApp {{
            background-image: url("data:image/jpg;base64,{b64}");
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
        }}
       
       
        .block-container {{
            background: rgba(255,255,255,0.88);
            border-radius: 16px;
            padding: 1.5rem;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


# --------------------------------------------------
# STATE
# --------------------------------------------------
if "lat" not in st.session_state:
    st.session_state.lat = 47.57
if "lon" not in st.session_state:
    st.session_state.lon = 7.66
if "place_name" not in st.session_state:
    st.session_state.place_name = "Bettingen (BS)"


def on_place_change() -> None:
    lat, lon = PLACES[st.session_state.place_name]
    st.session_state.lat = lat
    st.session_state.lon = lon


# --------------------------------------------------
# UI START
# --------------------------------------------------
set_background("davos.jpg")

st.title("❄️ Schneit es noch vor Weihnachten?")
st.write(
    "Wir prüfen, ob es zwischen dem 16.12. und 25.12. "
    "an einem Ort in der Schweiz oder Umgebung schneit."
)

# Zeitraum
start_date = st.date_input("Startdatum", value=pd.to_datetime("2025-12-16").date())
end_date = st.date_input("Enddatum", value=pd.to_datetime("2025-12-25").date())

# Ort
st.selectbox(
    "Ort auswählen",
    list(PLACES.keys()),
    key="place_name",
    on_change=on_place_change,
)

# Karte
st.subheader("Ort auf der Karte anklicken")
m = folium.Map(
    location=[st.session_state.lat, st.session_state.lon],
    zoom_start=11,
    control_scale=True,
)

folium.Marker(
    [st.session_state.lat, st.session_state.lon],
    tooltip="Gewählter Ort",
).add_to(m)

map_data = st_folium(m, height=500)

if map_data and map_data.get("last_clicked"):
    st.session_state.lat = map_data["last_clicked"]["lat"]
    st.session_state.lon = map_data["last_clicked"]["lng"]

st.write(
    f"Aktuelle Koordinaten: "
    f"{st.session_state.lat:.5f}, {st.session_state.lon:.5f}"
)


# --------------------------------------------------
# FORECAST
# --------------------------------------------------
st.divider()

if st.button("❄️ Schneevorhersage berechnen"):
    with st.spinner("Berechne Vorhersage…"):
        data = load_forecast(st.session_state.lat, st.session_state.lon)
        df = to_table(data)

        will_snow, total_snow_cm, snow_hours, window = will_it_snow_between(
            df, str(start_date), str(end_date)
        )

    st.subheader("Ergebnis")

    if will_snow:
        st.success(
            f"❄️ Ja – es wird schneien. "
            f"Erwartete Schneemenge: {total_snow_cm:.2f} cm"
        )
        st.dataframe(
            snow_hours[["time", "snowfall_cm", "temp_c"]],
            use_container_width=True,
        )
    else:
        st.warning("🌧️ Nein – laut Vorhersage kein Schneefall in diesem Zeitraum.")

    st.caption(
        "Hinweis: Wettervorhersagen werden unsicherer, "
        "je weiter sie in der Zukunft liegen."
    )

    st.dataframe(
        window[["time", "snowfall_cm", "temp_c", "precip_mm"]],
        use_container_width=True,
    )
