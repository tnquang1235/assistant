import requests
import pytz
from datetime import datetime

class WeatherModule:
    """
    Xử lý dữ liệu thời tiết.
    """
    CITIES = ["Ho Chi Minh City", "Can Tho"]

    def __init__(self, api_key, google_manager, sheet_name="weather", timezone="Asia/Ho_Chi_Minh"):
        self.api_key = api_key
        self.gs = google_manager
        self.sheet_name = sheet_name
        self.tz = pytz.timezone(timezone)

    def get_report(self):
        """Lấy thời tiết chi tiết và tạo bản tin thẩm mỹ cao."""
        print("🌤 Đang lấy dữ liệu thời tiết...")
        now = datetime.now(self.tz)
        timestamp = now.strftime("%Y-%m-%d %H:%M")
        
        report = f"🌤 <b>DỰ BÁO THỜI TIẾT</b>\nCập nhật: {timestamp}\n\n"
        report += "<pre>"
        
        rows = []
        for city in self.CITIES:
            try:
                url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={self.api_key}&units=metric"
                response = requests.get(url)
                data = response.json()
                
                if response.status_code != 200:
                    print(f"⚠️ Weather API Error ({city}): {data.get('message', 'Unknown error')}")
                    continue

                # Fetch 12 parameters
                temp = data["main"]["temp"]
                feels_like = data["main"]["feels_like"]
                temp_max = data["main"]["temp_max"]
                temp_min = data["main"]["temp_min"]
                humidity = data["main"]["humidity"]
                main_cond = data["weather"][0]["main"]
                desc = data["weather"][0]["description"]
                wind_speed = data["wind"]["speed"]
                wind_deg = data["wind"].get("deg", 0)
                clouds = data["clouds"]["all"]
                
                # Visual Formatting: Icons and optimized spacing
                city_map = {"Ho Chi Minh City": "HCMC", "Can Tho": "Cần Thơ"}
                display_city = city_map.get(city, city[:10])
                
                # Row design: City | Temp | Max/Min | Humidity | Desc
                # Icons: 🌡 (temp), 🔼 (max), 🔽 (min), 💧 (hum), ☁️ (clouds/desc)
                report += f"📍 {display_city:<8} 🌡 {temp:>4.1f}°C   🔼{temp_max:>2.0f} 🔽{temp_min:<2.0f}   💧{humidity:>2}%   ☁️ {desc:<10}\n\n"
                
                rows.append({
                    "timestamp": timestamp, 
                    "city": city, 
                    "main": main_cond,
                    "temp": temp,
                    "feels_like": feels_like,
                    "temp_max": temp_max,
                    "temp_min": temp_min,
                    "humidity": humidity,
                    "wind_speed": wind_speed,
                    "wind_deg": wind_deg,
                    "clouds": clouds,
                    "description": desc
                })
            except Exception as e:
                print(f"⚠️ Lỗi thời tiết {city}: {e}")

        report += "</pre>"

        if rows:
            self.gs.append_rows(self.sheet_name, rows)
            
        return report
