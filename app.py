import base64
import pandas as pd
import streamlit as st
import folium
from streamlit_folium import st_folium

from snow_checker import load_forecast, to_table, will_it_snow_between

st.set_page_config(
    page_title="Laurins Schneevorhersage",
    page_icon="❄️"
)

st.markdown(
    """
    <style>
    /* Zentrierter blauer Hauptbutton */
    div.stButton > button {
        display: block;
        margin: 2rem auto;
        background-color: #1f77ff;
        color: white;
        font-weight: 700;
        font-size: 1.1rem;
        padding: 0.6rem 2.2rem;
        border-radius: 10px;
        border: none;
    }

    div.stButton > button:hover {
        background-color: #155edb;
        color: white;
    }
    </style>
    """,
    unsafe_allow_html=True
)

PLACES = {
    "Bettingen (BS)": (47.57, 7.66),
    "Basel SBB": (47.547, 7.589),
    "Davos": (46.802, 9.835),
    "Zermatt": (46.020, 7.749),
    "Zürich": (47.376, 8.541),
    "Flims/Laax": (46.838, 9.286),
    "Grindelwald": (46.624, 8.035),
    "Hasliberg": (46.757, 8.151),
    "St. Moritz": (46.498, 9.839),
    "Innsbruck": (47.265, 11.393)
}


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
            background: rgba(255,255,255,0.85);
            border-radius: 16px;
            padding: 1.2rem;
            max-width: 900px;   /* hält Textblock angenehm schmal */
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def ensure_state_defaults() -> None:
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


def draw_clickable_map() -> None:
    previous = st.session_state.get("map")
    if previous and previous.get("last_clicked"):
        st.session_state.lat = previous["last_clicked"]["lat"]
        st.session_state.lon = previous["last_clicked"]["lng"]

    m = folium.Map(
        location=[st.session_state.lat, st.session_state.lon],
        zoom_start=11,
        control_scale=True,
    )

    folium.Marker(
        [st.session_state.lat, st.session_state.lon],
        tooltip="Gewählter Ort",
    ).add_to(m)

    st_folium(
        m,
        height=500,
        use_container_width=True,  # ← ENTSCHEIDEND
        key="map"
    )

# --- UI START ---
set_background("davos.jpg")
ensure_state_defaults()

st.title("Schneit es noch vor Weihnachten?")
st.write("Wir prüfen die Wettervorhersage: Gibt es irgendwo Schneefall (> 0 cm) im gewählten Zeitraum?")

# Zeitraum
start_date = st.date_input("Startdatum", value=pd.to_datetime("2025-12-16").date())
end_date = st.date_input("Enddatum", value=pd.to_datetime("2025-12-25").date())

# Ort per Dropdown
st.selectbox(
    "Ort auswählen (Marker springt dorthin). Danach mit Single-Click auf der Karte feinjustieren.",
    list(PLACES.keys()),
    key="place_name",
    on_change=on_place_change,
)


# Karte
st.subheader("Ort auf der Karte anklicken (Single-Click)")
draw_clickable_map()

# Forecast
if st.button("❄️Schneevorhersage berechnen"):
    data = load_forecast(st.session_state.lat, st.session_state.lon)
    df = to_table(data)

    will_snow, total_snow_cm, snow_hours, window = will_it_snow_between(
        df, str(start_date), str(end_date)
    )

    if will_snow:
        st.success(f"Ja – Schneefall in der Vorhersage. ❄️: {total_snow_cm:.2f} cm")
        st.dataframe(snow_hours[["time", "snowfall_cm", "temp_c"]], use_container_width=True)
    else:
        st.warning("Nein – kein Schneefall (> 0 cm) in der Vorhersage für diesen Zeitraum.")

    st.caption("Hinweis: Vorhersagen werden unsicherer, je weiter sie in der Zukunft liegen.")
    st.dataframe(window[["time", "snowfall_cm", "temp_c", "precip_mm"]], use_container_width=True)
