import concurrent.futures.thread
import hashlib
import io
import json
import logging
import os
import platform
import queue
import shutil
import sqlite3
import subprocess
import sys
import zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from contextlib import closing
from datetime import datetime
from glob import glob
from random import choice, choices, randint, shuffle, uniform
from time import gmtime, sleep, strftime, time

import requests
import undetected_chromedriver as uc
from fake_headers import Headers, browsers
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from undetected_chromedriver.patcher import Patcher

import website
from config import create_config

log = logging.getLogger('werkzeug')
log.disabled = True

os.system("")


class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


print(bcolors.OKGREEN + """

                        Yb    dP 88 888888 Yb        dP 888888 88""Yb 
                         Yb  dP  88 88__    Yb  db  dP  88__   88__dP 
                          YbdP   88 88""     YbdPYbdP   88""   88"Yb  
                           YP    88 888888    YP  YP    888888 88  Yb 
""" + bcolors.ENDC)

print(bcolors.OKCYAN + """
           [ Rumble Viewer ]
""" + bcolors.ENDC)

SCRIPT_VERSION = '1.6.2'

proxy = None
driver = None
status = None
server_running = False

urls = []
hash_urls = None
start_time = None

driver_list = []
view = []
duration_dict = {}
checked = {}
console = []
threads = 0

WEBRTC = os.path.join('extension', 'webrtc_control.zip')
ACTIVE = os.path.join('extension', 'always_active.zip')
FINGERPRINT = os.path.join('extension', 'fingerprint_defender.zip')
TIMEZONE = os.path.join('extension', 'spoof_timezone.zip')
CUSTOM_EXTENSIONS = glob(os.path.join('extension', 'custom_extension', '*.zip')) + \
    glob(os.path.join('extension', 'custom_extension', '*.crx'))

DATABASE = 'database.db'
DATABASE_BACKUP = 'database_backup.db'

WIDTH = 0
VIEWPORT = ['2560,1440', '1920,1080', '1440,900',
            '1536,864', '1366,768', '1280,1024', '1024,768']

CHROME = ['{8A69D345-D564-463c-AFF1-A69D9E530F96}',
          '{8237E44A-0054-442C-B6B6-EA0509993955}',
          '{401C381F-E0DE-4B85-8BD8-3F3F14FBDA57}',
          '{4ea16ac7-fd5a-47c3-875b-dbf4a2008c20}']

REFERERS = ['https://search.yahoo.com/', 'https://duckduckgo.com/', 'https://www.google.com/',
            'https://www.bing.com/', 'https://t.co/', '']

COMMANDS = [Keys.UP, Keys.DOWN, 'k', 'j', 'l', 't', 'c']

website.console = console
website.database = DATABASE

link = 'https://gist.githubusercontent.com/MShawon/29e185038f22e6ac5eac822a1e422e9d/raw/versions.txt'

output = requests.get(link, timeout=60).text
chrome_versions = output.split('\n')

browsers.chrome_ver = chrome_versions


def monkey_patch_exe(self):
    linect = 0
    replacement = self.gen_random_cdc()
    replacement = f"  var key = '${replacement.decode()}_';\n".encode()
    with io.open(self.executable_path, "r+b") as fh:
        for line in iter(lambda: fh.readline(), b""):
            if b"var key = " in line:
                fh.seek(-len(line), 1)
                fh.write(replacement)
                linect += 1
        return linect


Patcher.patch_exe = monkey_patch_exe


class UrlsError(Exception):
    pass


class SearchError(Exception):
    pass


class CaptchaError(Exception):
    pass


def timestamp():
    date_fmt = datetime.now().strftime("%d-%b-%Y %H:%M:%S")
    return bcolors.OKGREEN + f'[{date_fmt}] '


