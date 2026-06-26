import io
import pandas as pd
from config import LuxEndpoints

class LuxDataExporter:
    def __init__(self, client):
        """
        Приймає вже створений об'єкт LuxPowerClient,
        щоб використовувати його сесію та стан авторизації.
        """
        self.client = client

    def download_monthly_data(self, date_periods, serials=None):
        """
        Виконує повний цикл завантаження Excel-вкладок у пам'ять
        та об'єднує їх в один великий DataFrame.
        """
        if serials is None:
            serials = LuxEndpoints.SERIALS

        all_chunks = []
        print("Запуск процесу експорту даних у пам'ять через LuxDataExporter...")

        for sn in serials:
            print(f"\nОбробка інвертора: {sn}")

            for start_date, end_date in date_periods:
                print(f" -> Запит за період: {start_date} - {end_date}")

                # Формуємо динамічний лінк для скачування файлу
                download_url = f"{LuxEndpoints.EXPORT_DATA}/{sn}/{start_date}"
                params = {"endDateText": end_date}

                try:
                    # Контролюємо, щоб сесія була активною
                    if not self.client.is_logged_in:
                        self.client.login()

                    # Використовуємо .get сесії нашого клієнта
                    response = self.client.session.get(download_url, params=params, timeout=15)

                    if response.status_code == 200:
                        # Загортаємо сирі байти Excel-файлу у віртуальний файл в RAM
                        excel_file_in_memory = io.BytesIO(response.content)

                        # Читаємо абсолютно всі вкладки файлу (sheet_name=None)
                        all_sheets = pd.read_excel(excel_file_in_memory, sheet_name=None)

                        sheets_count = 0
                        rows_count = 0

                        for sheet_name, df_sheet in all_sheets.items():
                            if not df_sheet.empty:
                                all_chunks.append(df_sheet)
                                sheets_count += 1
                                rows_count += len(df_sheet)

                        print(f"   Успішно оброблено. Знайдено днів (вкладок): {sheets_count}, рядків: {rows_count}")
                    else:
                        print(f"   Помилка сервера (Код {response.status_code}) для періоду {start_date}")

                except Exception as e:
                    print(f"   Помилка з'єднання під час завантаження: {e}")

        print("\n--- ЕКСПОРТ ЗАВЕРШЕНО ---")
        print(f"Всього завантажено шматків (вкладок Excel) в пам'ять: {len(all_chunks)}")

        if all_chunks:
            print("Об'єднуємо всі шматки в один великий масив...")
            return pd.concat(all_chunks, ignore_index=True)
        else:
            print("Не вдалося зібрати жодного файлу.")
            return pd.DataFrame()  # Повертаємо порожній DF, щоб уникнути NameError далі