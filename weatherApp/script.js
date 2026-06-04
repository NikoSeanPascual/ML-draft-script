updateWeatherEffects

//  GO TO https://openweathermap.org/api abd sign up to get your API key and replace this
const apiKey = "f37d5bb25dd2a510c04d31a694d8d329";
let tempChart = null;
let rainChart = null;
let windChart = null;
let favorites = JSON.parse(localStorage.getItem("weatherFavs")) || [];
let recents = JSON.parse(localStorage.getItem("weatherRecents")) || [];
let currentCity = "";
let defaultCity = localStorage.getItem("weatherDefaultCity") || "";

Chart.defaults.color = '#e2e8f0';
Chart.defaults.font.family = '"Jersey 10", cursive';

// ELEMENTS REGISTRY FOR SKELETON LOADING UI
const textElements = [
    "cityName", "temperature", "feelsLike", "description", "rainChance",
    "humidity", "wind", "pressure", "visibility", "uvIndex", "dewPoint",
    "aqi", "sunrise", "sunset"
];
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

// SKELETON TOGGLE SYSTEM
function toggleLoadingState(isLoading) {
    textElements.forEach(id => {
        const el = document.getElementById(id);
        if (el) {
            if (isLoading) {
                el.classList.add("skeleton");
                el.innerText = " "; // Retains spacing box height
            } else {
                el.classList.remove("skeleton");
            }
        }
    });
}

// THEME TOGGLE
function toggleTheme() {
    const body = document.body;
    const themeBtn = document.querySelector(".theme-switch");

    if (themeBtn) {
        themeBtn.classList.add("active");
        setTimeout(() => themeBtn.classList.remove("active"), 500);
    }

    body.classList.toggle("light-mode");

    const isLight = body.classList.contains("light-mode");
    const themeIcon = document.getElementById("theme-icon");
    if (themeIcon) themeIcon.innerText = isLight ? "☀️" : "🌙";

    const textColor = isLight ? '#1e293b' : '#e2e8f0';
    Chart.defaults.color = textColor;

    if (currentCity) {
        fetchWeatherByCity(currentCity);
    }

    localStorage.setItem("weatherTheme", isLight ? "light" : "dark");
}

// CLEAR LIST
function clearList(type) {
    if (confirm(`Are you sure you want to clear your ${type}?`)) {
        if (type === 'favorites') {
            favorites = [];
            localStorage.setItem("weatherFavs", JSON.stringify(favorites));
        } else {
            recents = [];
            localStorage.setItem("weatherRecents", JSON.stringify(recents));
        }
        renderListUI();
    }
}

// UPDATE WEATHER EFFECTS
function updateWeatherEffects(weatherMain, isDay) {
    const container = document.getElementById("weather-effects");
    if (!container) return;
    container.innerHTML = "";

    const createParticles = (type, count) => {
        for (let i = 0; i < count; i++) {
            let p = document.createElement("div");
            p.className = type;
            if (type === "rain") {
                p.style.left = (Math.random() * 120 - 10) + "%";
                p.style.height = (Math.random() * 15 + 10) + "px";
                p.style.animationDuration = (Math.random() * 0.4 + 0.4) + "s";
                p.style.animationDelay = (Math.random() * 2) + "s";
            } else if (type === "snow") {
                let size = Math.random() * 5 + 2;
                p.style.width = size + "px";
                p.style.height = size + "px";
                p.style.left = (Math.random() * 110 - 5) + "%";
                let fall = Math.random() * 3 + 3;
                p.style.animationDuration = `${fall}s, ${fall / 2}s`;
                p.style.animationDelay = `${Math.random() * 3}s, ${Math.random() * 2}s`;
                if (size < 4) { p.style.filter = "blur(2px)"; p.style.zIndex = "-1"; }
            }
            container.appendChild(p);
        }
    };

    if (weatherMain === "Thunderstorm") {
        createParticles("rain", 100);
    } else if (weatherMain === "Rain" || weatherMain === "Drizzle") {
        createParticles("rain", 60);
    } else if (weatherMain === "Snow") {
        createParticles("snow", 40);
    }
}

