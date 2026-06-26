import os
import requests
from dotenv import load_dotenv
from config import LuxEndpoints

load_dotenv()


class LuxPowerClient:
    def __init__(self):
        self.username = os.getenv("ACCOUNT")
        self.password = os.getenv("PASSWORD")
        self.session = requests.Session()
        self.is_logged_in = False

    def login(self):
        """Метод для авторизації на сервісі з дебагом відповіді"""
        payload = {
            "account": self.username,
            "password": self.password,
        }
        try:
            response = self.session.post(LuxEndpoints.LOGIN, data=payload, timeout=5)

            if response.status_code == 200:
                self.is_logged_in = True
                print("Successfully authorized to Luxpower!")

                # # --- НАШ ДЕБАГ ТУТ ---
                # print("--- DEBUG LOGIN RESPONSE ---")
                # print("Status:", response.status_code)
                # print("Headers:", dict(response.headers))  # Дивимося, які куки або заголовки прийшли
                # print("Body (Сирий текст):", response.text[:500])  # Роздрукуємо перші 500 символів
                # print("----------------------------")

                return True

            print(f"Login error: {response.status_code}")
            return False
        except Exception as e:
            print(f"Connection error during login: {e}")
            return False

    def _post_request(self, url, payload):
        """Внутрішній допоміжний метод для безпечних POST-запитів з авто-перезавантаженням сесії"""
        if not self.is_logged_in:
            self.login()

        # Відправляємо через data=, як у робочому додатку
        response = self.session.post(url, data=payload, timeout=5)

        # Перевіряємо, чи не вилетіла помилка авторизації (UNLOGIN_ERROR)
        # Або якщо сервер повернув статус 401, або замість JSON прийшов HTML лінк логіну
        if response.status_code == 401 or "UNLOGIN_ERROR" in response.text:
            print("Сесія застаріла або протухла — виконуємо повторний логін...")
            self.login()
            response = self.session.post(url, data=payload, timeout=5)

        try:
            return response.json()
        except ValueError:
            print("Отримано некоректну відповідь (можливо HTML сторінка).")
            return None

    # def get_inverter_runtime(self, inverter_sn):
    #     """Method to get current data of every inverter by its serial number"""
    #     # Справжня назва параметра, яку хоче сервер — serialNum
    #     payload = {"serialNum": inverter_sn}
    #
    #     return self._post_request(LuxEndpoints.INVERTER_DATA, payload)