# 🌦️ Weather App Website

A simple and visually dynamic weather application that allows users to search for real-time weather information by city. This app uses the OpenWeather API and features smooth background transitions based on temperature.

[**View Live Demo 👉**](https://nikos-weather-app.netlify.app/)
---

## 🚀 Features

- 🔍 Search weather by city name  
- 🌡️ Displays temperature in Celsius  
- ☁️ Shows weather description  
- ⚠️ Error handling for invalid input or city not found  
- 🎨 Dynamic background gradient based on temperature  
- ✨ Smooth animated transitions between background states  
- 🧠 Clean and beginner-friendly code structure  

---

## 🛠️ Technologies Used

- HTML5 – Structure of the app  
- CSS3 – Styling, animations, and gradients  
- JavaScript (Vanilla) – Logic and API handling  
- OpenWeather API – Weather data source  
- Google Fonts (Jersey 10) – Custom font styling  

---

## 📂 Project Structure
```text
calculator
│
|── Assets folder  # Images used in the project(currently empty)
├── index.html     # Main structure of the application
├── styles.css     # UI Styling and containers
└── script.js      # Core Logic
```
---

## ⚙️ How It Works

1. User enters a city name in the input field  
2. Clicks the **Search** button  
3. App fetches data from the OpenWeather API  
4. Displays:
   - City Name  
   - Temperature  
   - Weather Description  
5. Background updates based on temperature:
   - ❄️ Cold (≤10°C) → Blue gradient  
   - 🌿 Cool (≤20°C) → Green gradient  
   - ☀️ Warm (≤30°C) → Orange gradient  
   - 🔥 Hot (>30°C) → Red gradient  

---

## 🔑 API Setup

1. Go to: https://openweathermap.org/api  
2. Sign up and get your API key  
3. Replace the API key in `script.js`:

```javascript
const apiKey = "YOUR_API_KEY_HERE";
```

## 📌 Future Improvements

1. 🌦️ Core Weather Enhancements
    * Add feels like temperature ✅ FINISHED 04/30/26
    * Show humidity ✅ FINISHED 04/30/26
    * Show wind speed & direction ✅ FINISHED 04/30/26
    * Display pressure ✅ FINISHED 05/01/26
    * Add visibility ✅ FINISHED 05/01/26
    * Show UV index ✅ FINISHED 05/01/26
    * Add dew point ✅ FINISHED 05/03/26
    * Display sunrise & sunset times ✅ FINISHED 05/03/26
    * Add air quality index (AQI) ✅ FINISHED 05/03/26
    * Show chance of rain (%)\ ✅ FINISHED 05/03/26
    * Add weather icons (from API) ✅ FINISHED 05/03/26
2. 📊 Forecast Features
    * 5-day forecast ✅ FINISHED 05/05/26
    * Hourly forecast (next 24–48 hours) ✅ FINISHED 05/05/26
    * Weekly overview cards ✅ FINISHED 05/05/26
    * Expandable forecast sections ✅ FINISHED 05/05/26
    * Graphs (temperature over time) ✅ FINISHED 05/06/26
    * Rain probability chart ✅ FINISHED 05/06/26
    * Wind speed graph ✅ FINISHED 05/06/26
3. 📍 Detect user location (Geolocation API)
    * “Use my location” button ✅ FINISHED 05/07/26 
    * Save favorite cities ✅ FINISHED 05/07/26
    * Recently searched cities ✅ FINISHED 05/07/26
    * Default city on load  ✅ FINISHED 05/09/26
    * Multiple city comparison view ✅ FINISHED 05/09/26
4. 🎨 UI / UX Improvements 
    * Dark / Light mode toggle ✅ FINISHED 05/11/26
    * Animated weather effects (rain, snow, clouds)  ✅ FINISHED 05/11/26
    * Smooth loading skeleton UI
    * Weather-based icons and backgrounds
    * Responsive design improvements
    * Card-based layout redesign
    * Glassmorphism / neumorphism styles
    * Custom cursor or hover effects
5. 🌈 Advanced Visual Effects
    * Background changes based on:
    * Weather condition (rainy, sunny, cloudy)
    * Time of day (day/night)
    * Particle effects (rain, snow)
    * Lightning animation for storms\
    * Fog overlay for misty weather
    * Animated sun/moon
6. 🔔 Smart Features
    * Weather alerts (extreme conditions)
    * Daily weather notifications
    * “What should I wear?” suggestion
    * Travel weather checker
    * Weather-based reminders
    * Auto-refresh weather every X minutes
7. ⚙️ Customization
    * Switch between Celsius / Fahrenheit
    * Custom themes
    * Adjustable refresh rate
    * Toggle UI elements on/off
8. 🚀 Performance & Dev Improvements
    * Loading spinner / skeleton
    * Error retry system\
    * Debounce input search
    * API caching (localStorage)
    * Optimize DOM updates
    * Modular JS structure
9. 🧪 Fun / Creative Features
    * Weather sounds (rain, wind)
    * Easter eggs (secret animations)
    * Theme based on seasons
    * “Weather mood meter”
    * Animated mascot reacting to weather
