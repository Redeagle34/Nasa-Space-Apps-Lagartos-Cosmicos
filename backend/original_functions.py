# Original functions to be used when frontend, ML model and Snowflake are ready
'''
def get_data_from_snowflake(location):
    """Connects to Snowflake and fetches historical weather data for the ML model."""
    conn = snowflake.connector.connect(
        user=os.getenv("SNOWFLAKE_USER"),
        password=os.getenv("SNOWFLAKE_PASSWORD"),
        account=os.getenv("SNOWFLAKE_ACCOUNT"),
        warehouse="COMPUTE_WH",
        database="WEATHER_DATA",
        schema="PUBLIC"
    )
    try:
        cs = conn.cursor()
        query = f"SELECT TEMPERATURE_C, HUMIDITY_PERCENT, WIND_SPEED_KPH FROM HOURLY_RECORDS WHERE LOCATION_NAME = '{location}' ORDER BY RECORDED_AT DESC LIMIT 168;" # Get last 7 days of data
        cs.execute(query)
        # Assuming your model needs a list of tuples or a similar format
        return cs.fetchall()
    finally:
        cs.close()
        conn.close()

const API_BASE_URL = 'http://localhost:5000/api';
'''

# Instructions for restoring the original functionality:
# 1. Uncomment the imports at the top of app.py:
#    import snowflake.connector
#    import joblib
#
# 2. Uncomment the ML model loading:
#    ml_model = joblib.load('weather_model.pkl')
#
# 3. In the get_weather_prediction() function:
#    - Replace get_mock_weather_data() with get_data_from_snowflake()
#    - Replace get_mock_prediction() with ml_model.predict()
#    - Remove the mock functions