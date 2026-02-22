"""Dashboard widget backend.

Provides weather data, news feeds, and YouTube playlist configuration.
System metrics (CPU, memory, disk, network) are handled by Pytonium's
built-in SystemServices and pushed via the state bridge.
"""

import json
import urllib.request
import urllib.parse
import os
from datetime import datetime


class WidgetBackend:
    """Backend for the dashboard widget."""

    def __init__(self):
        self._weather_cache = None
        self._weather_last_fetch = 0
        self._news_cache = None
        self._news_last_fetch = 0

    # ─── Configuration ───

    def get_config(self, key):
        """Return a config value. Called from JS via Pytonium.callFunction."""
        config = {
            "youtube_playlist": "PLrAXtmErZgOeiKm4sgNOknGvNjby9efdf",
            "weather_location": "Königswinter,DE",
        }
        return config.get(key, None)

    # ─── Weather ───
    # Uses Open-Meteo (free, no API key needed)

    def fetch_weather(self):
        """Fetch current weather and 7-day forecast for Königswinter."""
        try:
            # Königswinter coordinates: 50.6833° N, 7.1833° E
            lat, lon = 50.6833, 7.1833
            url = (
                "https://api.open-meteo.com/v1/forecast?"
                f"latitude={lat}&longitude={lon}"
                "&current=temperature_2m,relative_humidity_2m,apparent_temperature,"
                "weather_code,wind_speed_10m,surface_pressure"
                "&daily=weather_code,temperature_2m_max,temperature_2m_min"
                "&timezone=Europe/Berlin"
                "&forecast_days=7"
            )

            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode())

            current = data.get("current", {})
            daily = data.get("daily", {})

            # Map WMO weather codes to descriptions
            wmo_codes = {
                0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy",
                3: "Overcast", 45: "Fog", 48: "Rime fog",
                51: "Light drizzle", 53: "Drizzle", 55: "Dense drizzle",
                61: "Light rain", 63: "Rain", 65: "Heavy rain",
                71: "Light snow", 73: "Snow", 75: "Heavy snow",
                80: "Rain showers", 81: "Rain showers", 82: "Heavy showers",
                85: "Snow showers", 86: "Heavy snow showers",
                95: "Thunderstorm", 96: "Thunderstorm w/ hail",
                99: "Thunderstorm w/ heavy hail"
            }

            code = current.get("weather_code", 0)
            day_names = []
            for d in daily.get("time", []):
                dt = datetime.strptime(d, "%Y-%m-%d")
                day_names.append(dt.strftime("%a"))

            forecast = []
            for i in range(min(7, len(daily.get("time", [])))):
                fc = daily.get("weather_code", [0])[i] if i < len(daily.get("weather_code", [])) else 0
                forecast.append({
                    "name": day_names[i] if i < len(day_names) else "?",
                    "desc": wmo_codes.get(fc, "Unknown"),
                    "high": daily.get("temperature_2m_max", [0])[i] if i < len(daily.get("temperature_2m_max", [])) else 0,
                    "low": daily.get("temperature_2m_min", [0])[i] if i < len(daily.get("temperature_2m_min", [])) else 0,
                })

            result = {
                "temp": current.get("temperature_2m", 0),
                "feels_like": current.get("apparent_temperature", 0),
                "description": wmo_codes.get(code, "Unknown"),
                "humidity": current.get("relative_humidity_2m", 0),
                "wind": current.get("wind_speed_10m", 0),
                "pressure": current.get("surface_pressure", 0),
                "forecast": forecast,
            }

            self._weather_cache = result
            return json.dumps(result)

        except Exception as e:
            if self._weather_cache:
                return json.dumps(self._weather_cache)
            return json.dumps({"temp": 0, "description": "Error: " + str(e)})

    # ─── News ───
    # Uses a simple RSS approach — can be extended

    def fetch_news(self):
        """Fetch tech/science news headlines.

        Uses a lightweight approach. For production, integrate with
        a proper news API or RSS parser.
        """
        # Placeholder structure — in real use, parse RSS feeds or
        # call a news API. This returns the cached/example data.
        # You can integrate:
        #   - feedparser for RSS (pip install feedparser)
        #   - NewsAPI (https://newsapi.org) with free tier
        #   - Hacker News API (no key needed)
        try:
            # Hacker News top stories (free, no API key)
            url = "https://hacker-news.firebaseio.com/v0/topstories.json"
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=10) as resp:
                story_ids = json.loads(resp.read().decode())[:8]

            articles = []
            for sid in story_ids:
                story_url = f"https://hacker-news.firebaseio.com/v0/item/{sid}.json"
                req = urllib.request.Request(story_url)
                with urllib.request.urlopen(req, timeout=5) as resp:
                    story = json.loads(resp.read().decode())
                    if story and story.get("title"):
                        # Guess category from title keywords
                        title = story["title"]
                        cat = "tech"
                        lower = title.lower()
                        if any(w in lower for w in ["study", "research", "brain", "quantum", "physics", "biology"]):
                            cat = "science"
                        elif any(w in lower for w in ["eu", "government", "law", "policy", "war", "election"]):
                            cat = "world"
                        elif any(w in lower for w in ["art", "music", "book", "film", "culture"]):
                            cat = "culture"

                        articles.append({
                            "category": cat,
                            "title": title,
                            "source": story.get("by", "HN"),
                            "url": story.get("url", ""),
                            "time": str(story.get("score", 0)) + " pts",
                        })

            self._news_cache = articles
            return json.dumps(articles)

        except Exception as e:
            if self._news_cache:
                return json.dumps(self._news_cache)
            return json.dumps([{"category": "tech", "title": "Error fetching news: " + str(e), "source": "System"}])

    # ─── System Extras ───

    def get_hostname(self):
        """Return the machine hostname."""
        return os.environ.get("COMPUTERNAME", "unknown")

    def get_username(self):
        """Return the current username."""
        return os.environ.get("USERNAME", os.environ.get("USER", "unknown"))
