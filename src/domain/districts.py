"""
src/domain/districts.py
-----------------------
Complete Catalog of all 36 Districts of Maharashtra across 6 Administrative Divisions.
Includes Marathi names, geographic coordinates, dominant economic/emission profiles,
and division hierarchy.
"""

from typing import Dict, Any, List, Optional
import numpy as np

MAHARASHTRA_DISTRICTS: List[Dict[str, Any]] = [
    # ── 1. Pune Division (Western Maharashtra) ──────────────────────
    {
        "id": "MH_PUN",
        "name": "Pune",
        "name_mr": "पुणे",
        "name_hi": "पुणे",
        "division": "Pune Division",
        "region": "Western Maharashtra",
        "lat": 18.5204,
        "lon": 73.8567,
        "population_approx": 9429408,
        "emission_profile": "Automotive, IT corridors, heavy vehicular transit, valley inversion",
        "tier": 1,
        "has_cpcb": True
    },
    {
        "id": "MH_SAT",
        "name": "Satara",
        "name_mr": "सातारा",
        "name_hi": "सतारा",
        "division": "Pune Division",
        "region": "Western Maharashtra",
        "lat": 17.6805,
        "lon": 73.9937,
        "population_approx": 3003741,
        "emission_profile": "Western Ghats foothills, sugarcane agro-processing, highway transit",
        "tier": 3,
        "has_cpcb": False
    },
    {
        "id": "MH_SOL",
        "name": "Solapur",
        "name_mr": "सोलापूर",
        "name_hi": "सोलापुर",
        "division": "Pune Division",
        "region": "Western Maharashtra",
        "lat": 17.6599,
        "lon": 75.9064,
        "population_approx": 4317756,
        "emission_profile": "Textile spinning mills, power looms, dry arid dust, sugar factories",
        "tier": 2,
        "has_cpcb": True
    },
    {
        "id": "MH_KOL",
        "name": "Kolhapur",
        "name_mr": "कोल्हापूर",
        "name_hi": "कोल्हापुर",
        "division": "Pune Division",
        "region": "Western Maharashtra",
        "lat": 16.7050,
        "lon": 74.2433,
        "population_approx": 3876001,
        "emission_profile": "Foundry clusters, jaggery/sugar units, sugarcane trash burning",
        "tier": 2,
        "has_cpcb": True
    },
    {
        "id": "MH_SAN",
        "name": "Sangli",
        "name_mr": "सांगली",
        "name_hi": "सांगली",
        "division": "Pune Division",
        "region": "Western Maharashtra",
        "lat": 16.8524,
        "lon": 74.5815,
        "population_approx": 2822143,
        "emission_profile": "Turmeric trade hub, sugarcane processing, Krishna river basin agriculture",
        "tier": 3,
        "has_cpcb": False
    },

    # ── 2. Konkan Division (Coastal Belt & MMR) ─────────────────────
    {
        "id": "MH_MUM_CITY",
        "name": "Mumbai City",
        "name_mr": "मुंबई शहर",
        "name_hi": "मुंबई शहर",
        "division": "Konkan Division",
        "region": "Konkan",
        "lat": 18.9388,
        "lon": 72.8354,
        "population_approx": 3085411,
        "emission_profile": "Marine boundary layer, dense vehicular traffic, port maritime emissions",
        "tier": 1,
        "has_cpcb": True
    },
    {
        "id": "MH_MUM_SUB",
        "name": "Mumbai Suburban",
        "name_mr": "मुंबई उपनगर",
        "name_hi": "मुंबई उपनगर",
        "division": "Konkan Division",
        "region": "Konkan",
        "lat": 19.0760,
        "lon": 72.8777,
        "population_approx": 9356962,
        "emission_profile": "Hyper-dense urban canyons, Western/Eastern Express highways, construction",
        "tier": 1,
        "has_cpcb": True
    },
    {
        "id": "MH_THA",
        "name": "Thane",
        "name_mr": "ठाणे",
        "name_hi": "ठाणे",
        "division": "Konkan Division",
        "region": "Konkan",
        "lat": 19.2183,
        "lon": 72.9781,
        "population_approx": 8070032,
        "emission_profile": "Chemical manufacturing corridors (Trans-Thane Creek), logistics transit",
        "tier": 1,
        "has_cpcb": True
    },
    {
        "id": "MH_PAL",
        "name": "Palghar",
        "name_mr": "पालघर",
        "name_hi": "पालघर",
        "division": "Konkan Division",
        "region": "Konkan",
        "lat": 19.6967,
        "lon": 72.7699,
        "population_approx": 2990116,
        "emission_profile": "Tarapur MIDC industrial zone, power transmission, coastal tribal belt",
        "tier": 3,
        "has_cpcb": False
    },
    {
        "id": "MH_RAI",
        "name": "Raigad",
        "name_mr": "रायगड",
        "name_hi": "रायगढ़",
        "division": "Konkan Division",
        "region": "Konkan",
        "lat": 18.5158,
        "lon": 73.1822,
        "population_approx": 2634200,
        "emission_profile": "JNPT Port corridors, petrochemicals, coastal tourism, Western Ghats forests",
        "tier": 2,
        "has_cpcb": True
    },
    {
        "id": "MH_RAT",
        "name": "Ratnagiri",
        "name_mr": "रत्नागिरी",
        "name_hi": "रत्नागिरी",
        "division": "Konkan Division",
        "region": "Konkan",
        "lat": 16.9902,
        "lon": 73.3120,
        "population_approx": 1615064,
        "emission_profile": "Clean maritime airflow, Alphonso mango orchards, fish processing, thermal power",
        "tier": 3,
        "has_cpcb": False
    },
    {
        "id": "MH_SIN",
        "name": "Sindhudurg",
        "name_mr": "सिंधुदुर्ग",
        "name_hi": "सिंधुदुर्ग",
        "division": "Konkan Division",
        "region": "Konkan",
        "lat": 16.1165,
        "lon": 73.7147,
        "population_approx": 849651,
        "emission_profile": "Pristine coastal forests, low industrial activity, bio-clean baseline",
        "tier": 3,
        "has_cpcb": False
    },

    # ── 3. Nashik Division (North Maharashtra / Khandesh) ───────────
    {
        "id": "MH_NSK",
        "name": "Nashik",
        "name_mr": "नाशिक",
        "name_hi": "नासिक",
        "division": "Nashik Division",
        "region": "North Maharashtra",
        "lat": 19.9975,
        "lon": 73.7898,
        "population_approx": 6107187,
        "emission_profile": "Satpur/Ambad MIDC, Godavari river valley, agro-vineyards, winter chill inversions",
        "tier": 2,
        "has_cpcb": True
    },
    {
        "id": "MH_AHM",
        "name": "Ahmednagar",
        "name_mr": "अहिल्यानगर (अहमदनगर)",
        "name_hi": "अहमदनगर",
        "division": "Nashik Division",
        "region": "North Maharashtra",
        "lat": 19.0948,
        "lon": 74.7480,
        "population_approx": 4543159,
        "emission_profile": "Sugarcane cooperative belt, co-generation plants, central highway freight",
        "tier": 3,
        "has_cpcb": False
    },
    {
        "id": "MH_DHU",
        "name": "Dhule",
        "name_mr": "धुळे",
        "name_hi": "धुले",
        "division": "Nashik Division",
        "region": "Khandesh",
        "lat": 20.9042,
        "lon": 74.7749,
        "population_approx": 2050862,
        "emission_profile": "NH52/NH53 National Highway junction, textile processing, dry soil dust",
        "tier": 3,
        "has_cpcb": False
    },
    {
        "id": "MH_JAL",
        "name": "Jalgaon",
        "name_mr": "जळगाव",
        "name_hi": "जलगांव",
        "division": "Nashik Division",
        "region": "Khandesh",
        "lat": 21.0077,
        "lon": 75.5626,
        "population_approx": 4229917,
        "emission_profile": "Banana & cotton trade, pipe manufacturing, railway freight corridor",
        "tier": 3,
        "has_cpcb": True
    },
    {
        "id": "MH_NAN_KHD",
        "name": "Nandurbar",
        "name_mr": "नंदुरबार",
        "name_hi": "नंदुरबार",
        "division": "Nashik Division",
        "region": "Khandesh",
        "lat": 21.3735,
        "lon": 74.2415,
        "population_approx": 1648295,
        "emission_profile": "Satpura tribal forested belt, wind farm ridges, low anthropogenic emissions",
        "tier": 3,
        "has_cpcb": False
    },

    # ── 4. Chhatrapati Sambhajinagar Division (Marathwada) ───────────
    {
        "id": "MH_AUR",
        "name": "Chhatrapati Sambhajinagar",
        "name_mr": "छत्रपती संभाजीनगर (औरंगाबाद)",
        "name_hi": "छत्रपति संभाजीनगर",
        "division": "Chhatrapati Sambhajinagar Division",
        "region": "Marathwada",
        "lat": 19.8762,
        "lon": 75.3433,
        "population_approx": 3701282,
        "emission_profile": "Shendra/Waluj MIDC engineering & pharma, semi-arid continental winter inversions",
        "tier": 2,
        "has_cpcb": True
    },
    {
        "id": "MH_JAL_MRW",
        "name": "Jalna",
        "name_mr": "जालना",
        "name_hi": "जालना",
        "division": "Chhatrapati Sambhajinagar Division",
        "region": "Marathwada",
        "lat": 19.8410,
        "lon": 75.8864,
        "population_approx": 1959046,
        "emission_profile": "Steel re-rolling mills, seed processing capital of India, dry particulate dust",
        "tier": 3,
        "has_cpcb": False
    },
    {
        "id": "MH_PAR",
        "name": "Parbhani",
        "name_mr": "परभणी",
        "name_hi": "परभणी",
        "division": "Chhatrapati Sambhajinagar Division",
        "region": "Marathwada",
        "lat": 19.2608,
        "lon": 76.7748,
        "population_approx": 1836086,
        "emission_profile": "Cotton ginning, Godavari agrarian basin, low industrial density",
        "tier": 3,
        "has_cpcb": False
    },
    {
        "id": "MH_HIN",
        "name": "Hingoli",
        "name_mr": "हिंगोली",
        "name_hi": "हिंगोली",
        "division": "Chhatrapati Sambhajinagar Division",
        "region": "Marathwada",
        "lat": 19.7180,
        "lon": 77.1485,
        "population_approx": 1177345,
        "emission_profile": "LIGO-India site, predominantly agrarian, turmeric farming, bio-clean baseline",
        "tier": 3,
        "has_cpcb": False
    },
    {
        "id": "MH_NED",
        "name": "Nanded",
        "name_mr": "नांदेड",
        "name_hi": "नांदेड़",
        "division": "Chhatrapati Sambhajinagar Division",
        "region": "Marathwada",
        "lat": 19.1383,
        "lon": 77.3210,
        "population_approx": 3361292,
        "emission_profile": "Religious pilgrimage hub, agro-processing, river valley humidity",
        "tier": 2,
        "has_cpcb": False
    },
    {
        "id": "MH_BEE",
        "name": "Beed",
        "name_mr": "बीड",
        "name_hi": "बीड",
        "division": "Chhatrapati Sambhajinagar Division",
        "region": "Marathwada",
        "lat": 18.9891,
        "lon": 75.7601,
        "population_approx": 2585049,
        "emission_profile": "Seasonal sugarcane labor migration, cotton farming, arid heat waves",
        "tier": 3,
        "has_cpcb": False
    },
    {
        "id": "MH_LAT",
        "name": "Latur",
        "name_mr": "लातूर",
        "name_hi": "लातुर",
        "division": "Chhatrapati Sambhajinagar Division",
        "region": "Marathwada",
        "lat": 18.4088,
        "lon": 76.5604,
        "population_approx": 2455543,
        "emission_profile": "Soybean & pulse oil mills, educational hub, continental winter cooling",
        "tier": 3,
        "has_cpcb": False
    },
    {
        "id": "MH_DHA",
        "name": "Dharashiv",
        "name_mr": "धाराशिव (उस्मानाबाद)",
        "name_hi": "धाराशिव",
        "division": "Chhatrapati Sambhajinagar Division",
        "region": "Marathwada",
        "lat": 18.1856,
        "lon": 76.0416,
        "population_approx": 1657576,
        "emission_profile": "Wind power ridges, solar farms, drought-prone plateau, low industrial baseline",
        "tier": 3,
        "has_cpcb": False
    },

    # ── 5. Amravati Division (Western Vidarbha) ──────────────────────
    {
        "id": "MH_AMR",
        "name": "Amravati",
        "name_mr": "अमरावती",
        "name_hi": "अमरावती",
        "division": "Amravati Division",
        "region": "Vidarbha",
        "lat": 20.9374,
        "lon": 77.7796,
        "population_approx": 2888445,
        "emission_profile": "Textile processing park (Nandgaon Peth), cotton ginning, Satpura hills boundary",
        "tier": 2,
        "has_cpcb": True
    },
    {
        "id": "MH_AKL",
        "name": "Akola",
        "name_mr": "अकोला",
        "name_hi": "अकोला",
        "division": "Amravati Division",
        "region": "Vidarbha",
        "lat": 20.7002,
        "lon": 77.0082,
        "population_approx": 1813906,
        "emission_profile": "Cotton City of Vidarbha, oil mills, pulse processing, summer extreme heat",
        "tier": 3,
        "has_cpcb": True
    },
    {
        "id": "MH_YAV",
        "name": "Yavatmal",
        "name_mr": "यवतमाळ",
        "name_hi": "यवतमाल",
        "division": "Amravati Division",
        "region": "Vidarbha",
        "lat": 20.3888,
        "lon": 78.1204,
        "population_approx": 2772348,
        "emission_profile": "Agrarian cotton belt, teak forests, low industrial emissions",
        "tier": 3,
        "has_cpcb": False
    },
    {
        "id": "MH_BUL",
        "name": "Buldhana",
        "name_mr": "बुलढाणा",
        "name_hi": "बुलढाणा",
        "division": "Amravati Division",
        "region": "Vidarbha",
        "lat": 20.5292,
        "lon": 76.1843,
        "population_approx": 2586258,
        "emission_profile": "Lonar crater geological sanctuary, cotton farming, clean rural baseline",
        "tier": 3,
        "has_cpcb": False
    },
    {
        "id": "MH_WAS",
        "name": "Washim",
        "name_mr": "वाशीम",
        "name_hi": "वाशिम",
        "division": "Amravati Division",
        "region": "Vidarbha",
        "lat": 20.1110,
        "lon": 77.1342,
        "population_approx": 1197160,
        "emission_profile": "Soybean agrarian belt, minimal heavy industry, rural background",
        "tier": 3,
        "has_cpcb": False
    },

    # ── 6. Nagpur Division (Eastern Vidarbha & Mining Belt) ─────────
    {
        "id": "MH_NAG",
        "name": "Nagpur",
        "name_mr": "नागपूर",
        "name_hi": "नागपुर",
        "division": "Nagpur Division",
        "region": "Vidarbha",
        "lat": 21.1458,
        "lon": 79.0882,
        "population_approx": 4653570,
        "emission_profile": "Geographical Center of India, MIHAN logistics, Koradi/Khaparkheda thermal plants",
        "tier": 1,
        "has_cpcb": True
    },
    {
        "id": "MH_WAR",
        "name": "Wardha",
        "name_mr": "वर्धा",
        "name_hi": "वर्धा",
        "division": "Nagpur Division",
        "region": "Vidarbha",
        "lat": 20.7453,
        "lon": 78.6022,
        "population_approx": 1300774,
        "emission_profile": "Gandhian heritage center, steel industries at Deoli, cotton processing",
        "tier": 3,
        "has_cpcb": False
    },
    {
        "id": "MH_BHA",
        "name": "Bhandara",
        "name_mr": "भंडारा",
        "name_hi": "भंडारा",
        "division": "Nagpur Division",
        "region": "Vidarbha",
        "lat": 21.1714,
        "lon": 79.6548,
        "population_approx": 1200334,
        "emission_profile": "Brass city, ordnance factories, Wainganga river lakes & paddy agriculture",
        "tier": 3,
        "has_cpcb": False
    },
    {
        "id": "MH_GON",
        "name": "Gondia",
        "name_mr": "गोंदिया",
        "name_hi": "गोंदिया",
        "division": "Nagpur Division",
        "region": "Vidarbha",
        "lat": 21.4554,
        "lon": 80.1965,
        "population_approx": 1322507,
        "emission_profile": "Rice bowl of Maharashtra, Tiroda thermal power station, forested ecology",
        "tier": 3,
        "has_cpcb": False
    },
    {
        "id": "MH_CHA",
        "name": "Chandrapur",
        "name_mr": "चंद्रपूर",
        "name_hi": "चंद्रपुर",
        "division": "Nagpur Division",
        "region": "Vidarbha",
        "lat": 19.9615,
        "lon": 79.2961,
        "population_approx": 2204307,
        "emission_profile": "Coal mining (WCL), CSTPS Super Thermal Power Station, cement plants, high industrial SO2/NO2",
        "tier": 2,
        "has_cpcb": True
    },
    {
        "id": "MH_GAD",
        "name": "Gadchiroli",
        "name_mr": "गडचिरोली",
        "name_hi": "गडचिरोली",
        "division": "Nagpur Division",
        "region": "Vidarbha",
        "lat": 20.1849,
        "lon": 79.9948,
        "population_approx": 1072942,
        "emission_profile": "Dense teak & bamboo forests, Surjagarh iron ore mining, minimal urban vehicular footprint",
        "tier": 3,
        "has_cpcb": False
    }
]


