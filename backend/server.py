# Import the required libraries
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from modal import App, Image, asgi_app, Secret
import joblib
import os
import numpy as np

# Set up the Modal deployment
web_app = FastAPI(title='API de Predicción de Propinas en NYC')
app = App("propinas-nyc")

model_path = os.path.abspath('./model/random_forest.joblib')
zones_shp_path = os.path.abspath('./taxi_zones/taxi_zones.shp')
zones_shx_path = os.path.abspath('./taxi_zones/taxi_zones.shx')
zones_dbf_path = os.path.abspath('./taxi_zones/taxi_zones.dbf')
zones_prj_path = os.path.abspath('./taxi_zones/taxi_zones.prj')
zones_sbn_path = os.path.abspath('./taxi_zones/taxi_zones.sbn')
zones_sbx_path = os.path.abspath('./taxi_zones/taxi_zones.sbx')
zones_shp_xml_path = os.path.abspath('./taxi_zones/taxi_zones.shp.xml')
zones_lookup_csv_path = os.path.abspath('./taxi_zones/taxi_zone_lookup.csv')


# Define the image for deployment, installing necessary libraries
image = (
    Image.debian_slim()
    .pip_install(
        "fastapi",
        "numpy", 
        "pydantic",
        "python-dotenv",
        "uvicorn", 
        "joblib",
        "scikit-learn",
        "folium",
        "streamlit_folium",
        "geopandas",
        "folium",
        "matplotlib",
        "mapclassify",
        "geopy",
    )
    .copy_local_file(
        model_path, '/model/random_forest.joblib'
    )
    .copy_local_file(
        zones_shp_path,
        '/taxi_zones/taxi_zones.shp'
    )
    .copy_local_file(
        zones_shx_path,
        '/taxi_zones/taxi_zones.shx'
    )
    .copy_local_file(
        zones_dbf_path,
        '/taxi_zones/taxi_zones.dbf'
    )
    .copy_local_file(
        zones_prj_path,
        '/taxi_zones/taxi_zones.prj'
    )
    .copy_local_file(
        zones_sbn_path,
        '/taxi_zones/taxi_zones.sbn'
    )
    .copy_local_file(
        zones_sbx_path,
        '/taxi_zones/taxi_zones.sbx'
    )
    .copy_local_file(
        zones_shp_xml_path,
        '/taxi_zones/taxi_zones.shp.xml'
    )
    .copy_local_file(
        zones_lookup_csv_path,
        '/taxi_zones/taxi_zone_lookup.csv'
    )

)

# Clase que representa el vector de características del viaje
class TripFeatures(BaseModel):
    pickup_weekday: float
    pickup_hour: float
    work_hours: float
    pickup_minute: float
    passenger_count: float
    trip_distance: float
    trip_time: float
    trip_speed: float
    PULocationID: float
    DOLocationID: float
    RatecodeID: float

# Definimos la función de predicción
def predict_taxi_trip(features_trip, confidence=0.5):
    # Cargar el modelo entrenado de Random Forest
    rfc = joblib.load("/model/random_forest.joblib")
    #
    pred_value = rfc.predict_proba(features_trip.reshape(1, -1))[0][1]
    return 1 if pred_value >= confidence else 0 # 1 si la propina es alta, 0 si no.


# Define a route that will respond to a GET request with a simple message
@web_app.get("/ping")
async def ping():
    return "pong"

@web_app.get("/")
async def read_root():
    return {"message": "Bienvenido a la API de Predicción de Propinas en NYC"}

# Endpoint para la predicción
@web_app.post("/predict")
async def prediction(features: TripFeatures, confidence: float = 0.5):
    # Convertir las características en un vector numpy
    features_trip = np.array([features.pickup_weekday, features.pickup_hour, features.work_hours, 
                              features.pickup_minute, features.passenger_count, features.trip_distance,
                              features.trip_time, features.trip_speed, features.PULocationID, 
                              features.DOLocationID, features.RatecodeID])

    # Realizar la predicción
    try:
        pred = predict_taxi_trip(features_trip, confidence)
        # Retornar la predicción
        return {'predicted_class': pred}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Set up the deployment details for the Modal platform
@app.function(image=image)
@asgi_app()
def fastapi_app():
    return web_app

# Deploy the application if this script is run directly
if __name__ == "__main__":
    app.deploy("webapp")