// UPDATE ATMOSPHERIC OVERLAYS
function updateAdvancedEffects(weatherMain, isDay) {
    const celestial = document.getElementById("celestial-body");
    const lightning = document.getElementById("lightning-overlay");
    const fog = document.getElementById("fog-overlay");

    if (!celestial) return;

    if (isDay) {
        celestial.className = "sun-active";
    } else {
        celestial.className = "moon-active";
    }

    if (weatherMain === "Thunderstorm") {
        lightning.classList.add("flash-active");
    } else {
        lightning.classList.remove("flash-active");
    }

    const fogConditions = ["Fog", "Mist", "Haze", "Smoke", "Dust", "Sand", "Ash"];
    if (fogConditions.includes(weatherMain)) {
        fog.classList.add("fog-active");
    } else {
        fog.classList.remove("fog-active");
    }

    updateWeatherEffects(weatherMain, isDay);
}

// DISPLAY WEATHER MAIN ENGINE
function displayWeather(data) {
    updateCityLists(data.name);

    const { lat, lon } = data.coord;
    const timezone = data.timezone;
    const temp = data.main.temp;
    const humidity = data.main.humidity;

    const isDay = data.dt >= data.sys.sunrise && data.dt < data.sys.sunset;

    const update = (id, text) => {
        const el = document.getElementById(id);
        if (el) el.innerText = text;
    };

    update("cityName", data.name);
    update("temperature", `Temp: ${temp.toFixed(1)}°C`);
    update("feelsLike", `Feels like: ${data.main.feels_like.toFixed(1)}°C`);
    update("description", `Condition: ${data.weather[0].description}`);

    getRainChance(data.name);

    update("humidity", `Humidity: ${humidity}%`);
    update("wind", `Wind: ${data.wind.speed} m/s ${getWindDirection(data.wind.deg)}`);
    update("pressure", `Pressure: ${data.main.pressure} hPa`);
    update("visibility", `Visibility: ${(data.visibility / 1000).toFixed(1)} km`);
    update("sunrise", `Sunrise: ${formatTime(data.sys.sunrise, timezone)}`);
    update("sunset", `Sunset: ${formatTime(data.sys.sunset, timezone)}`);
    update("dewPoint", `Dew Point: ${calculateDewPoint(temp, humidity).toFixed(1)}°C`);

    const iconElement = document.getElementById("weatherIcon");
    if (iconElement) {
        const iconCode = data.weather[0].icon;
        iconElement.src = `https://openweathermap.org/img/wn/${iconCode}@2x.png`;
        iconElement.style.display = "block";
    }

    getAQI(lat, lon);
    getUVIndex(lat, lon);

    changeBackground(temp, isDay);
    updateAdvancedEffects(data.weather[0].main, isDay);
    getForecastData(data.name);
    update("error", "");
}

//DISPLAY WEATHER
function displayWeather(data) {
    updateCityLists(data.name);

    const { lat, lon } = data.coord;
    const timezone = data.timezone;
    const temp = data.main.temp;
    const humidity = data.main.humidity;
    const isDay = data.dt >= data.sys.sunrise && data.dt < data.sys.sunset;

    const update = (id, text) => {
        const el = document.getElementById(id);
        if (el) el.innerText = text;
    };

    update("cityName", data.name);
    update("temperature", `Temp: ${temp.toFixed(1)}°C`);
    update("feelsLike", `Feels like: ${data.main.feels_like.toFixed(1)}°C`);
    update("description", `Condition: ${data.weather[0].description}`);

    getRainChance(data.name);

    update("humidity", `Humidity: ${humidity}%`);
    update("wind", `Wind: ${data.wind.speed} m/s ${getWindDirection(data.wind.deg)}`);
    update("pressure", `Pressure: ${data.main.pressure} hPa`);
    update("visibility", `Visibility: ${(data.visibility / 1000).toFixed(1)} km`);
    update("sunrise", `Sunrise: ${formatTime(data.sys.sunrise, timezone)}`);
    update("sunset", `Sunset: ${formatTime(data.sys.sunset, timezone)}`);
    update("dewPoint", `Dew Point: ${calculateDewPoint(temp, humidity).toFixed(1)}°C`);

    const iconElement = document.getElementById("weatherIcon");
    if (iconElement) {
        const iconCode = data.weather[0].icon;
        iconElement.src = `https://openweathermap.org/img/wn/${iconCode}@2x.png`;
        iconElement.style.display = "block";
    }

    getAQI(lat, lon);
    getUVIndex(lat, lon);

    changeBackground(temp, isDay);
    updateAdvancedEffects(data.weather[0].main, isDay);
    getForecastData(data.name);
    update("error", "");
}

