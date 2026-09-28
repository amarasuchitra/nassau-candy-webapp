"""
Centralized constants for Nassau Candy Factory Reallocation project.
Single source of truth for all magic numbers, coordinates, and configuration.
"""
import os

# ---------------------------------------------------------------------------
# File paths
# ---------------------------------------------------------------------------
_HERE = os.path.dirname(os.path.abspath(__file__))
RAW_DATA_PATH = os.path.join(_HERE, "..", "data", "Nassau_Candy_Distributor.csv")
OUTPUT_DIR = os.path.join(_HERE, "..", "outputs")

# ---------------------------------------------------------------------------
# Factory coordinates (lat, lon)
# ---------------------------------------------------------------------------
FACTORY_COORDS = {
    "Lot's O' Nuts":      (32.881893, -111.768036),
    "Wicked Choccy's":    (32.076176, -81.088371),
    "Sugar Shack":        (48.11914,  -96.18115),
    "Secret Factory":     (41.446333, -90.565487),
    "The Other Factory":  (35.1175,   -89.971107),
}

FACTORIES = list(FACTORY_COORDS.keys())

# ---------------------------------------------------------------------------
# Region coordinates (lat, lon) — approximate centroids for route map
# ---------------------------------------------------------------------------
REGION_COORDS = {
    "Atlantic": [41.6932, -76.4266],
    "Gulf":     [33.5739, -83.0493],
    "Interior": [37.0473, -92.9007],
    "Pacific":  [38.6479, -118.3112],
}

REGIONS = list(REGION_COORDS.keys())

# ---------------------------------------------------------------------------
# Product → Factory mapping (current assignment)
# ---------------------------------------------------------------------------
PRODUCT_TO_FACTORY = {
    "Wonka Bar - Nutty Crunch Surprise": "Lot's O' Nuts",
    "Wonka Bar - Fudge Mallows":         "Lot's O' Nuts",
    "Wonka Bar -Scrumdiddlyumptious":    "Lot's O' Nuts",
    "Wonka Bar - Milk Chocolate":        "Wicked Choccy's",
    "Wonka Bar - Triple Dazzle Caramel": "Wicked Choccy's",
    "Laffy Taffy":                       "Sugar Shack",
    "SweeTARTS":                         "Sugar Shack",
    "Nerds":                             "Sugar Shack",
    "Fun Dip":                           "Sugar Shack",
    "Fizzy Lifting Drinks":              "Sugar Shack",
    "Everlasting Gobstopper":            "Secret Factory",
    "Lickable Wallpaper":                "Secret Factory",
    "Wonka Gum":                         "Secret Factory",
    "Hair Toffee":                       "The Other Factory",
    "Kazookles":                         "The Other Factory",
}

# ---------------------------------------------------------------------------
# State/Province centroids for shipping distance calculation
# ---------------------------------------------------------------------------
STATE_CENTROIDS = {
    "Alabama": (32.806671, -86.791130), "Alaska": (61.370716, -152.404419),
    "Arizona": (33.729759, -111.431221), "Arkansas": (34.969704, -92.373123),
    "California": (36.116203, -119.681564), "Colorado": (39.059811, -105.311104),
    "Connecticut": (41.597782, -72.755371), "Delaware": (39.318523, -75.507141),
    "District of Columbia": (38.897438, -77.026817), "Florida": (27.766279, -81.686783),
    "Georgia": (33.040619, -83.643074), "Idaho": (44.240459, -114.478828),
    "Illinois": (40.349457, -88.986137), "Indiana": (39.849426, -86.258278),
    "Iowa": (42.011539, -93.210526), "Kansas": (38.526600, -96.726486),
    "Kentucky": (37.668140, -84.670067), "Louisiana": (31.169546, -91.867805),
    "Maine": (44.693947, -69.381927), "Maryland": (39.063946, -76.802101),
    "Massachusetts": (42.230171, -71.530106), "Michigan": (43.326618, -84.536095),
    "Minnesota": (45.694454, -93.900192), "Mississippi": (32.741646, -89.678696),
    "Missouri": (38.456085, -92.288368), "Montana": (46.921925, -110.454353),
    "Nebraska": (41.125370, -98.268082), "Nevada": (38.313515, -117.055374),
    "New Hampshire": (43.452492, -71.563896), "New Jersey": (40.298904, -74.521011),
    "New Mexico": (34.840515, -106.248482), "New York": (42.165726, -74.948051),
    "North Carolina": (35.630066, -79.806419), "North Dakota": (47.528912, -99.784012),
    "Ohio": (40.388783, -82.764915), "Oklahoma": (35.565342, -96.928917),
    "Oregon": (44.572021, -122.070938), "Pennsylvania": (40.590752, -77.209755),
    "Rhode Island": (41.680893, -71.511780), "South Carolina": (33.856892, -80.945007),
    "South Dakota": (44.299782, -99.438828), "Tennessee": (35.747845, -86.692345),
    "Texas": (31.054487, -97.563461), "Utah": (40.150032, -111.862434),
    "Vermont": (44.045876, -72.710686), "Virginia": (37.769337, -78.169968),
    "Washington": (47.400902, -121.490494), "West Virginia": (38.491226, -80.954453),
    "Wisconsin": (44.268543, -89.616508), "Wyoming": (42.755966, -107.302490),
    # Canadian provinces (approximate)
    "Alberta": (53.933271, -116.576504), "British Columbia": (53.726669, -127.647621),
    "Manitoba": (53.760860, -98.813873), "New Brunswick": (46.565314, -66.461914),
    "Newfoundland and Labrador": (53.135509, -57.660435), "Nova Scotia": (44.681999, -63.744311),
    "Ontario": (51.253775, -85.323214), "Prince Edward Island": (46.510712, -63.416687),
    "Quebec": (52.939916, -73.549136), "Saskatchewan": (52.935397, -106.450864),
}

