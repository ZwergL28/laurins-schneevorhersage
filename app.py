import base64
import pandas as pd
import streamlit as st
import folium
from streamlit_folium import st_folium

from snow_checker import load_forecast, to_table, will_it_snow_between

st.set_page_config(
    page_title="Laurins Schneevorhersage",
    page_icon="❄️",
    layout="centered",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
    /* Grössere Touch-Ziele für Mobile */
    button {
        min-height: 48px;
    }

    /* Überschriften nicht zu breit */
    h1, h2, h3 {
        text-align: center;
    }

    /* Karte auf Mobile etwas höher */
    @media (max-width: 600px) {
        iframe {
            height: 70vh !important;
        }
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
    "Arosa": (46.777, 9.678),
    "St. Gallen": (47.424, 9.375),
    "Klosters": (46.9, 9.9),
    "Churwalden":(9.54, 46.78),
    "St. Moritz":(46.488, 9.835),
    "Innsbruck": (47.268, 11.393)
}

st.set_page_config(page_title="Laurins Schneevorhersage")

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

st.markdown(
    """
    <style>
    /* Zentrierter Hauptbutton */
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


def ensure_state_defaults() -> None:
    if "lat" not in st.session_state:
        st.session_state.lat = 47.57
    if "lon" not in st.session_state:
        st.session_state.lon = 7.66
    if "place_name" not in st.session_state:
        st.session_state.place_name = "Bettingen (BS)"
    if "map_fullscreen" not in st.session_state:
        st.session_state.map_fullscreen = False


def on_place_change() -> None:
    lat, lon = PLACES[st.session_state.place_name]
    st.session_state.lat = lat
    st.session_state.lon = lon


def draw_clickable_map() -> None:
    # Klick-Daten aus dem letzten Render lesen
    previous = st.session_state.get("map")
    if previous and previous.get("last_clicked"):
        st.session_state.lat = previous["last_clicked"]["lat"]
        st.session_state.lon = previous["last_clicked"]["lng"]

    # Nur die Karte wird "fullscreen" (hoch), nicht die ganze App
    map_height = 850 if st.session_state.map_fullscreen else 450
    zoom = 10 if st.session_state.map_fullscreen else 11

    m = folium.Map(
        location=[st.session_state.lat, st.session_state.lon],
        zoom_start=zoom,
        control_scale=True,
    )

    folium.Marker(
        [st.session_state.lat, st.session_state.lon],
        tooltip="Gewählter Ort",
    ).add_to(m)

    st_folium(m, height=map_height, width=None, key="map")


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

# Checkbox direkt unter der Karte
st.checkbox("Karte gross anzeigen", key="map_fullscreen")

# Optional: Rest einklappen, damit es sich wie „Kartenmodus“ anfühlt
with st.expander("Infos (einklappen für mehr Platz)", expanded=not st.session_state.map_fullscreen):
    st.write(f"Aktueller Ort (Koordinaten): {st.session_state.lat:.5f}, {st.session_state.lon:.5f}")

# Forecast
# ---------- ANKER OBEN (für "Zurück zur Karte") ----------
st.markdown("<div id='top'></div>", unsafe_allow_html=True)

# ---------- BUTTON ----------
if st.button("❄️ Schneevorhersage berechnen"):

    with st.spinner("Berechne Schneevorhersage…"):
        data = load_forecast(st.session_state.lat, st.session_state.lon)
        df = to_table(data)

        will_snow, total_snow_cm, snow_hours, window = will_it_snow_between(
            df, str(start_date), str(end_date)
        )

    # ---------- ANKER FÜR ERGEBNIS ----------
    st.markdown("<div id='result'></div>", unsafe_allow_html=True)

    # ---------- AUTO-SCROLL ZUM ERGEBNIS ----------
    st.markdown(
        """
        <script>
        document.getElementById("result").scrollIntoView({behavior: "smooth"});
        </script>
        """,
        unsafe_allow_html=True
    )

    # ---------- ÜBERSCHRIFT ----------
    st.markdown("## ❄️ Ergebnis der Schneevorhersage")

    # ---------- ERGEBNIS-BOX ----------
    if will_snow:
        st.markdown(
            f"""
            <div style="
                background:#e8f3ff;
                border-radius:20px;
                padding:1.5rem;
                margin-top:1rem;
                text-align:center;
                font-size:1.25rem;
                font-weight:700;
            ">
            ❄️ <strong>Ja, es wird schneien!</strong><br>
            Erwartete Schneemenge: <strong>{total_snow_cm:.2f} cm</strong>
            </div>
            """,
            unsafe_allow_html=True
        )

        st.dataframe(
            snow_hours[["time", "snowfall_cm", "temp_c"]],
            use_container_width=True
        )

    else:
        st.markdown(
            """
            <div style="
                background:#fff3e0;
                border-radius:20px;
                padding:1.5rem;
                margin-top:1rem;
                text-align:center;
                font-size:1.25rem;
                font-weight:700;
            ">
            🌧️ <strong>Kein Schneefall</strong><br>
            Laut Vorhersage schneit es in diesem Zeitraum nicht.
            </div>
            """,
            unsafe_allow_html=True
        )

    # ---------- DETAILS ----------
    st.caption("Hinweis: Vorhersagen werden unsicherer, je weiter sie in der Zukunft liegen.")
    st.dataframe(
        window[["time", "snowfall_cm", "temp_c", "precip_mm"]],
        use_container_width=True
    )

    # ---------- ZURÜCK-ZUR-KARTE BUTTON ----------
    st.markdown(
        """
        <div style="text-align:center; margin-top:2rem;">
            <a href="#top" style="
                display:inline-block;
                background:#1f77ff;
                color:white;
                padding:0.7rem 1.6rem;
                border-radius:14px;
                font-weight:700;
                text-decoration:none;
                font-size:1rem;
            ">
            ⬆️ Zurück zur Karte
            </a>
        </div>
        """,
        unsafe_allow_html=True
    )