// SHOW ERROR IF SOMETHING WENT WRONG
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

// BACKGROUND COLOR CHANGE
function changeBackground(temp, isDay) {
    let color, gradient;

    if (!isDay) {
        color = "#8b5cf6";
        gradient = "linear-gradient(135deg, #0f172a, #1e1b4b, #020617)";
    } else {
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
    }

    document.documentElement.style.setProperty('--accent-color', color);
    document.body.style.setProperty("--next-bg", gradient);
    document.body.classList.add("fade");

    setTimeout(() => {
        document.body.style.setProperty("--current-bg", gradient);
        document.body.classList.remove("fade");
    }, 1500);
}

function renderCharts(labels, temps, rainProbs, windSpeeds) {
    if (tempChart) tempChart.destroy();
    if (rainChart) rainChart.destroy();
    if (windChart) windChart.destroy();

    const commonOptions = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: {
            x: { grid: { color: 'rgba(255, 255, 255, 0.1)' } },
            y: { grid: { color: 'rgba(255, 255, 255, 0.1)' } }
        }
    };

    const canvasTemp = document.getElementById('tempChart');
    if (canvasTemp) {
        const ctxTemp = canvasTemp.getContext('2d');
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
    }

    const canvasRain = document.getElementById('rainChart');
    if (canvasRain) {
        const ctxRain = canvasRain.getContext('2d');
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
    }

    const canvasWind = document.getElementById('windChart');
    if (canvasWind) {
        const ctxWind = canvasWind.getContext('2d');
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
    }

    document.getElementById("chartsContainer").style.display = "block";
}

function getLocation() {
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(async (position) => {
            const { latitude, longitude } = position.coords;
            toggleLoadingState(true);
            try {
                const response = await fetch(`https://api.openweathermap.org/data/2.5/weather?lat=${latitude}&lon=${longitude}&units=metric&appid=${apiKey}`);
                const data = await response.json();
                displayWeather(data);
            } catch (e) {
                showError("Location access denied or failed");
            } finally {
                toggleLoadingState(false);
            }
        }, () => {
            showError("Please enable location permissions");
        });
    } else {
        showError("Geolocation not supported by browser");
    }
}

function updateCityLists(city) {
    currentCity = city;
    recents = [city, ...recents.filter(c => c !== city)].slice(0, 5);
    localStorage.setItem("weatherRecents", JSON.stringify(recents));

    const favBtn = document.getElementById("addFavorite");
    if (favBtn) favBtn.style.color = favorites.includes(city) ? "#facc15" : "#e2e8f0";

    renderListUI();
}

function toggleFavorite() {
    if (!currentCity) return;
    if (favorites.includes(currentCity)) {
        favorites = favorites.filter(c => c !== currentCity);
    } else {
        favorites.push(currentCity);
    }
    localStorage.setItem("weatherFavs", JSON.stringify(favorites));
    updateCityLists(currentCity);
}

function renderListUI() {
    const favContainer = document.getElementById("favoritesList");
    const recentContainer = document.getElementById("recentList");
    if (!favContainer || !recentContainer) return;

    const createChip = (city) => {
        const chip = document.createElement("div");
        chip.className = "city-chip";
        chip.innerText = city;
        chip.onclick = () => {
            document.getElementById("cityInput").value = city;
            getWeather();
        };
        return chip;
    };

    favContainer.innerHTML = "";
    favorites.forEach(city => favContainer.appendChild(createChip(city)));

    recentContainer.innerHTML = "";
    recents.forEach(city => recentContainer.appendChild(createChip(city)));

    attachCursorHoverEffects();
}

function setDefaultCity() {
    if (!currentCity) return;
    localStorage.setItem("weatherDefaultCity", currentCity);
    alert(`${currentCity} set as your home city!`);
}
const cursorDot = document.querySelector(".cursor-dot");
const cursorOutline = document.querySelector(".cursor-outline");

window.addEventListener("mousemove", (e) => {
    const posX = e.clientX;
    const posY = e.clientY;

    cursorDot.style.left = `${posX}px`;
    cursorDot.style.top = `${posY}px`;

    cursorOutline.animate({
        left: `${posX}px`,
        top: `${posY}px`
    }, { duration: 500, fill: "forwards" });
});

