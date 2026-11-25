"""The places analysed: where each InsideAirbnb snapshot lives and when it was downloaded.

London and Paris are the two cities of the main analysis. The others are the extension behind the app.
"""
BASE = "https://data.insideairbnb.com"
MAIN = ["London", "Paris"]

# name: (InsideAirbnb path, country, longitude, latitude, currency, in Sengupta et al. 2021)
CITIES = {
    "London":            ("united-kingdom/england/london/2026-09-17", "United Kingdom", -0.12, 51.51, "GBP", False),
    "Paris":             ("france/ile-de-france/paris/2026-09-16", "France", 2.35, 48.86, "EUR", False),
    "Dublin":            ("ireland/leinster/dublin/2026-09-17", "Ireland", -6.26, 53.35, "EUR", True),
    "Rest of Ireland":   ("ireland/2026-09-17", "Ireland", -8.2, 53.2, "EUR", False),
    "Amsterdam":         ("the-netherlands/north-holland/amsterdam/2026-09-16", "Netherlands", 4.90, 52.37, "EUR", True),
    "Athens":            ("greece/attica/athens/2026-09-22", "Greece", 23.73, 37.98, "EUR", True),
    "Barcelona":         ("spain/catalonia/barcelona/2026-09-17", "Spain", 2.17, 41.39, "EUR", True),
    "Copenhagen":        ("denmark/hovedstaden/copenhagen/2026-09-25", "Denmark", 12.57, 55.68, "DKK", True),
    "Geneva":            ("switzerland/geneva/geneva/2026-09-23", "Switzerland", 6.14, 46.20, "CHF", True),
    "Melbourne":         ("australia/vic/melbourne/2026-09-16", "Australia", 144.96, -37.81, "AUD", True),
    "Sydney":            ("australia/nsw/sydney/2026-09-16", "Australia", 151.21, -33.87, "AUD", True),
    "Tasmania":          ("australia/tas/tasmania/2026-09-16", "Australia", 146.8, -42.0, "AUD", True),
    "Western Australia": ("australia/wa/western-australia/2026-09-21", "Australia", 115.86, -31.95, "AUD", True),
    "Hong Kong":         ("china/hk/hong-kong/2026-09-20", "China", 114.17, 22.32, "HKD", True),
    "Tokyo":             ("japan/kantō/tokyo/2026-09-25", "Japan", 139.69, 35.69, "JPY", True),
    "Austin":            ("united-states/tx/austin/2026-09-17", "United States", -97.74, 30.27, "USD", True),
    "Boston":            ("united-states/ma/boston/2026-09-19", "United States", -71.06, 42.36, "USD", True),
    "Chicago":           ("united-states/il/chicago/2026-09-19", "United States", -87.63, 41.88, "USD", True),
    "Hawaii":            ("united-states/hi/hawaii/2026-09-17", "United States", -157.86, 21.31, "USD", True),
    "New York City":     ("united-states/ny/new-york-city/2026-09-14", "United States", -74.01, 40.71, "USD", True),
    "Seattle":           ("united-states/wa/seattle/2026-09-20", "United States", -122.33, 47.61, "USD", True),
    "Mexico City":       ("mexico/df/mexico-city/2026-09-23", "Mexico", -99.13, 19.43, "MXN", False),
}

# Rest of Ireland is the all-Ireland file with Dublin's listings removed
DERIVED = {"Rest of Ireland": ("Ireland", "ireland/2026-09-17", "Dublin")}


def snapshot(city):
    return CITIES[city][0].rsplit("/", 1)[1]


def download_date(city):
    return "2026-10-17" if city in MAIN else "2026-11-25"