def get_all_districts() -> List[Dict[str, Any]]:
    """Returns catalog of all 36 Maharashtra districts."""
    return MAHARASHTRA_DISTRICTS


def find_nearest_district(lat: float, lon: float) -> Dict[str, Any]:
    """Finds nearest district seat to query coordinates."""
    min_dist = float("inf")
    nearest = MAHARASHTRA_DISTRICTS[0]

    for d in MAHARASHTRA_DISTRICTS:
        d_lat = (lat - d["lat"]) * 111.0
        d_lon = (lon - d["lon"]) * (111.0 * np.cos(np.radians(lat)))
        dist = np.sqrt(d_lat**2 + d_lon**2)
        if dist < min_dist:
            min_dist = dist
            nearest = d

    res = dict(nearest)
    res["distance_to_center_km"] = round(float(min_dist), 2)
    return res


# ─────────────────────────────────────────────────────────────────────────────
# In-Between Cities, Talukas, Industrial Corridors & Highway Nodes
# ─────────────────────────────────────────────────────────────────────────────

MAHARASHTRA_IN_BETWEEN_TOWNS: List[Dict[str, Any]] = [
    # ── 1. Pune – Mumbai Expressway & Old Highway Belt ──────────────
    {"id": "MH_TWN_LON", "name": "Lonavala", "name_mr": "लोणावळा", "name_hi": "लोनावला", "district": "Pune", "division": "Pune Division", "region": "Western Maharashtra", "lat": 18.7557, "lon": 73.4091, "type": "corridor_node", "emission_profile": "Ghat transit, heavy weekend vehicular emissions, mountain valley trapping"},
    {"id": "MH_TWN_KHA", "name": "Khandala", "name_mr": "खंडाळा", "name_hi": "खंडाला", "district": "Pune", "division": "Pune Division", "region": "Western Maharashtra", "lat": 18.7625, "lon": 73.3762, "type": "corridor_node", "emission_profile": "Expressway ridge, heavy commercial diesel trucks"},
    {"id": "MH_TWN_TAL", "name": "Talegaon Dabhade", "name_mr": "तळेगाव दाभाडे", "name_hi": "तलेगांव दाभाड़े", "district": "Pune", "division": "Pune Division", "region": "Western Maharashtra", "lat": 18.7340, "lon": 73.6766, "type": "industrial_hub", "emission_profile": "Automobile MIDC, warehousing, transit logistics"},
    {"id": "MH_TWN_DEH", "name": "Dehu Road", "name_mr": "देहूरोड", "name_hi": "देहू रोड", "district": "Pune", "division": "Pune Division", "region": "Western Maharashtra", "lat": 18.7180, "lon": 73.7290, "type": "corridor_node", "emission_profile": "Defense depot, highway transit, cantonment"},
    {"id": "MH_TWN_PCMC", "name": "Pimpri-Chinchwad", "name_mr": "पिंपरी-चिंचवड", "name_hi": "पिंपरी-चिंचवड़", "district": "Pune", "division": "Pune Division", "region": "Western Maharashtra", "lat": 18.6277, "lon": 73.8009, "type": "industrial_hub", "emission_profile": "Major automotive & engineering hub (Tata Motors, Thermax), dense traffic"},
    {"id": "MH_TWN_KHO", "name": "Khopoli", "name_mr": "खोपोली", "name_hi": "खोपोली", "district": "Raigad", "division": "Konkan Division", "region": "Konkan", "lat": 18.7885, "lon": 73.3444, "type": "industrial_hub", "emission_profile": "Ghat base, chemical synthesis, steel mills, thermal inversion pocket"},
    {"id": "MH_TWN_KAR", "name": "Karjat", "name_mr": "कर्जत", "name_hi": "कर्जत", "district": "Raigad", "division": "Konkan Division", "region": "Konkan", "lat": 18.9102, "lon": 73.3283, "type": "corridor_node", "emission_profile": "Railway junction, foothills, residential expansion"},
    {"id": "MH_TWN_PAN", "name": "Panvel", "name_mr": "पनवेल", "name_hi": "पनवेल", "district": "Raigad", "division": "Konkan Division", "region": "Konkan", "lat": 18.9894, "lon": 73.1175, "type": "corridor_node", "emission_profile": "Navi Mumbai international airport zone, major highway interchange"},

    # ── 2. Pune – Solapur / Marathwada Corridor ─────────────────────
    {"id": "MH_TWN_DAU", "name": "Daund", "name_mr": "दौंड", "name_hi": "दौंड", "district": "Pune", "division": "Pune Division", "region": "Western Maharashtra", "lat": 18.4658, "lon": 74.5828, "type": "taluka_town", "emission_profile": "Central rail junction, Bhima river sugarcane mills, agro processing"},
    {"id": "MH_TWN_BAR", "name": "Baramati", "name_mr": "बारामती", "name_hi": "बारामती", "district": "Pune", "division": "Pune Division", "region": "Western Maharashtra", "lat": 18.1517, "lon": 74.5770, "type": "taluka_town", "emission_profile": "Agro-industrial powerhouse, sugar cooperatives, textile park, MIDC"},
    {"id": "MH_TWN_IND", "name": "Indapur", "name_mr": "इंदापूर", "name_hi": "इंदापुर", "district": "Pune", "division": "Pune Division", "region": "Western Maharashtra", "lat": 18.1189, "lon": 75.0264, "type": "taluka_town", "emission_profile": "Pune-Solapur NH65 freight corridor, sugarcane trash burning"},
    {"id": "MH_TWN_PHA", "name": "Phaltan", "name_mr": "फलटण", "name_hi": "फलटन", "district": "Satara", "division": "Pune Division", "region": "Western Maharashtra", "lat": 17.9867, "lon": 74.4332, "type": "taluka_town", "emission_profile": "Sugarcane agro-processing, dairy cooperatives (Govind), Cummins plant"},
    {"id": "MH_TWN_PAN2", "name": "Pandharpur", "name_mr": "पंढरपूर", "name_hi": "पंढरपुर", "district": "Solapur", "division": "Pune Division", "region": "Western Maharashtra", "lat": 17.6778, "lon": 75.3278, "type": "taluka_town", "emission_profile": "Pilgrimage hub, episodic massive crowds, agro sugar mills"},
    {"id": "MH_TWN_KUR", "name": "Kurduvadi", "name_mr": "कुर्डुवाडी", "name_hi": "कुर्डूवाडी", "district": "Solapur", "division": "Pune Division", "region": "Western Maharashtra", "lat": 18.0872, "lon": 75.4344, "type": "corridor_node", "emission_profile": "Railway crossing, dry semi-arid dust, agricultural transit"},

    # ── 3. Pune – Kolhapur – Sangli Corridor (NH48) ────────────────
    {"id": "MH_TWN_SHI", "name": "Shirwal", "name_mr": "शिरवळ", "name_hi": "शिरवल", "district": "Satara", "division": "Pune Division", "region": "Western Maharashtra", "lat": 18.1364, "lon": 73.9856, "type": "industrial_hub", "emission_profile": "NH48 MIDC manufacturing, godowns, highway freight"},
    {"id": "MH_TWN_WAI", "name": "Wai", "name_mr": "वाई", "name_hi": "वाई", "district": "Satara", "division": "Pune Division", "region": "Western Maharashtra", "lat": 17.9493, "lon": 73.8924, "type": "taluka_town", "emission_profile": "Krishna river valley, turmeric processing, Ghat gateway"},
    {"id": "MH_TWN_MAH", "name": "Mahabaleshwar", "name_mr": "महाबळेश्वर", "name_hi": "महाबलेश्वर", "district": "Satara", "division": "Pune Division", "region": "Western Maharashtra", "lat": 17.9237, "lon": 73.6586, "type": "taluka_town", "emission_profile": "Pristine Western Ghats plateau (1350m elevation), tourist transit"},
    {"id": "MH_TWN_PCH", "name": "Panchgani", "name_mr": "पाचगणी", "name_hi": "पांचगणी", "district": "Satara", "division": "Pune Division", "region": "Western Maharashtra", "lat": 17.9237, "lon": 73.8016, "type": "taluka_town", "emission_profile": "Table land plateau, boarding schools, strawberry tourism"},
    {"id": "MH_TWN_KRD", "name": "Karad", "name_mr": "कराड", "name_hi": "कराड", "district": "Satara", "division": "Pune Division", "region": "Western Maharashtra", "lat": 17.2885, "lon": 74.1844, "type": "taluka_town", "emission_profile": "Koyna-Krishna confluence, agro-engineering, education hub"},
    {"id": "MH_TWN_ISL", "name": "Islampur", "name_mr": "इस्लामपूर", "name_hi": "इस्लामपुर", "district": "Sangli", "division": "Pune Division", "region": "Western Maharashtra", "lat": 17.0519, "lon": 74.2674, "type": "taluka_town", "emission_profile": "Rajarambapu sugar complex, milk processing, NH48 transit"},
    {"id": "MH_TWN_ICH", "name": "Ichalkaranji", "name_mr": "इचलकरंजी", "name_hi": "इचलकरंजी", "district": "Kolhapur", "division": "Pune Division", "region": "Western Maharashtra", "lat": 16.6980, "lon": 74.4578, "type": "industrial_hub", "emission_profile": "'Manchester of Maharashtra', massive textile sizing/dyeing & powerlooms"},
    {"id": "MH_TWN_MIR", "name": "Miraj", "name_mr": "मिरज", "name_hi": "मिरज", "district": "Sangli", "division": "Pune Division", "region": "Western Maharashtra", "lat": 16.8284, "lon": 74.6465, "type": "corridor_node", "emission_profile": "Major medical hub, railway junction, musical instrument crafting"},

    # ── 4. Nashik – Ahmednagar – Pune Corridor ─────────────────────
    {"id": "MH_TWN_SIN", "name": "Sinnar", "name_mr": "सिन्नर", "name_hi": "सिन्नर", "district": "Nashik", "division": "Nashik Division", "region": "North Maharashtra", "lat": 19.8458, "lon": 73.9961, "type": "industrial_hub", "emission_profile": "Sinnar SEZ, thermal power, engineering & pharma units"},
    {"id": "MH_TWN_SAN2", "name": "Sangamner", "name_mr": "संगमनेर", "name_hi": "संगमनेर", "district": "Ahilyanagar", "division": "Nashik Division", "region": "North Maharashtra", "lat": 19.5767, "lon": 74.2078, "type": "taluka_town", "emission_profile": "Pravara basin, cooperative milk and sugar factories, NH60 transit"},
    {"id": "MH_TWN_SHR", "name": "Shirdi", "name_mr": "शिर्डी", "name_hi": "शिरडी", "district": "Ahilyanagar", "division": "Nashik Division", "region": "North Maharashtra", "lat": 19.7667, "lon": 74.4764, "type": "taluka_town", "emission_profile": "World pilgrimage destination, airport, heavy tourist bus traffic"},
    {"id": "MH_TWN_KOP", "name": "Kopargaon", "name_mr": "कोपरगाव", "name_hi": "कोपरगांव", "district": "Ahilyanagar", "division": "Nashik Division", "region": "North Maharashtra", "lat": 19.8885, "lon": 74.4795, "type": "taluka_town", "emission_profile": "Godavari river agro processing, sugar & distillery emissions"},
    {"id": "MH_TWN_SRP", "name": "Shrirampur", "name_mr": "श्रीरामपूर", "name_hi": "श्रीरामपुर", "district": "Ahilyanagar", "division": "Nashik Division", "region": "North Maharashtra", "lat": 19.6175, "lon": 74.6567, "type": "taluka_town", "emission_profile": "Mosambi citrus market, sugar factories, railway transit"},
    {"id": "MH_TWN_RAH", "name": "Rahuri", "name_mr": "राहुरी", "name_hi": "राहुरी", "district": "Ahilyanagar", "division": "Nashik Division", "region": "North Maharashtra", "lat": 19.3900, "lon": 74.6500, "type": "taluka_town", "emission_profile": "Mahatma Phule Krishi Vidyapeeth (MPKV), Mula river agriculture"},
    {"id": "MH_TWN_MNC", "name": "Manchar", "name_mr": "मंचार", "name_hi": "मंचार", "district": "Pune", "division": "Pune Division", "region": "Western Maharashtra", "lat": 19.0069, "lon": 73.9406, "type": "taluka_town", "emission_profile": "Ghod river valley, onion/vegetable trade, NH60 transit"},
    {"id": "MH_TWN_JUN", "name": "Junnar", "name_mr": "जुन्नर", "name_hi": "जुन्नर", "district": "Pune", "division": "Pune Division", "region": "Western Maharashtra", "lat": 19.2069, "lon": 73.8767, "type": "taluka_town", "emission_profile": "Shivneri valley, horticulture, leopard habitat corridor"},
    {"id": "MH_TWN_CHK", "name": "Chakan", "name_mr": "चाकण", "name_hi": "चाकण", "district": "Pune", "division": "Pune Division", "region": "Western Maharashtra", "lat": 18.7597, "lon": 73.8584, "type": "industrial_hub", "emission_profile": "Global automotive manufacturing corridor (Bajaj, VW, Mercedes), heavy freight"},

    # ── 5. North Maharashtra / Khandesh Corridor ────────────────────
    {"id": "MH_TWN_MAL", "name": "Malegaon", "name_mr": "मालेगाव", "name_hi": "मालेगांव", "district": "Nashik", "division": "Nashik Division", "region": "North Maharashtra", "lat": 20.5539, "lon": 74.5298, "type": "industrial_hub", "emission_profile": "Major powerloom textile hub, plastic recycling, high local density"},
    {"id": "MH_TWN_MNM", "name": "Manmad", "name_mr": "मनमाड", "name_hi": "मनमाड", "district": "Nashik", "division": "Nashik Division", "region": "North Maharashtra", "lat": 20.2520, "lon": 74.4370, "type": "corridor_node", "emission_profile": "Central rail junction, BPCL/HPCL oil terminals, grain godowns"},
    {"id": "MH_TWN_YEO", "name": "Yeola", "name_mr": "येवला", "name_hi": "येवला", "district": "Nashik", "division": "Nashik Division", "region": "North Maharashtra", "lat": 20.0422, "lon": 74.4856, "type": "taluka_town", "emission_profile": "Paithani silk handloom weaving, onion trading, dry plains"},
    {"id": "MH_TWN_CHA2", "name": "Chalisgaon", "name_mr": "चाळीसगाव", "name_hi": "चालीसगांव", "district": "Jalgaon", "division": "Nashik Division", "region": "North Maharashtra", "lat": 20.4633, "lon": 75.0136, "type": "corridor_node", "emission_profile": "Rail junction, cotton trade, Girna river plains"},
    {"id": "MH_TWN_BHU", "name": "Bhusawal", "name_mr": "भुसावळ", "name_hi": "भुसावल", "district": "Jalgaon", "division": "Nashik Division", "region": "North Maharashtra", "lat": 21.0455, "lon": 75.7915, "type": "industrial_hub", "emission_profile": "Deepak TPS Thermal Power Station, ordnance factory, railway division"},
    {"id": "MH_TWN_AML", "name": "Amalner", "name_mr": "अमळनेर", "name_hi": "अमलनेर", "district": "Jalgaon", "division": "Nashik Division", "region": "North Maharashtra", "lat": 21.0442, "lon": 75.0594, "type": "taluka_town", "emission_profile": "Bori river, Wipro origin oil mills, educational institutes"},

    # ── 6. Marathwada Interior Corridors ───────────────────────────
    {"id": "MH_TWN_PAI", "name": "Paithan", "name_mr": "पैठण", "name_hi": "पैठन", "district": "Chhatrapati Sambhajinagar", "division": "Sambhajinagar Division", "region": "Marathwada", "lat": 19.4800, "lon": 75.3800, "type": "taluka_town", "emission_profile": "Jayakwadi dam reservoir, Paithani silk, Godavari riverside"},
    {"id": "MH_TWN_SEL", "name": "Selu", "name_mr": "सेलू", "name_hi": "सेलू", "district": "Parbhani", "division": "Sambhajinagar Division", "region": "Marathwada", "lat": 19.8000, "lon": 76.4500, "type": "taluka_town", "emission_profile": "Cotton ginning & pressing mills, agro-market"},
    {"id": "MH_TWN_BAS", "name": "Basmath", "name_mr": "वसमत", "name_hi": "वसमत", "district": "Hingoli", "division": "Sambhajinagar Division", "region": "Marathwada", "lat": 19.7000, "lon": 77.1600, "type": "taluka_town", "emission_profile": "Turmeric trade, sugarcane agro-processing"},
    {"id": "MH_TWN_PRL", "name": "Parli Vaijnath", "name_mr": "परळी वैजनाथ", "name_hi": "परली वैजनाथ", "district": "Beed", "division": "Sambhajinagar Division", "region": "Marathwada", "lat": 18.8500, "lon": 76.5300, "type": "industrial_hub", "emission_profile": "Parli Thermal Power Station (fly ash, SO2), Jyotirlinga pilgrimage"},
    {"id": "MH_TWN_AMB", "name": "Ambajogai", "name_mr": "अंबाजोगाई", "name_hi": "अंबाजोगाई", "district": "Beed", "division": "Sambhajinagar Division", "region": "Marathwada", "lat": 18.7300, "lon": 76.3800, "type": "taluka_town", "emission_profile": "Cultural & medical college hub, plateau microclimate"},
    {"id": "MH_TWN_UDG", "name": "Udgir", "name_mr": "उदगीर", "name_hi": "उदगीर", "district": "Latur", "division": "Sambhajinagar Division", "region": "Marathwada", "lat": 18.3900, "lon": 77.1100, "type": "taluka_town", "emission_profile": "Border trade hub, veterinary university, pulse mills"},
    {"id": "MH_TWN_TUL", "name": "Tuljapur", "name_mr": "तुळजापूर", "name_hi": "तुलजापुर", "district": "Dharashiv", "division": "Sambhajinagar Division", "region": "Marathwada", "lat": 18.0050, "lon": 76.0717, "type": "taluka_town", "emission_profile": "Historic temple town, hill ridge, heavy pilgrim vehicular transit"},

    # ── 7. Vidarbha Industrial & Agricultural Belt ─────────────────
    {"id": "MH_TWN_HNG", "name": "Hinganghat", "name_mr": "हिंगणघाट", "name_hi": "हिंगणघाट", "district": "Wardha", "division": "Nagpur Division", "region": "Vidarbha", "lat": 20.5600, "lon": 78.8400, "type": "industrial_hub", "emission_profile": "Major cotton spinning mills (Pee Vee Textiles), Wena river"},
    {"id": "MH_TWN_WAR2", "name": "Warora", "name_mr": "वरोरा", "name_hi": "वरोरा", "district": "Chandrapur", "division": "Nagpur Division", "region": "Vidarbha", "lat": 20.2300, "lon": 78.9900, "type": "corridor_node", "emission_profile": "Coal rail sidings, Anandwan leprosy rehabilitation, cement transit"},
    {"id": "MH_TWN_BHD", "name": "Bhadravati", "name_mr": "भद्रावती", "name_hi": "भद्रावती", "district": "Chandrapur", "division": "Nagpur Division", "region": "Vidarbha", "lat": 20.1000, "lon": 79.1200, "type": "industrial_hub", "emission_profile": "Open cast coal mines, defense ordnance factory, high dust load"},
    {"id": "MH_TWN_BAL", "name": "Ballarpur", "name_mr": "बल्लारपूर", "name_hi": "बल्लारपुर", "district": "Chandrapur", "division": "Nagpur Division", "region": "Vidarbha", "lat": 19.8500, "lon": 79.3500, "type": "industrial_hub", "emission_profile": "Ballarpur Paper Mills (BILT), WCL coal mining, timber market"},
    {"id": "MH_TWN_KMP", "name": "Kamptee", "name_mr": "कामठी", "name_hi": "कामठी", "district": "Nagpur", "division": "Nagpur Division", "region": "Vidarbha", "lat": 21.2200, "lon": 79.2000, "type": "corridor_node", "emission_profile": "Military cantonment, Dragon Palace, Kanhan river coal corridor"},
    {"id": "MH_TWN_UMR", "name": "Umred", "name_mr": "उमरेड", "name_hi": "उमरेड", "district": "Nagpur", "division": "Nagpur Division", "region": "Vidarbha", "lat": 20.8500, "lon": 79.3300, "type": "taluka_town", "emission_profile": "WCL coal mines, major chili agricultural market"},
    {"id": "MH_TWN_KAT", "name": "Katol", "name_mr": "काटोल", "name_hi": "काटोल", "district": "Nagpur", "division": "Nagpur Division", "region": "Vidarbha", "lat": 21.2800, "lon": 78.5800, "type": "taluka_town", "emission_profile": "Citrus orange capital, food processing, Jam river"},
    {"id": "MH_TWN_RAM", "name": "Ramtek", "name_mr": "रामटेक", "name_hi": "रामटेक", "district": "Nagpur", "division": "Nagpur Division", "region": "Vidarbha", "lat": 21.4000, "lon": 79.3300, "type": "taluka_town", "emission_profile": "Kalidasa heritage, manganese mines, forest perimeter"},
    {"id": "MH_TWN_TUM", "name": "Tumsar", "name_mr": "तुमसर", "name_hi": "तुमसर", "district": "Bhandara", "division": "Nagpur Division", "region": "Vidarbha", "lat": 21.3800, "lon": 79.7400, "type": "taluka_town", "emission_profile": "'Rice city' agro mills, MOIL Dongri Buzurg manganese mines"},
    {"id": "MH_TWN_TIR", "name": "Tiroda", "name_mr": "तिरोडा", "name_hi": "तिरोड़ा", "district": "Gondia", "division": "Nagpur Division", "region": "Vidarbha", "lat": 21.4100, "lon": 79.9300, "type": "industrial_hub", "emission_profile": "Adani 3300MW Super Thermal Power Station, high point source SO2"},
    {"id": "MH_TWN_ACH", "name": "Achalpur", "name_mr": "अचलपूर", "name_hi": "अचलपुर", "district": "Amravati", "division": "Amravati Division", "region": "Vidarbha", "lat": 21.2600, "lon": 77.5100, "type": "taluka_town", "emission_profile": "Melghat forest foothills, cotton ginning, twin town Paratwada"},
    {"id": "MH_TWN_KHM", "name": "Khamgaon", "name_mr": "खामगाव", "name_hi": "खामगांव", "district": "Buldhana", "division": "Amravati Division", "region": "Vidarbha", "lat": 20.6900, "lon": 76.5700, "type": "industrial_hub", "emission_profile": "Cotton & silver trading hub, chemical & vanaspati oil MIDC"},
    {"id": "MH_TWN_SHE", "name": "Shegaon", "name_mr": "शेगाव", "name_hi": "शेगांव", "district": "Buldhana", "division": "Amravati Division", "region": "Vidarbha", "lat": 20.7900, "lon": 76.6900, "type": "taluka_town", "emission_profile": "Shri Gajanan Maharaj temple pilgrimage, Anand Sagar eco-park"},
    {"id": "MH_TWN_MLK", "name": "Malkapur", "name_mr": "मलकापूर", "name_hi": "मलकापुर", "district": "Buldhana", "division": "Amravati Division", "region": "Vidarbha", "lat": 20.8800, "lon": 76.2000, "type": "corridor_node", "emission_profile": "NH53 major freight junction, Nalganga river agricultural plain"},

    # ── 8. Konkan Highway & Coastal Belt ────────────────────────────
    {"id": "MH_TWN_PEN", "name": "Pen", "name_mr": "पेण", "name_hi": "पेण", "district": "Raigad", "division": "Konkan Division", "region": "Konkan", "lat": 18.7400, "lon": 73.0900, "type": "taluka_town", "emission_profile": "Bhogavati river, salt pans, Ganesh idol sculpture clusters"},
    {"id": "MH_TWN_ROH", "name": "Roha", "name_mr": "रोहा", "name_hi": "रोहा", "district": "Raigad", "division": "Konkan Division", "region": "Konkan", "lat": 18.4400, "lon": 73.1200, "type": "industrial_hub", "emission_profile": "Dhatav chemical MIDC zone, Kundalika river, paper & dyes"},
    {"id": "MH_TWN_MAN", "name": "Mangaon", "name_mr": "माणगाव", "name_hi": "माणगांव", "district": "Raigad", "division": "Konkan Division", "region": "Konkan", "lat": 18.2500, "lon": 73.2800, "type": "corridor_node", "emission_profile": "Mumbai-Goa NH66 key transit crossroads, Konkan railway"},
    {"id": "MH_TWN_MHD", "name": "Mahad", "name_mr": "महाड", "name_hi": "महाड", "district": "Raigad", "division": "Konkan Division", "region": "Konkan", "lat": 18.0800, "lon": 73.4200, "type": "industrial_hub", "emission_profile": "Savitri river valley, major chemical & pharma MIDC, flood basin"},
    {"id": "MH_TWN_ALI", "name": "Alibaug", "name_mr": "अलिबाग", "name_hi": "अलिबाग", "district": "Raigad", "division": "Konkan Division", "region": "Konkan", "lat": 18.6414, "lon": 72.8722, "type": "taluka_town", "emission_profile": "Coastal tourism, marine salt breeze, RCF Thal fertilizer plant nearby"},
    {"id": "MH_TWN_CHIP", "name": "Chiplun", "name_mr": "चिपळूण", "name_hi": "चिपळूण", "district": "Ratnagiri", "division": "Konkan Division", "region": "Konkan", "lat": 17.5300, "lon": 73.5100, "type": "industrial_hub", "emission_profile": "Vashishti river basin, Lote Parshuram chemical industrial complex"},
    {"id": "MH_TWN_DAP", "name": "Dapoli", "name_mr": "दापोली", "name_hi": "दापोली", "district": "Ratnagiri", "division": "Konkan Division", "region": "Konkan", "lat": 17.7600, "lon": 73.1800, "type": "taluka_town", "emission_profile": "Dr. BSKKV Agricultural University, coastal hill climate ('Camp Dapoli')"},
    {"id": "MH_TWN_KAN", "name": "Kankavli", "name_mr": "कणकवली", "name_hi": "कणकवली", "district": "Sindhudurg", "division": "Konkan Division", "region": "Konkan", "lat": 16.2700, "lon": 73.7100, "type": "corridor_node", "emission_profile": "Central Sindhudurg business hub, Gad river, Konkan railway"},
    {"id": "MH_TWN_SAW", "name": "Sawantwadi", "name_mr": "सावंतवाडी", "name_hi": "सावंतवाड़ी", "district": "Sindhudurg", "division": "Konkan Division", "region": "Konkan", "lat": 15.9000, "lon": 73.8200, "type": "taluka_town", "emission_profile": "Moti Talao lake, wooden craft heritage, Goa border transit corridor"},
    {"id": "MH_TWN_MAL2", "name": "Malvan", "name_mr": "मालवण", "name_hi": "मालवन", "district": "Sindhudurg", "division": "Konkan Division", "region": "Konkan", "lat": 16.0600, "lon": 73.4700, "type": "taluka_town", "emission_profile": "Sindhudurg Fort, marine sanctuary, coastal fisheries"},
    {"id": "MH_TWN_DAH", "name": "Dahanu", "name_mr": "डहाणू", "name_hi": "डहाणू", "district": "Palghar", "division": "Konkan Division", "region": "Konkan", "lat": 19.9700, "lon": 72.7300, "type": "taluka_town", "emission_profile": "Dahanu 500MW Thermal Power Station, chickoo orchards, coastal belt"},
    {"id": "MH_TWN_BOI", "name": "Boisar", "name_mr": "बोईसर", "name_hi": "बोईसर", "district": "Palghar", "division": "Konkan Division", "region": "Konkan", "lat": 19.8000, "lon": 72.7500, "type": "industrial_hub", "emission_profile": "Tarapur MIDC (Maharashtra's largest chemical zone) & TAPS Nuclear Power"},
    {"id": "MH_TWN_VAS", "name": "Vasai-Virar", "name_mr": "वसई-विरार", "name_hi": "वसई-विरार", "district": "Palghar", "division": "Konkan Division", "region": "Konkan", "lat": 19.3800, "lon": 72.8300, "type": "industrial_hub", "emission_profile": "High density peri-urban metropolis (1.3M pop), commuter rail & small industries"}
]