function attachCursorHoverEffects() {
    if (!cursorOutline) return;
    const interactables = document.querySelectorAll('button, input, .city-chip, .theme-switch, #addFavorite, #setDefault, .clear-btn');

    interactables.forEach(el => {
        el.addEventListener("mouseenter", () => cursorOutline.classList.add("cursor-hovered"));
        el.addEventListener("mouseleave", () => cursorOutline.classList.remove("cursor-hovered"));
    });
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

    toggleLoadingState(true);
    try {
        const response = await fetch(`https://api.openweathermap.org/data/2.5/weather?q=${city}&units=metric&appid=${apiKey}`);
        if (!response.ok) throw new Error("City not found");
        const data = await response.json();
        displayWeather(data);
    } catch (error) {
        showError(error.message);
    } finally {
        toggleLoadingState(false);
    }
}

async function getRainChance(city) {
    try {
        const response = await fetch(`https://api.openweathermap.org/data/2.5/forecast?q=${city}&units=metric&cnt=1&appid=${apiKey}`);
        const data = await response.json();

        const pop = data.list[0].pop * 100;
        const rainEl = document.getElementById("rainChance");

        if (rainEl) {
            rainEl.innerText = `Rain Chance: ${pop.toFixed(0)}%`;
            if (pop > 50) {
                rainEl.style.color = "var(--accent-color)";
                rainEl.style.fontWeight = "bold";
            } else {
                rainEl.style.color = "#94a3b8";
                rainEl.style.fontWeight = "normal";
            }
        }
    } catch (e) {
        const rainEl = document.getElementById("rainChance");
        if (rainEl) rainEl.innerText = "Rain Chance: N/A";
    }
}

async function getForecastData(city) {
    try {
        const response = await fetch(`https://api.openweathermap.org/data/2.5/forecast?q=${city}&units=metric&appid=${apiKey}`);
        const data = await response.json();

        const hourlyContainer = document.getElementById("hourlyForecast");
        const dailyContainer = document.getElementById("dailyForecast");

        if (!hourlyContainer || !dailyContainer) return;

        hourlyContainer.innerHTML = "";
        dailyContainer.innerHTML = "";

        const hourlyData = data.list.slice(0, 8);
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

        renderCharts(labels, temps, rainProbs, windSpeeds);

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

async function toggleComparison() {
    const section = document.getElementById("comparisonSection");
    const grid = document.getElementById("comparisonGrid");
    if (!section || !grid) return;

    if (section.style.display === "block") {
        section.style.display = "none";
        return;
    }

    if (favorites.length < 2) {
        alert("Add at least 2 favorites to compare!");
        return;
    }

    grid.innerHTML = "<p>Loading comparison...</p>";
    section.style.display = "block";

    try {
        const promises = favorites.map(city =>
            fetch(`https://api.openweathermap.org/data/2.5/weather?q=${city}&units=metric&appid=${apiKey}`).then(res => res.json())
        );

        const results = await Promise.all(promises);
        grid.innerHTML = "";

        results.forEach(data => {
            const card = document.createElement("div");
            card.className = "compare-card";
            card.innerHTML = `
                <h5>${data.name}</h5>
                <p class="comp-temp">${Math.round(data.main.temp)}°C</p>
                <p class="comp-desc">${data.weather[0].description}</p>
                <p style="font-size: 0.7rem; color: var(--accent-color)">H: ${data.main.humidity}%</p>
            `;
            grid.appendChild(card);
        });
        attachCursorHoverEffects();
    } catch (e) {
        grid.innerHTML = "<p>Error loading comparison.</p>";
    }
}

attachCursorHoverEffects();

// INITIALIZE APP
async function initApp() {
    renderListUI();
    if (localStorage.getItem("weatherTheme") === "light") toggleTheme();

    if (defaultCity) {
        fetchWeatherByCity(defaultCity);
    } else {
        getLocation();
    }
}

// HELPER TO FETCH WEATHER
async function fetchWeatherByCity(city) {
    toggleLoadingState(true);
    try {
        const response = await fetch(`https://api.openweathermap.org/data/2.5/weather?q=${city}&units=metric&appid=${apiKey}`);
        if (!response.ok) return;
        const data = await response.json();
        displayWeather(data);
    } catch (e) {
        console.error(e);
    } finally {
        toggleLoadingState(false);
    }
}
initApp();