def download_driver():
    OSNAME = platform.system()

    print(bcolors.WARNING + 'Getting Chrome Driver...' + bcolors.ENDC)

    if OSNAME == 'Linux':
        OSNAME = 'lin'
        EXE_NAME = ""
        with subprocess.Popen(['google-chrome', '--version'], stdout=subprocess.PIPE) as proc:
            version = proc.stdout.read().decode('utf-8').replace('Google Chrome', '').strip()
    elif OSNAME == 'Darwin':
        OSNAME = 'mac'
        EXE_NAME = ""
        process = subprocess.Popen(
            ['/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', '--version'], stdout=subprocess.PIPE)
        version = process.communicate()[0].decode(
            'UTF-8').replace('Google Chrome', '').strip()
    elif OSNAME == 'Windows':
        OSNAME = 'win'
        EXE_NAME = ".exe"
        version = None
        try:
            process = subprocess.Popen(
                ['reg', 'query', 'HKEY_CURRENT_USER\\Software\\Google\\Chrome\\BLBeacon', '/v', 'version'],
                stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL
            )
            version = process.communicate()[0].decode(
                'UTF-8').strip().split()[-1]
        except:
            for i in CHROME:
                for j in ['opv', 'pv']:
                    try:
                        command = [
                            'reg', 'query', f'HKEY_LOCAL_MACHINE\\Software\\Google\\Update\\Clients\\{i}', '/v', f'{j}', '/reg:32']
                        process = subprocess.Popen(
                            command,
                            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL
                        )
                        version = process.communicate()[0].decode(
                            'UTF-8').strip().split()[-1]
                    except:
                        pass

        if not version:
            print(bcolors.WARNING +
                  "Couldn't find your Google Chrome version automatically!" + bcolors.ENDC)
            version = input(bcolors.WARNING +
                            'Please input your google chrome version (ex: 91.0.4472.114) : ' + bcolors.ENDC)
    else:
        print('{} OS is not supported.'.format(OSNAME))
        sys.exit()

    try:
        with open('version.txt', 'r') as f:
            previous_version = f.read()
    except:
        previous_version = '0'

    with open('version.txt', 'w') as f:
        f.write(version)

    if version != previous_version:
        try:
            os.remove(f'chromedriver{EXE_NAME}')
        except:
            pass

    major_version = version.split('.')[0]

    uc.TARGET_VERSION = major_version

    uc.install()

    return OSNAME, EXE_NAME


def copy_drivers(total):
    cwd = os.getcwd()
    current = os.path.join(cwd, f'chromedriver{EXE_NAME}')
    os.makedirs('patched_drivers', exist_ok=True)
    for i in range(total+1):
        try:
            destination = os.path.join(
                cwd, 'patched_drivers', f'chromedriver_{i}{EXE_NAME}')
            shutil.copy(current, destination)
        except Exception as e:
            print(e)
            pass


def create_database():
    with closing(sqlite3.connect(DATABASE)) as connection:
        with closing(connection.cursor()) as cursor:
            cursor.execute("""CREATE TABLE IF NOT EXISTS
            statistics (date TEXT, view INTEGER)""")

            connection.commit()

    try:
        # remove previous backup if exists
        os.remove(DATABASE_BACKUP)
    except:
        pass

    try:
        # backup latest database
        shutil.copy(DATABASE, DATABASE_BACKUP)
    except:
        pass


def update_database():
    today = str(datetime.today().date())
    with closing(sqlite3.connect(DATABASE, timeout=threads*10)) as connection:
        with closing(connection.cursor()) as cursor:
            try:
                cursor.execute(
                    "SELECT view FROM statistics WHERE date = ?", (today,))
                previous_count = cursor.fetchone()[0]
                cursor.execute("UPDATE statistics SET view = ? WHERE date = ?",
                               (previous_count + 1, today))
            except:
                cursor.execute(
                    "INSERT INTO statistics VALUES (?, ?)", (today, 0),)

            connection.commit()


def create_html(text_dict):
    global console

    if len(console) > 50:
        console.pop(0)

    date_fmt = f'<span style="color:#23d18b"> [{datetime.now().strftime("%d-%b-%Y %H:%M:%S")}] </span>'
    str_fmt = ''.join(
        [f'<span style="color:{key}"> {value} </span>' for key, value in text_dict.items()])
    html = date_fmt + str_fmt

    console.append(html)


def load_url():
    print(bcolors.WARNING + 'Loading urls...' + bcolors.ENDC)

    with open('url.txt', encoding="utf-8") as fh:
        links = [x.strip() for x in fh if x.strip() != '']

    print(bcolors.OKGREEN +
          f'{len(links)} url loaded from url.txt' + bcolors.ENDC)

    return links


