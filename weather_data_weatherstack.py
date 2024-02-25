import requests
import os

# Load API key from environment variable
api_key = os.getenv('WEATHER_API_KEY')

def get_current_weather(query):
    base_url = "http://api.weatherstack.com/current"
    params = {
        'access_key': api_key,
        'query': query
    }
    response = requests.get(base_url, params=params)
    
    if response.status_code == 200:
        return response.json()
    else:
        return response.status_code, response.text


# Example usage, only run when the script is executed directly
if __name__ == "__main__":
    query = 'New York'  # Replace with your desired location
    weather_data = get_current_weather(query)
    print(weather_data)
