import geopandas as gpd
import streamlit as st
import folium
from streamlit_folium import folium_static
import requests
from datetime import datetime

# Configuración de la página
st.set_page_config(
    layout="centered",
)

# Estilos personalizados para el fondo púrpura más oscuro y los colores de texto
st.markdown(
    """
    <style>
    .stApp {
        background-color: #120012;  /* Púrpura más oscuro */
        color: white;  /* Texto en blanco */
        font-family: 'Helvetica', sans-serif;  /* Fuente característica */
    }
    .stButton>button {
        background-color: #4B0082;  /* Botón púrpura oscuro */
        color: white;
        font-family: 'Helvetica', sans-serif;
    }
    .stSelectbox label, .stNumberInput label {
        font-weight: bold;
        margin-bottom: 5px;
        color: white;
        font-family: 'Helvetica', sans-serif;
    }
    .block-container {
        padding-top: 20px;
    }
    .css-1lcbmhc {
        align-items: start;
    }
    .success-box {
        background-color: #7CFC00;  /* Fondo verde lima */
        color: black;
        padding: 10px;
        border-radius: 5px;
        font-family: 'Helvetica', sans-serif;
    }
    .error-box {
        background-color: #FF4500;  /* Fondo rojo anaranjado */
        color: white;
        padding: 10px;
        border-radius: 5px;
        font-family: 'Helvetica', sans-serif;
    }
    .custom-title {
        font-size: 36px;
        font-weight: bold;
        color: white;
        text-align: center;
        font-family: 'Helvetica', sans-serif;
        margin-top: 20px;  
    }
    .custom-subheader {
        font-size: 24px;
        color: white;
        text-align: center;
        font-family: 'Helvetica', sans-serif;
        margin-bottom: 20px;
    }
    .footer-text {
        font-size: 12px;  /* Tamaño de fuente menor */
        text-align: right;  /* Alineado a la derecha */
        margin-top: 50px;  /* Espacio adicional hacia abajo */
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Título y subtítulo utilizando HTML
st.markdown('<div class="custom-title">New York City Taxi Association</div>', unsafe_allow_html=True)
st.markdown('<div class="custom-subheader">Predicción de Propina según su viaje</div>', unsafe_allow_html=True)

# Cargar el shapefile de zonas
zone_shp = gpd.read_file('./taxi_zones/taxi_zones.shp')

# Extraer los nombres de las zonas
zones = zone_shp['zone'].unique()

# Obtener la hora actual
now = datetime.now()
current_weekday = now.weekday()
current_hour = now.hour
current_minute = now.minute

st.markdown("### Informacion del viaje")

# Crear la interfaz de usuario en Streamlit
origin_zone = st.selectbox("Zona de Origen", zones)
destination_zone = st.selectbox("Zona de Destino", zones)

# Filtrar los datos para las zonas seleccionadas
origin_geom = zone_shp[zone_shp['zone'] == origin_zone]
destination_geom = zone_shp[zone_shp['zone'] == destination_zone]

# Crear un mapa centrado en Nueva York
m = folium.Map(location=[40.7128, -74.0060], zoom_start=12)

# Definir estilos para los polígonos
origin_style = {
    'fillColor': '#00ff00',  # Verde
    'color': '#006400',  # Borde verde oscuro
    'weight': 4,  # Grosor del borde
    'fillOpacity': 0.5,  # Opacidad del relleno
    'dashArray': '5, 5',  # Líneas discontinuas
}

destination_style = {
    'fillColor': '#ff0000',  # Rojo
    'color': '#8B0000',  # Borde rojo oscuro
    'weight': 4,  # Grosor del borde
    'fillOpacity': 0.5,  # Opacidad del relleno
    'dashArray': '5, 5',  # Líneas discontinuas
}

# Añadir la zona de origen al mapa
if not origin_geom.empty:
    folium.GeoJson(origin_geom.geometry, style_function=lambda x: origin_style).add_to(m)
    folium.Marker(
        location=[origin_geom.geometry.centroid.y.values[0], origin_geom.geometry.centroid.x.values[0]],
        popup=f"Origen: {origin_zone}",
        icon=folium.Icon(color='green')
    ).add_to(m)

# Añadir la zona de destino al mapa
if not destination_geom.empty:
    folium.GeoJson(destination_geom.geometry, style_function=lambda x: destination_style).add_to(m)
    folium.Marker(
        location=[destination_geom.geometry.centroid.y.values[0], destination_geom.geometry.centroid.x.values[0]],
        popup=f"Destino: {destination_zone}",
        icon=folium.Icon(color='red')
    ).add_to(m)

# Dibujar la línea entre el origen y el destino
if not origin_geom.empty and not destination_geom.empty:
    folium.PolyLine(
        locations=[
            [origin_geom.geometry.centroid.y.values[0], origin_geom.geometry.centroid.x.values[0]],
            [destination_geom.geometry.centroid.y.values[0], destination_geom.geometry.centroid.x.values[0]]
        ],
        color='blue',
        weight=5,
        opacity=0.8
    ).add_to(m)

# Mostrar el mapa en Streamlit
folium_static(m)

# Layout 
col1, col2, col3 = st.columns([1, 1, 1])

with col1:
    pickup_weekday = st.selectbox(
        "Día de la Semana (Lunes a Domingo)",
        options=[0, 1, 2, 3, 4, 5, 6],
        format_func=lambda x: ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"][x],
        index=current_weekday
    )
    RatecodeID = st.number_input(
        "Código de Tarifa (1-7)", 
        min_value=1,
        max_value=7,
        step=1
    )
    
with col2:
    pickup_hour = st.selectbox(
        "Hora de Recogida (1-24 horas)", 
        options=list(range(24)),
        index=current_hour
    )
    confidence = st.selectbox(
        "Umbral de Confianza (0.1 a 1.0)", 
        options=[round(x * 0.1, 1) for x in range(0, 11)]
    )

with col3:
    pickup_minute = st.selectbox(
        "Minuto de Recogida", 
        options=list(range(60)),
        index=current_minute
    )

# Calcular si está en horas laborales (asumiendo que son de 9 AM a 6 PM, Lunes a Viernes)
work_hours = int(current_hour >= 9 and current_hour <= 18 and current_weekday < 5)

# Botón para predecir
if st.button("Predecir Propina"):
    # Obtener los IDs de las zonas de origen y destino seleccionadas
    PULocationID = int(zone_shp[zone_shp['zone'] == origin_zone]['LocationID'].values[0])
    DOLocationID = int(zone_shp[zone_shp['zone'] == destination_zone]['LocationID'].values[0])

    features = {
        "pickup_weekday": pickup_weekday,
        "pickup_hour": pickup_hour,
        "work_hours": work_hours,
        "pickup_minute": pickup_minute,
        "passenger_count": 1,  # Valor por defecto, se puede ajustar según necesidad
        "trip_distance": 0,  # Asumir que se calculará posteriormente
        "trip_time": 0,  # Asumir que se calculará posteriormente
        "trip_speed": 0,  # Asumir que se calculará posteriormente
        "PULocationID": PULocationID,
        "DOLocationID": DOLocationID,
        "RatecodeID": RatecodeID,
    }
   
    # Solicitud al backend
    response = requests.post(
        "https://nicolaslagosb--propinas-nyc-fastapi-app.modal.run/predict",  # URL de Modal
        json=features, 
        params={"confidence": confidence}
    )
      
    # Mostrar la respuesta
    if response.status_code == 200:
        prediction = response.json().get("predicted_class")
        if prediction == 1:
            st.markdown('<div class="success-box">Predicción: El pasajero dejará una propina ALTA</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="error-box">Predicción: El pasajero dejará una propina BAJA</div>', unsafe_allow_html=True)
    else:
        st.error(f"Error: {response.status_code}")