def gather_proxy():
    proxies = []
    print(bcolors.OKGREEN + 'Scraping proxies ...' + bcolors.ENDC)

    link_list = ['https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list-raw.txt',
                 'https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt',
                 'https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/socks4.txt',
                 'https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/socks5.txt',
                 'https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/proxy.txt',
                 'https://raw.githubusercontent.com/sunny9577/proxy-scraper/master/proxies.txt']

    for link in link_list:
        response = requests.get(link)
        output = response.content.decode()
        proxy = output.split('\n')
        proxies = proxies + proxy
        print(bcolors.OKGREEN +
              f'{len(proxy)} proxies gathered from {link}' + bcolors.ENDC)
    
    proxies = list(filter(None, proxies))
    shuffle(proxies)

    return proxies


def load_proxy(filename):
    proxies = []

    with open(filename, encoding="utf-8") as fh:
        loaded = [x.strip() for x in fh if x.strip() != '']

    for lines in loaded:
        if lines.count(':') == 3:
            split = lines.split(':')
            lines = f'{split[2]}:{split[-1]}@{split[0]}:{split[1]}'
        proxies.append(lines)

    proxies = list(filter(None, proxies))
    shuffle(proxies)

    return proxies


def scrape_api(link):
    proxies = []

    response = requests.get(link)
    output = response.content.decode()
    if '\r\n' in output:
        proxy = output.split('\r\n')
    else:
        proxy = output.split('\n')

    for lines in proxy:
        if lines.count(':') == 3:
            split = lines.split(':')
            lines = f'{split[2]}:{split[-1]}@{split[0]}:{split[1]}'
        proxies.append(lines)

    proxies = list(filter(None, proxies))
    shuffle(proxies)

    return proxies


def detect_file_change():
    global hash_urls
    global urls

    with open("url.txt", "rb") as f:
        new_hash = hashlib.md5(f.read()).hexdigest()

    if new_hash != hash_urls:
        hash_urls = new_hash
        urls = load_url()


def check_proxy(agent, proxy, proxy_type):
    if category == 'f':
        headers = {
            'User-Agent': f'{agent}',
        }

        proxy_dict = {
            "http": f"{proxy_type}://{proxy}",
            "https": f"{proxy_type}://{proxy}",
        }
        response = requests.get(
            'https://www.youtube.com/', headers=headers, proxies=proxy_dict, timeout=30)
        status = response.status_code

    else:
        status = 200

    return status


