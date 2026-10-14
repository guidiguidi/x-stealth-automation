import os
import random
import sys
import time
import json
from pathlib import Path
import tempfile
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.action_chains import ActionChains
# ========================
# КОНФИГУРАЦИЯ И НАСТРОЙКИ
# ========================
BASE_DIR = Path(__file__).parent
SETTINGS_DIR = BASE_DIR / "settings"
DIALOGS_DIR = BASE_DIR / "dialogs"

# Файлы конфигурации
CONFIG_FILE = SETTINGS_DIR / "config.json"
TOKEN_PREFS_FILE = SETTINGS_DIR / "token_prefs.json"
USER_AGENTS_FILE = SETTINGS_DIR / "user_agents.txt"
USER_IDS_FILE = SETTINGS_DIR / "ids.txt"
MESSAGES_FILE = SETTINGS_DIR / "messages.txt"
GOOD_LOG = DIALOGS_DIR / "good.txt"
BAD_LOG = DIALOGS_DIR / "bad.txt"
DEFAULT_CONFIG_FILE = SETTINGS_DIR / "default_config.json"
CONFIG_FILE = SETTINGS_DIR / "config.json"

# Глобальные переменные
users = []
messages = []
user_agents = []
config = None
# ========================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ========================
def init_default_config():
    """Создает дефолтный конфиг если его нет"""
    if not DEFAULT_CONFIG_FILE.exists():
        default_config = {
            "action_delay": 4,
            "scroll_time": 4,
            "proxy_enabled": False,
            "proxy": "socks5://user:pass@ip:port"
        }
        with open(DEFAULT_CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(default_config, f, indent=2)

def init_folders():
    """Создает необходимые папки если они не существуют"""
    os.makedirs(SETTINGS_DIR, exist_ok=True)
    os.makedirs(DIALOGS_DIR, exist_ok=True)


def log(msg, level="INFO"):
    """Логирование сообщений"""
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{level}] {msg}")


def wait_input(prompt="Нажмите ENTER чтобы продолжить..."):
    """Ожидание ввода пользователя"""
    input(prompt)


def random_message():
    """Возвращает случайное сообщение из списка"""
    return random.choice(messages) if messages else ""


# ========================
# ЗАГРУЗКА КОНФИГУРАЦИИ
# ========================
def load_config():
    """Загружает конфигурацию, объединяя дефолтные и пользовательские настройки"""
    init_default_config()

    with open(DEFAULT_CONFIG_FILE, "r", encoding="utf-8") as f:
        config = json.load(f)

    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                user_config = json.load(f)
                for key in user_config:
                    if key in config:
                        config[key] = user_config[key]
        except json.JSONDecodeError:
            log("Ошибка чтения config.json, используются значения по умолчанию", "WARNING")

    return config

def save_config():
    """Сохраняет текущую конфигурацию в файл"""
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)


def load_user_agents():
    """Загружает список User-Agent'ов"""
    global user_agents

    if not USER_AGENTS_FILE.exists():
        user_agents.extend([
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0"
        ])
        return

    with open(USER_AGENTS_FILE, "r", encoding="utf-8") as f:
        user_agents.extend(
            line.strip() for line in f
            if line.strip() and not line.startswith("#")
        )


def load_users():
    """Загружает список пользователей"""
    global users

    if USER_IDS_FILE.exists():
        with open(USER_IDS_FILE, "r", encoding="utf-8") as f:
            users.extend(
                line.strip() for line in f
                if line.strip() and not line.startswith("#")
            )


def load_messages():
    """Загружает список сообщений"""
    global messages

    if MESSAGES_FILE.exists():
        with open(MESSAGES_FILE, "r", encoding="utf-8") as f:
            messages.extend(
                line.strip() for line in f
                if line.strip() and not line.startswith("#")
            )


def load_token_prefs():
    """Загружает сохраненные токены"""
    if not TOKEN_PREFS_FILE.exists():
        return {
            "auth_token": "",
            "ct0": "",
            "last_updated": ""
        }

    try:
        with open(TOKEN_PREFS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}


def save_token_prefs(prefs):
    """Сохраняет токены в файл"""
    prefs["last_updated"] = time.strftime("%Y-%m-%d %H:%M:%S")
    with open(TOKEN_PREFS_FILE, "w", encoding="utf-8") as f:
        json.dump(prefs, f, indent=2, ensure_ascii=False)


