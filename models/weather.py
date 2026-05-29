from pydantic import BaseModel


class WeatherData(BaseModel):
    temp: int
    humidity: int
    wind: int
    precipitation: float
    cloud_cover: int
    weather_code: int
