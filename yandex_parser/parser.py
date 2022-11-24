import base64

import js2py
import requests
from urllib.parse import unquote
import json
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException, StaleElementReferenceException
from time import sleep
from random import random
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from browsermob_proxy_py.browsermobproxy import Server, Client
import time
import json
import re
import pandas as pd
import numpy as np
import logging
from twocaptcha import TwoCaptcha


class Parser:
    # useragent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36"

    @staticmethod
    def clear_sessions(url, session_id=None):
        """
        Here we query and delete orphan sessions
        docs: https://www.selenium.dev/documentation/grid/advanced_features/endpoints/
        :return: None
        """
        # url = "http://127.0.0.1:4444"
        if not session_id:
            # delete all sessions
            r = requests.get("{}/status".format(url))
            data = json.loads(r.text)
            for node in data['value']['nodes']:
                for slot in node['slots']:
                    if slot['session']:
                        id = slot['session']['sessionId']
                        r = requests.delete("{}/session/{}".format(url, id))
        else:
            # delete session from params
            r = requests.delete("{}/session/{}".format(url, session_id))

    @staticmethod
    def decode_wordstat(response_data, user_agent, key):
        key = user_agent[:25] + key
        res = ''
        for i, char in enumerate(response_data):
            decoded = chr(ord(char) ^ ord(key[i % len(key)]))
            res += decoded
        return res

    def close(self):
        logging.warn("CLOSING ALL!")
        self.proxy.close()
        self.browser.close()

    def __init__(self,
                 yandex_login,
                 yandex_pass,
                 webdriver_uri,
                 proxy_uri,
                 rucaptcha_key,
                 ):
        # server = Server(browsermob_path, options={"host": "0.0.0.0", "port": 7082})
        # server.start()
        self.clear_sessions(webdriver_uri)
        logging.info("[parser] Started browsermob")

        self.user = yandex_login
        self._pass = yandex_pass

        self.proxy = Client(proxy_uri)
        logging.warn(self.proxy.proxy)
        try:
            logging.warn(f"{proxy_uri}:{self.proxy.proxy.split(':')[1]}")

            chrome_options = Options()
            chrome_options.add_argument('--ignore-certificate-errors')
            chrome_options.add_argument('--window-size=1366,768')
            chrome_options.add_argument('--hide-scrollbars')
            # chrome_options.add_argument('--disable-dev-shm-usage')
            # chrome_options.add_argument('--no-sandbox')
            # chrome_options.add_argument('--headless')
            # chrome_options.add_argument(f'--user-agent="{self.useragent}"')
            chrome_options.add_argument('--proxy-server={0}'.format(f"http://{proxy_uri.split(':')[0]}:{self.proxy.proxy.split(':')[1]}"))

            self.browser = webdriver.Remote(webdriver_uri, options=chrome_options)
            self.actions = ActionChains(self.browser)

            logging.info("[parser] Started webdriver!")

            config = {
                'server': '2captcha.com',
                'apiKey': rucaptcha_key,
                'defaultTimeout': 120,
                'recaptchaTimeout': 600,
                'pollingInterval': 10,
            }

            self.solver = TwoCaptcha(**config)
            logging.info("[parser] Init done!")
        except KeyboardInterrupt as e:
            logging.info("CLOSE")
            self.proxy.close()
            self.browser.close()
            raise e

    def click(self, xpath):
        elem = self.browser.find_element(by='xpath', value=xpath)
        self.actions.move_to_element(elem)
        self.actions.click()
        self.actions.perform()
        return elem

    def login_wordstat(self):
        logging.info("[parser] Logging into wordstat...")
        self.browser.get("https://wordstat.yandex.ru/")

        self.click("/html/body/div[1]/table/tbody/tr/td[6]/table/tbody/tr[1]/td[2]/a/span")

        WebDriverWait(self.browser, 10).until(
            EC.presence_of_element_located(('xpath', "//*[@id=\"b-domik_popup-username\"]"))
            # wait until the lowest table is downloaded
        )
        logging.info("[parser] Got popup")

        elem = self.click("//*[@id=\"b-domik_popup-username\"]")

        for symbol in self.user:
            elem.send_keys(symbol)
            sleep(random() * 0.6)

        elem = self.click("//*[@id=\"b-domik_popup-password\"]")

        for symbol in self._pass:
            elem.send_keys(symbol)
            sleep(random() * 0.6)

        logging.info("[parser] Entered creds")

        self.click("/html/body/form/table/tbody/tr[2]/td[2]/div/div[5]/span[1]/input")
        logging.warn("[parser] Logged in!")

    def wait(self, xpath, max_wait=3):
        try:
            a = WebDriverWait(self.browser, max_wait).until(
                EC.presence_of_element_located(('xpath', xpath))  # wait until the lowest table is downloaded
            )
            return a
        except TimeoutException:
            return None

    def solver228(self):
        a = self.wait("//*[@id=\"root\"]/div/div/form/div[2]/div/div/div[1]")
        # click on checkbox
        if a:
            logging.info("[solver] Click on checkbox")
            self.click("//*[@id=\"root\"]/div/div/form/div[2]/div/div/div[1]")

        # wait img
        a = self.wait("//*[@id=\"advanced-captcha-form\"]/div/div[1]/img")

        if a:
            logging.info("[solver] Fetch img")
            img_elem = self.browser.find_element(by='xpath', value="//*[@id=\"advanced-captcha-form\"]/div/div[1]/img")

            url = img_elem.get_attribute('src')
            resp = requests.get(url)
            uid = re.findall(r'.*/[0-9]+/([0-9a-z_]+)', url)[0]

            with open(f'data/captcha/{uid}.png', 'wb') as f:
                f.write(resp.content)

            logging.info(f"[solver] Send img: {uid}")
            _id = self.solver.send(file=f"data/captcha/{uid}.png")

            done = False
            code = ''
            while not done: # FIXME
                try:
                    code = self.solver.get_result(_id)
                    done = True
                except:
                    pass
                sleep(2)
            logging.info(f"[solver] FUXK ME 228: {code}")

            WebDriverWait(self.browser, 3).until(
                EC.presence_of_element_located(('xpath', "/html/body/div[1]/div/div/form/div/div[2]/span/input"))
                # wait until the lowest table is downloaded
            )
            elem = self.click("/html/body/div[1]/div/div/form/div/div[2]/span/input")
            for symbol in code:
                elem.send_keys(symbol)
                sleep(random() * 0.15)
            logging.info(f"[solver] entered code")

        WebDriverWait(self.browser, 1).until(
            EC.presence_of_element_located(('xpath', "//*[@id=\"advanced-captcha-form\"]/div/div[3]/button[3]"))
            # wait until the lowest table is downloaded
        )
        self.click("//*[@id=\"advanced-captcha-form\"]/div/div[3]/button[3]")
        logging.info(f"[solver] SOLVED!")

    def get(self, q, rec=0):
        if rec > 2:
            raise Exception("MOM GAY")

        self.browser.get("https://wordstat.yandex.ru/")

        self.click(
            "/html/body/div[1]/table/tbody/tr/td[4]/div/div/form/table/tbody/tr[2]/td[1]/table/tbody/tr/td[1]/ul/li[3]/label/input")

        try:
            elem = self.click("//*[@class=\"b-form-input__input\"]")
            for symbol in q:
                elem.send_keys(symbol)
                sleep(random() * 0.1)
        except StaleElementReferenceException:
            self.solver228()
            self.get(q, rec=rec + 1)

        self.proxy.new_har(options={
            'captureContent': True,
            'captureHeaders': True
        })

        self.click("/html/body/div[1]/table/tbody/tr/td[4]/div/div/form/table/tbody/tr[1]/td[2]/span/input")

        try:
            logging.info("Wait for no res text")
            WebDriverWait(self.browser, 5).until(
                EC.presence_of_element_located(('xpath', "/html/body/div[2]/div/div/table/tbody/tr/td[4]/div/div/div"))
                # wait until the lowest table is downloaded
            )
            elem = self.browser.find_element(by='xpath', value="/html/body/div[2]/div/div/table/tbody/tr/td[4]/div/div/div")
            logging.info(elem, elem.text)
            if 'нигде не встречается' in elem.text:
                return None
        except NoSuchElementException as e:
            logging.info(e)
            pass
        except TimeoutException:
            logging.info("Timeout waiting text")
            pass

        a = self.wait("//*[@id=\"root\"]/div/div/form/div[2]/div/div/div[1]", max_wait=0.2)
        if a:
            self.solver228()
            self.get(q, rec=rec + 1)

        WebDriverWait(self.browser, 10).until(
            EC.presence_of_element_located(('xpath', "/html/body/div[2]/div/div/div[3]/div[3]"))
            # wait until the lowest table is downloaded
        )
        sleep(0.5)
        result = self.proxy.har

        txt = None
        req = None

        for entry in result['log']['entries']:
            request = entry['request']
            response = entry['response']

            # logging.info(request)

            if '/stat/history' in request['url']:
                txt = response
                req = request
                break
        dat = json.loads(txt['content']['text'])
        uagent = [e for e in req['headers'] if e['name'] == 'User-Agent'][0]['value']

        # print(str(base64.b64encode(bytes(dat['data'], 'utf-8'))))

        key = js2py.eval_js(dat['key'])
        # print(key)
        # print(uagent)
        # print(unquote(self.decode_wordstat(dat['data'], uagent, key)))
        # sleep(1000)
        return json.loads(unquote(self.decode_wordstat(dat['data'], uagent, key)))
