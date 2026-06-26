class LuxEndpoints:

    BASE_URL = "https://server.luxpowertek.com/WManage"
    LOGIN = f"{BASE_URL}/web/login"
    INVERTER_DATA = f"{BASE_URL}/api/inverter/getInverterRuntimeParallel"
    SERIALS = ['2423500220', '52730V1056', '2453530895']
    # Новий ендпоінт для експорту файлів
    EXPORT_DATA = f"{BASE_URL}/web/analyze/data/export"