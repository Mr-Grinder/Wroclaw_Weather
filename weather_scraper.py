from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.chrome.options import Options
import logging


#   Налаштування логування
# -------------------------------
logging.basicConfig(
    level=logging.INFO,                  
    format="%(asctime)s - %(levelname)s - %(message)s",
    filename="scraper.log",
    filemode="a"
)


def get_weather_info() -> str:
    """
    Повертає текстовий опис поточної погоди у Вроцлаві.
    Якщо не вдалося запустити браузер або знайти елемент — повертає відповідне повідомлення.
    """
    logging.info("get_weather_info(): Launching ChromeDriver in headless mode")

    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')

    try:
        driver = webdriver.Chrome(options=options)
    except WebDriverException as e:
        logging.error(f"Не вдалося запустити ChromeDriver: {e}")
        return "❌ Не вдалося запустити браузер."

    try:
        url = "https://www.timeanddate.com/weather/poland/wroclaw"
        driver.get(url)
        logging.info("Loaded page: " + url)

        # Очікуємо, поки з'явиться блок із швидкою інформацією про погоду
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CLASS_NAME, "bk-focus__qlook"))
        )

        # Витягуємо температуру (елемент з класом "h2" всередині блока qlook)
        temp_elem = driver.find_element(By.CSS_SELECTOR, ".bk-focus__qlook .h2")
        temperature = temp_elem.text.strip()  # Наприклад: "23 °C"

        # Витягуємо короткий опис (перший <p> в блоці .bk-focus__qlook)
        condition_elem = driver.find_element(By.CSS_SELECTOR, ".bk-focus__qlook")
        description = condition_elem.find_element(By.TAG_NAME, "p").text.strip()

        weather_text = (
            f"🌤️ <b>Today in Wroclaw</b>\n"
            f"Temperature: {temperature}\n"
            f"{description}"
        )
        logging.info(f"get_weather_info(): Extracted -> {weather_text}")
        return weather_text

    except Exception as e:
        logging.error(f"Помилка при отриманні погоди: {e}")
        return "❌ Не вдалося отримати дані про погоду."

    finally:
        driver.quit()


def get_weather_forecast_14days() -> str:
    """
    Повертає текстовий опис 14-денного прогнозу погоди у Вроцлаві
    та зберігає деталі в forecast_14days.csv.
    """
    logging.info("get_weather_forecast_14days(): Launching ChromeDriver in headless mode")

    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')

    try:
        driver = webdriver.Chrome(options=options)
    except WebDriverException as e:
        logging.error(f"Не вдалося запустити ChromeDriver: {e}")
        return "❌ Не вдалося запустити браузер."

    try:
        url = "https://www.timeanddate.com/weather/poland/wroclaw/ext"
        driver.get(url)
        logging.info("Loaded page: " + url)

        # Очікуємо, поки з'явиться 14-денна таблиця з прогнозом
        table = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CLASS_NAME, "zebra.tb-wt"))
        )

        rows = table.find_elements(By.TAG_NAME, "tr")
        forecast_text = "<b>📆 14-Day Weather Forecast for Wroclaw:</b>\n\n"
        data_rows = []

        for i, row in enumerate(rows[1:], 1):  # пропускаємо заголовок
            try:
                cols = row.find_elements(By.TAG_NAME, "td")
                if len(cols) >= 8:
                    day = cols[0].text.strip()        # Наприклад: "Fri  6 Jun"
                    temp = cols[1].text.strip()       # Наприклад: "23 / 15 °C"
                    weather = cols[2].text.strip()    # Наприклад: "Sunny"
                    feels = cols[3].text.strip()      # Наприклад: "Feels Like 20 °C"
                    wind = cols[4].text.strip()       # Наприклад: "7 km/h"
                    humidity = cols[5].text.strip()   # Наприклад: "60 %"
                    chance = cols[6].text.strip()     # Наприклад: "10 %"
                    amount = cols[7].text.strip()     # Наприклад: "0 mm"

                    # Формуємо текстовий рядок
                    forecast_text += (
                        f"📅 {day}: {temp}, {weather}, {feels}, Wind {wind}\n"
                        f"   Humidity: {humidity}, Rain chance: {chance}, Amount: {amount}\n\n"
                    )

                    data_rows.append([
                        day, temp, weather, feels, wind,
                        humidity, chance, amount
                    ])
            except Exception as e:
                logging.error(f"[Row {i}] Error processing row: {e}")
                continue

        # Зберігаємо у CSV
        import pandas as pd
        columns = [
            "Дата прогнозу", "Температура", "Погода", "Відчувається як", "Вітер",
            "Вологість", "Ймовірність опадів", "Кількість опадів"
        ]
        df = pd.DataFrame(data_rows, columns=columns)
        df.to_csv("forecast_14days.csv", index=False, encoding="utf-8")
        logging.info("get_weather_forecast_14days(): Saved forecast_14days.csv")

        return forecast_text

    except TimeoutException as e:
        logging.error("Timeout waiting for 14-day forecast table")
        return "❌ Прогноз на 14 днів недоступний в даний момент."

    except Exception as e:
        logging.error(f"Помилка при отриманні 14-денного прогнозу: {e}")
        return "❌ Не вдалося отримати 14-денний прогноз."

    finally:
        driver.quit()