def get_driver(path, agent, proxy, proxy_type, pluginfile):
    options = webdriver.ChromeOptions()
    options.headless = background
    options.add_argument(f"--window-size={choice(VIEWPORT)}")
    options.add_argument("--log-level=3")
    options.add_experimental_option(
        "excludeSwitches", ["enable-automation", "enable-logging"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_experimental_option(
        'prefs', {'intl.accept_languages': 'en_US,en'})
    options.add_argument(f"user-agent={agent}")
    options.add_argument("--mute-audio")
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-features=UserAgentClientHint')
    webdriver.DesiredCapabilities.CHROME['loggingPrefs'] = {
        'driver': 'OFF', 'server': 'OFF', 'browser': 'OFF'}

    if not background:
        options.add_extension(WEBRTC)
        options.add_extension(FINGERPRINT)
        options.add_extension(TIMEZONE)
        options.add_extension(ACTIVE)

        if CUSTOM_EXTENSIONS:
            for extension in CUSTOM_EXTENSIONS:
                options.add_extension(extension)

    if auth_required:
        proxy = proxy.replace('@', ':')
        proxy = proxy.split(':')
        manifest_json = """
        {
            "version": "1.0.0",
            "manifest_version": 2,
            "name": "Chrome Proxy",
            "permissions": [
                "proxy",
                "tabs",
                "unlimitedStorage",
                "storage",
                "<all_urls>",
                "webRequest",
                "webRequestBlocking"
            ],
            "background": {
                "scripts": ["background.js"]
            },
            "minimum_chrome_version":"22.0.0"
        }
        """

        background_js = """
        var config = {
                mode: "fixed_servers",
                rules: {
                singleProxy: {
                    scheme: "http",
                    host: "%s",
                    port: parseInt(%s)
                },
                bypassList: ["localhost"]
                }
            };

        chrome.proxy.settings.set({value: config, scope: "regular"}, function() {});

        function callbackFn(details) {
            return {
                authCredentials: {
                    username: "%s",
                    password: "%s"
                }
            };
        }

        chrome.webRequest.onAuthRequired.addListener(
                    callbackFn,
                    {urls: ["<all_urls>"]},
                    ['blocking']
        );
        """ % (proxy[2], proxy[-1], proxy[0], proxy[1])

        with zipfile.ZipFile(pluginfile, 'w') as zp:
            zp.writestr("manifest.json", manifest_json)
            zp.writestr("background.js", background_js)
        options.add_extension(pluginfile)

    else:
        options.add_argument(f'--proxy-server={proxy_type}://{proxy}')

    driver = webdriver.Chrome(executable_path=path, options=options)

    return driver


def play_video(driver):
    try:
        driver.execute_script("document.querySelector('div.bigPlayUI').click()")
    except:
        try:
            driver.find_element_by_css_selector(
                'div.bigPlayUI').send_keys(Keys.ENTER)	
        except:
            try:
                driver.find_element_by_css_selector(
                    '[div^="bigPlayUI"]').click()
            except:
                try:
                    driver.execute_script(
                        "document.querySelector('div.bigPlayUI').click()")
                except:
                    pass


def quit_driver(driver, pluginfile):
    try:
        driver_list.remove(driver)
    except:
        pass
    driver.quit()

    try:
        os.remove(pluginfile)
    except:
        pass

    status = 400
    return status


def sleeping():
    sleep(5)


def main_viewer(proxy_type, proxy, position):
    try:
        global WIDTH
        global VIEWPORT

        detect_file_change()

        checked[position] = None

        header = Headers(
            browser="chrome",
            os=OSNAME,
            headers=False
        ).generate()
        agent = header['User-Agent']

        url = ''
        method = 1

        if method == 1:
            try:
                url = choice(urls)
                output = url
                youtube = 'Video'
            except:
                raise UrlsError

        if category == 'r' and proxy_api:
            proxies = scrape_api(link=proxy)
            proxy = choice(proxies)

        status = check_proxy(agent, proxy, proxy_type)

        if status == 200:
            try:
                print(timestamp() + bcolors.OKBLUE + f"Tried {position} | " + bcolors.OKGREEN +
                      f"{proxy} | {proxy_type} --> Good Proxy | Opening a new driver..." + bcolors.ENDC)

                create_html({"#3b8eea": f"Tried {position} | ",
                             "#23d18b": f"{proxy} | {proxy_type} --> Good Proxy | Opening a new driver..."})

                patched_driver = os.path.join(
                    'patched_drivers', f'chromedriver_{position%threads}{EXE_NAME}')

                try:
                    Patcher(executable_path=patched_driver).patch_exe()
                except:
                    pass

                pluginfile = os.path.join(
                    'extension', f'proxy_auth_plugin{position}.zip')

                factor = int(threads/6)
                sleep_time = int((str(position)[-1])) * factor
                sleep(sleep_time)

                driver = get_driver(patched_driver, agent,
                                    proxy, proxy_type, pluginfile)

                driver_list.append(driver)

                sleep(2)

                try:
                    proxy_dict = {
                        "http": f"{proxy_type}://{proxy}",
                        "https": f"{proxy_type}://{proxy}",
                    }
                    location = requests.get(
                        "http://ip-api.com/json", proxies=proxy_dict, timeout=30).json()
                    params = {
                        "latitude": location['lat'],
                        "longitude": location['lon'],
                        "accuracy": randint(20, 100)
                    }
                    driver.execute_cdp_cmd(
                        "Emulation.setGeolocationOverride", params)
                except:
                    pass

                referer = choice(REFERERS)
                if referer:
                    if method == 2 and 't.co/' in referer:
                        driver.get(url)
                    else:
                        driver.get(referer)
                        if 'consent.yahoo.com' in driver.current_url:
                            try:
                                consent = driver.find_element_by_xpath(
                                    "//button[@name='agree']")
                                driver.execute_script(
                                    "arguments[0].scrollIntoView();", consent)
                                consent.click()
                                driver.get(referer)
                            except:
                                pass
                        driver.execute_script(
                            "window.location.href = '{}';".format(url))
                else:
                    driver.get(url)

                if youtube == 'Video':

                    try:
                        WebDriverWait(driver, 5).until(EC.visibility_of_element_located(
                            (By.XPATH, '//div[@id="videoPlayer"]')))
                    except:
                        raise CaptchaError

                    play_video(driver)

                    view_stat = WebDriverWait(driver, 30).until(EC.visibility_of_element_located(
                        (By.XPATH, '//div[@class="media-by-wrap"]'))).text

                if WIDTH == 0:
                    WIDTH = driver.execute_script('return screen.width')
                    VIEWPORT = [i for i in VIEWPORT if int(i[:4]) <= WIDTH]

                if 'watching' in view_stat:
                    error = 0
                    while True:
                        view_stat = driver.find_element_by_xpath(
                            '//div[@class="media-by-wrap"]').text
                        if 'watching' in view_stat:
                            print(timestamp() + bcolors.OKBLUE + f"Tried {position} | " + bcolors.OKGREEN +
                                  f"{proxy} | {output} | " + bcolors.OKCYAN + f"{view_stat} " + bcolors.ENDC)

                            create_html({"#3b8eea": f"Tried {position} | ",
                                         "#23d18b": f"{proxy} | {output} | ", "#29b2d3": f"{view_stat} "})
                        else:
                            error += 1

                        play_video(driver)

                        if error == 5:
                            break
                        sleep(60)

                else:
                    current_url = driver.current_url
                    play_video(driver)
                    sleep(300)

                view.append(position)

                view_count = len(view)
                print(timestamp() + bcolors.OKCYAN +
                      f'View added : {view_count}' + bcolors.ENDC)

                create_html({"#29b2d3": f'View added : {view_count}'})

                if database:
                    try:
                        update_database()
                    except:
                        pass

                status = quit_driver(driver, pluginfile)

            except CaptchaError:
                print(timestamp() + bcolors.FAIL +
                      f"Tried {position} | Slow internet speed or Stuck at recaptcha! Can't load YouTube..." + bcolors.ENDC)

                create_html(
                    {"#f14c4c": f"Tried {position} | Slow internet speed or Stuck at recaptcha! Can't load YouTube..."})

                status = quit_driver(driver, pluginfile)
                pass

            except Exception as e:
                *_, exc_tb = sys.exc_info()
                print(timestamp() + bcolors.FAIL +
                      f"Tried {position} | Line : {exc_tb.tb_lineno} | " + str(e) + bcolors.ENDC)

                create_html(
                    {"#f14c4c": f"Tried {position} | Line : {exc_tb.tb_lineno} | " + str(e)})

                status = quit_driver(driver, pluginfile)
                pass

    except UrlsError:
        print(timestamp() + bcolors.FAIL +
              f"Tried {position} | Your url.txt is empty!" + bcolors.ENDC)

        create_html(
            {"#f14c4c": f"Tried {position} | Your url.txt is empty!"})
        pass

    except:
        print(timestamp() + bcolors.OKBLUE + f"Tried {position} | " +
              bcolors.FAIL + f"{proxy} | {proxy_type} --> Bad proxy " + bcolors.ENDC)

        create_html({"#3b8eea": f"Tried {position} | ",
                     "#f14c4c": f"{proxy} | {proxy_type} --> Bad proxy "})

        checked[position] = proxy_type
        pass


def stop_server(immediate=False):
    global server_running

    if api and server_running:
        print('Trying to stop the server')
        if not immediate:
            while 'state=running' in str(futures[1:-1]):
                sleep(5)

        server_running = False
        requests.post(f'http://127.0.0.1:{port}/shutdown')


def view_video(position):
    global server_running

    if position == 0:
        if api and not server_running:
            server_running = True
            website.start_server(host=host, port=port)

    elif position == total_proxies - 1:
        stop_server()

    else:
        proxy = proxy_list[position]

        if proxy_type:
            main_viewer(proxy_type, proxy, position)
        else:
            main_viewer('http', proxy, position)
            if checked[position] == 'http':
                main_viewer('socks4', proxy, position)
            if checked[position] == 'socks4':
                main_viewer('socks5', proxy, position)


def clean_exit(executor):
    executor.shutdown(wait=False)

    driver_list_ = list(driver_list)
    for driver in driver_list_:
        quit_driver(driver, None)

    while True:
        try:
            work_item = executor._work_queue.get_nowait()
        except queue.Empty:
            break

        if work_item is not None:
            work_item.future.cancel()


def main():
    global start_time
    global total_proxies
    global proxy_list
    global threads
    global futures

    start_time = time()
    threads = randint(min_threads, max_threads)
    if api:
        threads += 1

    pool_number = [i for i in range(total_proxies)]

    with ThreadPoolExecutor(max_workers=threads) as executor:
        futures = [executor.submit(view_video, position)
                   for position in pool_number]

        try:
            for future in as_completed(futures):

                if len(view) == views:
                    print(
                        bcolors.WARNING + f'Amount of views added : {views} | Stopping program...' + bcolors.ENDC)

                    clean_exit(executor)
                    stop_server()
                    break

                elif refresh != 0:

                    if (time() - start_time) > refresh*60:

                        if filename:
                            if proxy_api:
                                proxy_list = scrape_api(filename)
                            else:
                                proxy_list = load_proxy(filename)
                        else:
                            proxy_list = gather_proxy()

                        print(bcolors.WARNING +
                              f'Proxy reloaded from : {filename}' + bcolors.ENDC)

                        total_proxies = len(proxy_list)
                        print(bcolors.OKCYAN +
                              f'Total proxies : {total_proxies}' + bcolors.ENDC)

                        proxy_list.insert(0, 'dummy')
                        proxy_list.append('dummy')

                        total_proxies += 2

                        clean_exit(executor)
                        stop_server()
                        break

                future.result()

        except KeyboardInterrupt:
            clean_exit(executor)
            executor._threads.clear()
            concurrent.futures.thread._threads_queues.clear()
            stop_server(immediate=True)
            sys.exit()


if __name__ == '__main__':

    OSNAME, EXE_NAME = download_driver()
    create_database()
    urls = load_url()

    with open("url.txt", "rb") as f:
        hash_urls = hashlib.md5(f.read()).hexdigest()

    if os.path.isfile('config.json'):
        with open('config.json', 'r') as openfile:
            config = json.load(openfile)

        if len(config) == 11:
            print(json.dumps(config, indent=4))
            previous = str(input(
                bcolors.OKBLUE + 'Config file exists! Do you want to continue with previous saved preferences ? [Yes/No] : ' + bcolors.ENDC)).lower()
            if previous == 'n' or previous == 'no':
                create_config()
            else:
                pass
        else:
            print(bcolors.FAIL + 'Previous config file is not compatible with the latest script! Create a new one...' + bcolors.ENDC)
            create_config()
    else:
        create_config()

    with open('config.json', 'r') as openfile:
        config = json.load(openfile)

    api = config["http_api"]["enabled"]
    host = config["http_api"]["host"]
    port = config["http_api"]["port"]
    database = config["database"]
    views = config["views"]
    minimum = config["minimum"] / 100
    maximum = config["maximum"] / 100
    category = config["proxy"]["category"]
    proxy_type = config["proxy"]["proxy_type"]
    filename = config["proxy"]["filename"]
    auth_required = config["proxy"]["authentication"]
    proxy_api = config["proxy"]["proxy_api"]
    refresh = config["proxy"]["refresh"]
    background = config["background"]
    max_threads = config["max_threads"]
    min_threads = config["min_threads"]

    if auth_required and background:
        print(bcolors.FAIL +
              "Premium proxy needs extension to work. Chrome doesn't support extension in Headless mode." + bcolors.ENDC)
        input(bcolors.WARNING +
              f"Either use proxy without username & password or disable headless mode " + bcolors.ENDC)
        sys.exit()

    copy_drivers(max_threads)

    if filename:
        if category == 'r':
            proxy_list = [filename]
            proxy_list = proxy_list * 1000
        else:
            if proxy_api:
                proxy_list = scrape_api(filename)
            else:
                proxy_list = load_proxy(filename)

    else:
        proxy_list = gather_proxy()

    total_proxies = len(proxy_list)
    if category != 'r':
        print(bcolors.OKCYAN +
              f'Total proxies : {total_proxies}' + bcolors.ENDC)

    proxy_list.insert(0, 'dummy')
    proxy_list.append('dummy')

    total_proxies += 2

    check = -1
    while len(view) < views:
        try:
            check += 1
            if check == 0:
                main()
            else:
                sleeping()
                print(bcolors.WARNING +
                      f'Total Checked : {check} times' + bcolors.ENDC)
                main()
        except KeyboardInterrupt:
            sys.exit()
