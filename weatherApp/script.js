//  GO TO https://openweathermap.org/api abd sign up to get your API key and replace this
const apiKey = "f37d5bb25dd2a510c04d31a694d8d329";
let tempChart = null;
let rainChart = null;
let windChart = null;

// Configure Chart.js default text color to match your app
Chart.defaults.color = '#e2e8f0';
Chart.defaults.font.family = '"Jersey 10", cursive';

// HELPER FUNCTIONS
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

    // TEXT UPDATES
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
        iconElement.src = `https://openweathermap.org/img/wn/${iconCode}@2x.png`;
        iconElement.style.display = "block";
    }

    getAQI(lat, lon);
    getUVIndex(lat, lon);
    changeBackground(temp);
    getForecastData(data.name);
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

    const forecast = document.getElementById("forecastContainer");
    if (forecast) forecast.style.display = "none";

    const charts = document.getElementById("chartsContainer");
    if (charts) charts.style.display = "none";
}

function changeBackground(temp) {
    let color, gradient;

    if (temp <= 10) {
        color = "#38bdf8";
        gradient = "linear-gradient(135deg, #0ea5e9, #1e3a8a)";
    } else if (temp <= 20) {
        color = "#4ade80";
        gradient = "linear-gradient(135deg, #22c55e, #065f46)";
    } else if (temp <= 30) {
        color = "#fbbf24";
        gradient = "linear-gradient(135deg, #f59e0b, #b45309)";
    } else {
        color = "#f87171";
        gradient = "linear-gradient(135deg, #ef4444, #7f1d1d)";
    }

    // UPDATE THE CSS VARIABLES FOR THE WHOLE UI
    document.documentElement.style.setProperty('--accent-color', color);
    document.body.style.setProperty("--next-bg", gradient);

    // TRIGGER THE FADE TRANSITION
    document.body.classList.add("fade");

    setTimeout(() => {
        document.styleSheets[0].addRule("body::before", `background: ${gradient}`);
        document.body.classList.remove("fade");
    }, 1500);
}

async function getForecastData(city) {
    try {
        const response = await fetch(`https://api.openweathermap.org/data/2.5/forecast?q=${city}&units=metric&appid=${apiKey}`);
        const data = await response.json();

        const hourlyContainer = document.getElementById("hourlyForecast");
        const dailyContainer = document.getElementById("dailyForecast");

        hourlyContainer.innerHTML = "";
        dailyContainer.innerHTML = "";

        // HOURLY FORECAST (Next 24 hours = next 8 items from the API)
        const hourlyData = data.list.slice(0, 8);

        // DATA FOR CHART
        const labels = [];
        const temps = [];
        const rainProbs = [];
        const windSpeeds = [];

        hourlyData.forEach(item => {
            const timeObj = new Date(item.dt * 1000);
            const timeString = timeObj.getHours().toString().padStart(2, '0') + ":00";
            const temp = Math.round(item.main.temp);
            const iconCode = item.weather[0].icon;

            labels.push(timeString);
            temps.push(temp);
            rainProbs.push(Math.round(item.pop * 100));
            windSpeeds.push(item.wind.speed);

            const card = document.createElement("div");
            card.className = "hourly-card";
            card.innerHTML = `
                <p>${timeString}</p>
                <img src="https://openweathermap.org/img/wn/${iconCode}.png" alt="icon">
                <p>${temp}°C</p>
            `;
            hourlyContainer.appendChild(card);
        });
        // CHARTS TRIGGER
        renderCharts(labels, temps, rainProbs, windSpeeds);
        // 5-DAY OVERVIEW
        const dailyData = data.list.filter(item => item.dt_txt.includes("12:00:00"));

        dailyData.forEach(item => {
            const dateObj = new Date(item.dt * 1000);
            const dayName = dateObj.toLocaleDateString('en-US', { weekday: 'short' });
            const temp = Math.round(item.main.temp);
            const desc = item.weather[0].description;
            const iconCode = item.weather[0].icon;

            const card = document.createElement("div");
            card.className = "daily-card";
            card.innerHTML = `
                <p style="width: 50px;">${dayName}</p>
                <img src="https://openweathermap.org/img/wn/${iconCode}.png" alt="icon">
                <p style="flex-grow: 1; text-align: center; text-transform: capitalize; font-size: 1rem; color: #94a3b8;">${desc}</p>
                <p class="daily-temp-range">${temp}°C</p>
            `;
            dailyContainer.appendChild(card);
        });

        document.getElementById("forecastContainer").style.display = "block";

    } catch (e) {
        console.error("Forecast fetch failed", e);
    }
}

function renderCharts(labels, temps, rainProbs, windSpeeds) {
    if (tempChart) tempChart.destroy();
    if (rainChart) rainChart.destroy();
    if (windChart) windChart.destroy();

    const commonOptions = {
        responsive: true,
        plugins: { legend: { display: false } },
        scales: {
            x: { grid: { color: 'rgba(255, 255, 255, 0.1)' } },
            y: { grid: { color: 'rgba(255, 255, 255, 0.1)' } }
        }
    };

    // TEMPERATURE CHART
    const ctxTemp = document.getElementById('tempChart').getContext('2d');
    tempChart = new Chart(ctxTemp, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Temp (°C)',
                data: temps,
                borderColor: '#facc15',
                backgroundColor: 'rgba(250, 204, 21, 0.2)',
                borderWidth: 2,
                fill: true,
                tension: 0.4
            }]
        },
        options: { ...commonOptions, plugins: { title: { display: true, text: 'Temperature (°C)' } } }
    });

    // RAIN PROBABILITY CHART
    const ctxRain = document.getElementById('rainChart').getContext('2d');
    rainChart = new Chart(ctxRain, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Rain Chance (%)',
                data: rainProbs,
                backgroundColor: '#38bdf8',
                borderRadius: 4
            }]
        },
        options: {
            ...commonOptions,
            scales: { ...commonOptions.scales, y: { beginAtZero: true, max: 100, grid: { color: 'rgba(255, 255, 255, 0.1)' } } },
            plugins: { title: { display: true, text: 'Rain Probability (%)' } }
        }
    });

    // WIND SPEED CHART
    const ctxWind = document.getElementById('windChart').getContext('2d');
    windChart = new Chart(ctxWind, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Wind (m/s)',
                data: windSpeeds,
                borderColor: '#4ade80',
                backgroundColor: 'rgba(74, 222, 128, 0.2)',
                borderWidth: 2,
                fill: true,
                tension: 0.4
            }]
        },
        options: { ...commonOptions, plugins: { title: { display: true, text: 'Wind Speed (m/s)' } } }
    });

    document.getElementById("chartsContainer").style.display = "block";
}