# ========================
# РАБОТА С WEBDRIVER
# ========================
def setup_driver():
    """Настраивает и возвращает экземпляр WebDriver с антидетект настройками"""
    options = Options()

    # 1. Базовые настройки для маскировки
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    # 2. Настройка User-Agent
    user_agent = random.choice(user_agents)
    options.add_argument(f"user-agent={user_agent}")

    # 3. Прокси настройки (если включены в конфиге)
    if config.get("proxy_enabled", False) and config.get("proxy"):
        proxy = config["proxy"]
        options.add_argument(f"--proxy-server={proxy}")
        proxy_log = proxy.split('@')[-1] if '@' in proxy else proxy
        log(f"Используется прокси: {proxy_log}")

    # 4. Дополнительные параметры для маскировки
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-web-security")
    options.add_argument("--disable-site-isolation-trials")
    options.add_argument("--disable-blink-features")
    options.add_argument("--disable-infobars")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--disable-default-apps")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-software-rasterizer")
    options.add_argument("--disable-remote-fonts")
    options.add_argument("--disable-logging")
    options.add_argument("--log-level=3")
    options.add_argument("--output=/dev/null")

    # 5. Настройки окна браузера
    options.add_argument(f"--window-size={random.randint(900, 1400)},{random.randint(600, 900)}")

    # 6. Отключаем WebDriver признаки
    params = {
        "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    }
    options.add_experimental_option("excludeSwitches", ["enable-automation"])

    try:
        # Инициализация драйвера с настройками
        driver = webdriver.Chrome(options=options)

        # 7. Изменяем JavaScript свойства
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": """
                Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3]});
                Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
                window.chrome = {runtime: {}};
            """
        })

        # 8. Рандомизация параметров
        driver.execute_script(
            "Object.defineProperty(navigator, 'platform', {get: function() {return 'Win32';}});"
        )
        driver.execute_script(
            "Object.defineProperty(navigator, 'hardwareConcurrency', {get: function() {return 4;}});"
        )

        # 9. Эмуляция поведения человека
        action = ActionChains(driver)
        action.move_by_offset(random.randint(1, 5), random.randint(1, 5)).perform()

        return driver

    except Exception as e:
        log(f"Ошибка инициализации WebDriver: {str(e)}", "ERROR")
        raise


def login_and_save_tokens(driver):
    """Выполняет автоматический вход с использованием сохранённых токенов"""
    try:
        token_prefs = load_token_prefs()

        if not token_prefs.get("auth_token") or not token_prefs.get("ct0"):
            raise Exception("Токены для входа не найдены в token_prefs.json")

        log("Использую сохранённые токены для автоматического входа")

        driver.get("https://x.com")
        time.sleep(2)
        driver.execute_script("window.localStorage.setItem('selenium', 'false');")
        driver.delete_all_cookies()

        driver.add_cookie({
            "name": "auth_token",
            "value": token_prefs["auth_token"],
            "domain": ".x.com"
        })

        driver.add_cookie({
            "name": "ct0",
            "value": token_prefs["ct0"],
            "domain": ".x.com"
        })

        driver.refresh()
        time.sleep(3)

        current_url = driver.current_url
        if "https://x.com/home" in current_url:
            log("Успешный автоматический вход (перенаправление на /home)")
            return True

        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'div[data-testid="primaryColumn"]')))
            log("Успешный автоматический вход (найдена лента новостей)")
            return True
        except:
            raise Exception("Не удалось подтвердить вход - возможно, токены устарели")

    except Exception as e:
        log(f"Ошибка автоматического входа: {str(e)}", "ERROR")
        log("Попробуйте обновить токены вручную", "WARNING")

        driver.get("https://x.com/i/flow/login")
        wait_input("Выполните вход вручную и нажмите ENTER...")

        start_time = time.time()
        while time.time() - start_time < 30:
            if "https://x.com/home" in driver.current_url:
                log("Ручной вход выполнен успешно (перенаправление на /home)")
                break
            time.sleep(1)

        if input("Сохранить новые токены для следующего входа? (y/n): ").lower() == "y":
            cookies = driver.get_cookies()
            token_prefs = {
                "auth_token": next((c["value"] for c in cookies if c["name"] == "auth_token"), ""),
                "ct0": next((c["value"] for c in cookies if c["name"] == "ct0"), ""),
            }
            save_token_prefs(token_prefs)
            log("Новые токены успешно сохранены")

        return True

# ========================
# ОСНОВНЫЕ ФУНКЦИИ
# ========================
def random_actions(driver):
    """
    Выполняет случайные действия в браузере для имитации человеческого поведения
    Возможные действия:
    - Случайный скроллинг
    - Перемещение курсора
    - Клики по пустому месту
    - Переключение между вкладками
    - Микро-паузы
    """
    try:
        actions = [
            # Случайный скроллинг (вверх/вниз)
            lambda: driver.execute_script(f"window.scrollBy(0, {random.randint(-300, 300)})"),

            # Движение курсора по случайной траектории
            lambda: ActionChains(driver).move_by_offset(
                random.randint(-50, 50),
                random.randint(-50, 50)
            ).perform(),

            # Клик по пустому месту (50% chance)
            lambda: ActionChains(driver).click().perform() if random.random() > 0.5 else None,

            # Микро-пауза с разной длительностью
            lambda: time.sleep(random.uniform(0.1, 1.2)),

            # Переключение между вкладками (если их больше одной)
            lambda: driver.switch_to.window(random.choice(driver.window_handles))
            if len(driver.window_handles) > 1 else None
        ]

        # Выполняем 3-5 случайных действий
        for _ in range(random.randint(3, 5)):
            try:
                random.choice(actions)()
                time.sleep(random.uniform(0.3, 1.0))
            except:
                continue

    except Exception as e:
        log(f"Ошибка при выполнении случайных действий: {str(e)}", "WARNING")


def human_type(element, text):
    """
    Эмулирует человеческий ввод текста с:
    - Разной скоростью набора
    - Случайными опечатками и исправлениями
    - Естественными паузами между словами
    """
    try:
        words = text.split(' ')
        for i, word in enumerate(words):
            for j, char in enumerate(word):
                element.send_keys(char)

                delay = random.uniform(0.05, 0.3)

                # 10% chance сделать опечатку и исправить её
                if random.random() < 0.1 and j > 2:
                    wrong_char = random.choice('abcdefghijklmnopqrstuvwxyz')
                    element.send_keys(wrong_char)
                    time.sleep(delay / 2)
                    element.send_keys(Keys.BACKSPACE)
                    time.sleep(delay / 2)
                    element.send_keys(char)

                time.sleep(delay)

            if i < len(words) - 1:
                space_delay = random.uniform(0.1, 0.4)
                element.send_keys(' ')
                time.sleep(space_delay)

                # 5% chance сделать паузу подольше (как будто задумался)
                if random.random() < 0.05:
                    time.sleep(random.uniform(0.5, 1.5))

    except Exception as e:
        log(f"Ошибка при эмуляции ввода: {str(e)}", "WARNING")
        element.send_keys(text)

def human_like_click(driver, element):
    """Эмуляция человеческого клика"""
    action = ActionChains(driver)
    action.move_to_element(element).pause(random.uniform(0.1, 0.5)).click().perform()
def send_dm(driver, username, message):
    """
    Отправляет прямое сообщение пользователю с полной эмуляцией человеческого поведения:
    1. Случайные действия перед началом
    2. Естественный поиск пользователя
    3. Человекообразный ввод сообщения
    4. Проверка отправки
    5. Логирование результата
    """
    try:
        log(f"Начинаю отправку сообщения для @{username}")

        random_actions(driver)

        driver.get("https://x.com/messages/compose")
        time.sleep(random.uniform(1.2, 2.8))

        search = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'input[data-testid="searchPeople"]'))
        )

        human_type(search, f"@{username}")
        time.sleep(random.uniform(0.5, 1.8))

        time.sleep(random.uniform(1.0, 2.0))

        user_elements = driver.find_elements(
            By.CSS_SELECTOR, "span.css-1jxf684.r-bcqeeo.r-1ttztb7.r-qvutc0.r-poiln3"
        )

        user_found = False
        for el in user_elements:
            txt = el.text.strip().lower()
            if txt == f"@{username.lower()}":
                human_like_click(driver, el)
                user_found = True
                break
            if f"{username.lower()} can't be messaged" in txt:
                raise Exception("can't be messaged")

        if not user_found:
            raise Exception("user not found")

        time.sleep(random.uniform(0.8, 1.5))

        next_buttons = driver.find_elements(
            By.XPATH, '//span[contains(text(), "Next") or contains(text(), "Далее")]'
        )
        if next_buttons:
            human_like_click(driver, next_buttons[0])

        input_el = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((
                By.CSS_SELECTOR,
                'div[data-testid="dmComposerTextInput"][contenteditable="true"]'
            ))
        )

        time.sleep(random.uniform(0.5, 3.0))

        human_type(input_el, message)

        send_btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable(
                (By.CSS_SELECTOR, 'button[data-testid="dmComposerSendButton"]')
            )
        )

        random_actions(driver)
        human_like_click(driver, send_btn)

        check_sent(driver)

        log(f"Сообщение для @{username} успешно отправлено")
        with open(GOOD_LOG, "a", encoding="utf-8") as f:
            f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} | {username} | {message}\n")

        random_actions(driver)

        return True

    except Exception as e:
        error_msg = f"Ошибка отправки для @{username}: {str(e)}"
        log(error_msg, "ERROR")

        with open(BAD_LOG, "a", encoding="utf-8") as f:
            f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} | {username} | {error_msg}\n")

        if "can't be messaged" in str(e):
            log(f"Пытаюсь подписаться на @{username}...", "WARNING")
            follow_user(driver, username)
        elif "user not found" in str(e):
            log(f"Пользователь @{username} не найден, пропускаю", "WARNING")

        time.sleep(random.uniform(5.0, 10.0))
        return False

def check_sent(driver):
    """Проверяет что сообщение было отправлено"""
    start = time.time()
    while time.time() - start < 10:
        elements = driver.find_elements(
            By.CSS_SELECTOR, "span.css-1jxf684.r-bcqeeo.r-1ttztb7.r-qvutc0.r-poiln3"
        )
        for el in elements:
            if el.text.strip().lower() == "sent":
                return
        time.sleep(0.5)
    raise Exception("no sent status")


def follow_user(driver, username):
    """Подписывается на пользователя"""
    log(f"Попытка подписаться на @{username}")
    driver.get(f"https://x.com/{username}")

    start = time.time()
    while time.time() - start < 30:
        buttons = driver.find_elements(By.CSS_SELECTOR, 'button[role="button"]')
        for btn in buttons:
            label = btn.get_attribute("aria-label")
            if label == f"Follow @{username}":
                btn.click()
                log(f"Успешно подписался на @{username}")
                return
            if label in [f"Following @{username}", f"Unfollow @{username}"]:
                log(f"Уже подписан на @{username}")
                return
        time.sleep(0.5)
    raise Exception("follow button not found")


# ========================
# ГЛАВНАЯ ФУНКЦИЯ
# ========================
def main():
    """Основная функция выполнения скрипта"""
    global config

    try:
        init_folders()
        config = load_config()
        load_user_agents()
        load_users()
        load_messages()

        if not users:
            log("Нет пользователей для отправки сообщений", "ERROR")
            return

        if not messages:
            log("Нет сообщений для отправки", "ERROR")
            return

        driver = setup_driver()

        try:
            login_and_save_tokens(driver)

            for i, user in enumerate(users):
                try:
                    msg = random_message()
                    send_dm(driver, user, msg)

                    with open(GOOD_LOG, "a", encoding="utf-8") as f:
                        f.write(f"{user} : {msg}\n")

                    if i < len(users) - 1:
                        time.sleep(config["action_delay"])

                except Exception as e:
                    log(f"Ошибка для @{user}: {str(e)}", "ERROR")

                    with open(BAD_LOG, "a", encoding="utf-8") as f:
                        f.write(f"{user} : {str(e)}\n")

                    if str(e) == "can't be messaged":
                        follow_user(driver, user)
                    elif str(e) == "user not found":
                        continue

                    time.sleep(5)

        finally:
            driver.quit()
            log("Работа завершена")

    except Exception as e:
        log(f"Критическая ошибка: {str(e)}", "ERROR")
        sys.exit(1)


if __name__ == "__main__":
    main()