def get_all_towns() -> List[Dict[str, Any]]:
    """Returns catalog of in-between cities, talukas, and corridor hubs."""
    return MAHARASHTRA_IN_BETWEEN_TOWNS


def get_all_locations() -> List[Dict[str, Any]]:
    """Returns combined catalog of all 36 districts + in-between towns/talukas."""
    combined = []
    for d in MAHARASHTRA_DISTRICTS:
        item = dict(d)
        item["is_district_hq"] = True
        combined.append(item)
    for t in MAHARASHTRA_IN_BETWEEN_TOWNS:
        item = dict(t)
        item["is_district_hq"] = False
        item["has_cpcb"] = False
        item["tier"] = 3
        combined.append(item)
    return combined


def search_locations(query: str) -> List[Dict[str, Any]]:
    """Fast case-insensitive search across English, Marathi, and Hindi names."""
    if not query or not query.strip():
        return get_all_locations()

    q = query.strip().lower()
    results = []
    for loc in get_all_locations():
        name_en = loc.get("name", "").lower()
        name_mr = loc.get("name_mr", "")
        name_hi = loc.get("name_hi", "")
        district = loc.get("district", loc.get("name", "")).lower()

        if q in name_en or q in name_mr or q in name_hi or q in district:
            results.append(loc)
    return results


def find_nearest_location(lat: float, lon: float) -> Dict[str, Any]:
    """Finds nearest location (district or in-between town) to query coordinates."""
    min_dist = float("inf")
    all_locs = get_all_locations()
    nearest = all_locs[0]

    for loc in all_locs:
        d_lat = (lat - loc["lat"]) * 111.0
        d_lon = (lon - loc["lon"]) * (111.0 * np.cos(np.radians(lat)))
        dist = np.sqrt(d_lat**2 + d_lon**2)
        if dist < min_dist:
            min_dist = dist
            nearest = loc

    res = dict(nearest)
    res["distance_to_center_km"] = round(float(min_dist), 2)
    return res

