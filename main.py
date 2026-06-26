import calendar
from datetime import datetime
from lux_api import LuxPowerClient
from lux_exporter import LuxDataExporter  # Імпортуємо наш новий клас
import pandas as pd


def generate_date_periods(year: int, month: int):
    """Автоматично генерує блоки дат по 9 днів для будь-якого місяця"""
    # Дізнаємося кількість днів у місяці (наприклад, для травня 2026 це 31)
    _, last_day = calendar.monthrange(year, month)

    periods = []
    start = 1
    while start <= last_day:
        end = min(start + 8, last_day)  # крок 9 днів (включаючи перший день)


        # Форматуємо у вигляд YYYY-MM-DD
        start_str = f"{year}-{month:02d}-{start:02d}"
        end_str = f"{year}-{month:02d}-{end:02d}"

        periods.append((start_str, end_str))
        start = end + 1

    return periods, last_day

def main():
    # 1. Ініціалізуємо базового клієнта авторизації
    client = LuxPowerClient()

    # 2. Передаємо клієнта в наш новий сервіс експорту
    exporter = LuxDataExporter(client)

    # 3. Конфігуруємо потрібний період дат
    year = datetime.today().year
    try:
        month = int(input("Введіть номер місяця для аналізу (1-12): "))
        if not (1 <= month <= 12):
            raise ValueError
    except ValueError:
        print("❌ Некоректний номер місяця. Завершення роботи.")
        return

    date_periods, total_days = generate_date_periods(year, month)

    # 4. Отримуємо ОДИН готовий фінальний DataFrame в пам'ять
    final_dataframe = exporter.download_monthly_data(date_periods)

    # final_dataframe = pd.read_csv('luxpower_monthly_report.csv')

    # 5. Якщо дані успішно зібрано — зберігаємо їх на диск
    if not final_dataframe.empty:
        print(f"\nФінальний масив готовий! Загальна кількість рядків: {len(final_dataframe)}")

        """
        Розбираємо роботу пандас, перетворюємо типи даних, фільтруємо по колонках
        """
        final_dataframe['Time'] = pd.to_datetime(final_dataframe['Time'])
        final_dataframe['Date_Only'] = final_dataframe['Time'].dt.date

        if 'SOC' in final_dataframe.columns:
            final_dataframe['SOC'] = final_dataframe['SOC'].astype(str).str.replace('%', '').astype(float)/100
            final_dataframe['SOC'] = final_dataframe['SOC'].round(3)

        daily_summary = final_dataframe.groupby(['Serial number', 'Date_Only']).agg(
            SOC = ('SOC', 'mean'),
            ppv1 = ('ppv1', 'max'),
            ppv2 = ('ppv2', 'max'),
            ePv1Day = ('ePv1Day', 'max'),
            ePv2Day = ('ePv2Day', 'max'),
            eToUserDay = ('eToUserDay', 'max'),
            eInvDay = ('eInvDay', 'max'),
            eRecDay=('eRecDay', 'max'),
            eChgDay=('eChgDay', 'max'),
            eDisChgDay=('eDisChgDay', 'max'),
            eEpsDay=('eEpsDay', 'max'),
            eToGridDay=('eToGridDay', 'max'),
        ).reset_index()

        # 6. Створюємо трафаретну сітку з дат місяця та серійних номерів інверторів
        # задля отримання інформації про повний місяць, на випадок, якщо за якийсь день дані будуть відсутні

        # --- КРОК 1: Створюємо "ідеальний трафарет" дат строго під обраний місяць ---
        # (Наприклад, травень 2026 року: з 01 по 31 число)

        full_date_range = pd.date_range(start=f"{year}-{month:02d}-01", end=f"{year}-{month:02d}-{total_days}").date

        # Беремо унікальні серійні номери інверторів, які взагалі є у твоїх даних
        unique_serials = daily_summary['Serial number'].unique()

        # Створюємо повну сітку: кожен інвертор ПОВИНЕН мати кожен день місяця
        ideal_index = pd.MultiIndex.from_product(
            [unique_serials, full_date_range],
            names=['Serial number', 'Date_Only']
        ).to_frame().reset_index(drop=True)

        # --- КРОК 2: Накладаємо наші дані на цей трафарет ---
        # how='left' означає: зберегти абсолютно всі рядки з ідеального трафарету,
        # навіть якщо для них немає даних у daily_summary
        daily_summary = pd.merge(ideal_index, daily_summary, on=['Serial number', 'Date_Only'], how='left')

        # --- КРОК 3: Заміняємо порожнечі (NaN) на нулі ---
        # Знаходимо всі колонки, крім текстових ідентифікаторів
        numeric_cols = daily_summary.columns.drop(['Serial number', 'Date_Only'])

        # Заповнюємо їх нулями
        daily_summary[numeric_cols] = daily_summary[numeric_cols].fillna(0.0)

        # --- КРОК 4: Сортуємо для краси ---
        daily_summary = daily_summary.sort_values(by=['Serial number', 'Date_Only']).reset_index(drop=True)

        # print(daily_summary.to_string())

        output_filename = f"{month}_report.csv"
        daily_summary.round(3).to_csv(
            output_filename,
            index=False,
            encoding="utf-8",
            sep=';',
            decimal=',',
        )

        print(f"🔥 Дані успішно збережено на диск у файл: {output_filename}")

        # ТУТ ТИ ЗМОЖЕШ ЗАПУСТИТИ СВІЙ АНАЛІЗ:
        # analyze_data(final_dataframe)
    else:
        print("❌ Скрипт завершено без збереження: дані відсутні.")


if __name__ == "__main__":
    main()