# ---------------------------------------------------------------------------
# Modeling & Simulation Parameters (tunable)
# ---------------------------------------------------------------------------
# Shipping cost proxy: dollars per mile per unit
SHIP_COST_PER_MILE_PER_UNIT = 0.001

# Average ground transit speed for lead-time estimation (miles per day)
AVG_TRANSIT_SPEED_MILES_PER_DAY = 500.0

# Road factor: real driving distance ≈ straight-line × ROAD_FACTOR
ROAD_FACTOR = 1.19

# Ship mode base transit days (before distance)
SHIP_MODE_BASE_DAYS = {
    "Same Day": 0.5,
    "First Class": 1.5,
    "Second Class": 2.5,
    "Standard Class": 4.0,
}

# Division handling allowance (days)
DIVISION_HANDLING_DAYS = {
    "Chocolate": 0.4,
    "Sugar": 0.2,
    "Other": 0.3,
}

# Confidence scoring: log1p(orders) / log1p(CONFIDENCE_ORDER_CEILING)
CONFIDENCE_ORDER_CEILING = 500

# Lead-time proxy noise (for synthetic target generation)
LEAD_TIME_NOISE_STD = 0.3

# Minimum lead time floor (days)
MIN_LEAD_TIME_DAYS = 0.3

# Outlier clipping quantiles for lead time
LEAD_TIME_CLIP_QUANTILES = (0.01, 0.99)

# Model features
NUMERIC_FEATURES = ["shipping_distance_miles", "Units", "Sales"]
CATEGORICAL_FEATURES = ["Product Name", "Current Factory", "Region", "Ship Mode", "Division"]
TARGET = "est_lead_time_days"

# Train/test split
TEST_SIZE = 0.2
RANDOM_STATE = 42

# ---------------------------------------------------------------------------
# Factory colors (for consistent UI theming)
# ---------------------------------------------------------------------------
FACTORY_COLORS = {
    "Lot's O' Nuts":      '#1F4E8C',
    "Wicked Choccy's":    '#D91C6B',
    "Sugar Shack":        '#E8791F',
    "Secret Factory":     '#1B9E8F',
    "The Other Factory":  '#D93A2E',
}

# Network diagram positions (static SVG layout)
NET_FACTORY_POS = {
    "Lot's O' Nuts":     {'x': 150, 'y': 200},
    "Wicked Choccy's":   {'x': 660, 'y': 230},
    "Sugar Shack":       {'x': 430, 'y': 70},
    "Secret Factory":    {'x': 470, 'y': 150},
    "The Other Factory": {'x': 560, 'y': 190},
}

NET_REGION_POS = {
    "Pacific":  {'x': 60,  'y': 280},
    "Interior": {'x': 330, 'y': 290},
    "Gulf":     {'x': 520, 'y': 300},
    "Atlantic": {'x': 820, 'y': 270},
}

# Map projection bounds for route map SVG
MAP_BOUNDS = {
    'west': -125, 'east': -66,
    'north': 49, 'south': 24.5,
    'width': 860, 'height': 380,
    'pad_x': 36, 'pad_y': 30,
}

# Average ground speed for real-route time estimate (miles/day)
AVG_GROUND_SPEED_MPD = 500