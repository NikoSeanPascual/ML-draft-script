//  GO TO https://openweathermap.org/api abd sign up to get your API key and replace this
const apiKey = "f37d5bb25dd2a510c04d31a694d8d329";

// HELPER FUNCTIONS (Load these first)
function formatTime(unix, timezone) {
    const date = new Date((unix + timezone) * 1000);
    return date.getUTCHours().toString().padStart(2, '0') + ":" +
           date.getUTCMinutes().toString().padStart(2, '0');
}
// CALCULATION
function calculateDewPoint(temp, humidity) {
    const a = 17.27;
    const b = 237.7;
    const alpha = ((a * temp) / (b + temp)) + Math.log(humidity / 100.0);
    return (b * alpha) / (a - alpha);
}
// WIND DIRECTIONS
function getWindDirection(deg) {
    const directions = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'];
    return directions[Math.round(deg / 45) % 8];
}

// API CALLS
async function getAQI(lat, lon) {
    try {
        const response = await fetch(`https://api.openweathermap.org/data/2.5/air_pollution?lat=${lat}&lon=${lon}&appid=${apiKey}`);
        const data = await response.json();
        const aqi = data.list[0].main.aqi;
        const aqiLabels = ["", "Good", "Fair", "Moderate", "Poor", "Very Poor"];
        document.getElementById("aqi").innerText = `AQI: ${aqi} (${aqiLabels[aqi]})`;
    } catch (e) { document.getElementById("aqi").innerText = "AQI: N/A"; }
}
// UV INDEX
async function getUVIndex(lat, lon) {
    try {
        const response = await fetch(`https://api.openweathermap.org/data/2.5/uvi?lat=${lat}&lon=${lon}&appid=${apiKey}`);
        const data = await response.json();
        document.getElementById("uvIndex").innerText = `UV Index: ${data.value || 0}`;
    } catch (e) { document.getElementById("uvIndex").innerText = "UV Index: N/A"; }
}

// MAIN SEARCH FUNCTION
async function getWeather() {
    const city = document.getElementById("cityInput").value;
    if (!city) { showError("Enter a city name"); return; }

    try {
        const response = await fetch(`https://api.openweathermap.org/data/2.5/weather?q=${city}&units=metric&appid=${apiKey}`);
        if (!response.ok) throw new Error("City not found");
        const data = await response.json();
        displayWeather(data);
    } catch (error) {
        showError(error.message);
    }
}
async function getRainChance(city) {
    try {
        const response = await fetch(`https://api.openweathermap.org/data/2.5/forecast?q=${city}&units=metric&cnt=1&appid=${apiKey}`);
        const data = await response.json();
        const pop = data.list[0].pop * 100;
        document.getElementById("rainChance").innerText = `Rain Chance: ${pop.toFixed(0)}%`;
    } catch (e) {
        document.getElementById("rainChance").innerText = "Rain Chance: N/A";
    }
}
function displayWeather(data) {
    const { lat, lon } = data.coord;
    const timezone = data.timezone;
    const temp = data.main.temp;
    const humidity = data.main.humidity;

    const update = (id, text) => {
        const el = document.getElementById(id);
        if (el) el.innerText = text;
    };

    // Text Updates
    update("cityName", data.name);
    update("temperature", `Temp: ${temp.toFixed(1)}°C`);
    update("feelsLike", `Feels like: ${data.main.feels_like.toFixed(1)}°C`);
    update("description", `Condition: ${data.weather[0].description}`);

    // NEW: Fetch Rain Chance using the city name
    getRainChance(data.name);

    update("humidity", `Humidity: ${humidity}%`);
    update("wind", `Wind: ${data.wind.speed} m/s ${getWindDirection(data.wind.deg)}`);
    update("pressure", `Pressure: ${data.main.pressure} hPa`);
    update("visibility", `Visibility: ${(data.visibility / 1000).toFixed(1)} km`);
    update("sunrise", `Sunrise: ${formatTime(data.sys.sunrise, timezone)}`);
    update("sunset", `Sunset: ${formatTime(data.sys.sunset, timezone)}`);
    update("dewPoint", `Dew Point: ${calculateDewPoint(temp, humidity).toFixed(1)}°C`);

    // UPDATED ICON LOGIC: Using official API icons
    const iconElement = document.getElementById("weatherIcon");
    if (iconElement) {
        const iconCode = data.weather[0].icon;
        // This URL pulls the high-res (@2x) official icon
        iconElement.src = `https://openweathermap.org/img/wn/${iconCode}@2x.png`;
        iconElement.style.display = "block";
    }

    getAQI(lat, lon);
    getUVIndex(lat, lon);
    changeBackground(temp);
    update("error", "");
}

function showError(message) {
    const errorEl = document.getElementById("error");
    if (errorEl) errorEl.innerText = message;

    const idsToClear = [
        "cityName", "temperature", "feelsLike", "humidity", "wind",
        "pressure", "visibility", "uvIndex", "dewPoint", "aqi",
        "sunrise", "sunset", "description"
    ];

    idsToClear.forEach(id => {
        const el = document.getElementById(id);
        if (el) el.innerText = "";
    });
    const rain = document.getElementById("rainChance");
    if (rain) rain.innerText = "";
}

function changeBackground(temp) {
    const newGradient = temp <= 10 ? "linear-gradient(135deg, #0ea5e9, #1e3a8a)" :
                        temp <= 20 ? "linear-gradient(135deg, #22c55e, #065f46)" :
                        temp <= 30 ? "linear-gradient(135deg, #f59e0b, #b45309)" :
                        "linear-gradient(135deg, #ef4444, #7f1d1d)";

    document.body.style.setProperty("--next-bg", newGradient);
    document.styleSheets[0].addRule("body::after", `background: ${newGradient}`);
    document.body.classList.add("fade");
    setTimeout(() => {
        document.styleSheets[0].addRule("body::before", `background: ${newGradient}`);
        document.body.classList.remove("fade");
    }, 1500);
}
