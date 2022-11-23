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
from browsermobproxy import Server
import time
import json
import re
import pandas as pd
import numpy as np

import logging

useragent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36"

from twocaptcha import TwoCaptcha
config = {
            'server':           '2captcha.com',
            'apiKey':           '',
            'defaultTimeout':    120,
            'recaptchaTimeout':  600,
            'pollingInterval':   10,
        }
solver = TwoCaptcha(**config)


def decode_wordstat(response_data, user_agent, key):
    key = user_agent[:25] + key
    res = ''
    for i, char in enumerate(response_data):
        decoded = chr(ord(char) ^ ord(key[i % len(key)]))
        res += decoded
    return res


def activate_and_login():
    server = Server('./browsermob-proxy-2.1.4/bin/browsermob-proxy')
    server.start()

    proxy = server.create_proxy()

    chrome_options = Options()
    chrome_options.add_argument('--ignore-certificate-errors')
    chrome_options.add_argument('--window-size=1920,2802')
    chrome_options.add_argument('--hide-scrollbars')
    chrome_options.add_argument('--proxy-server={0}'.format(proxy.proxy))
    chrome_options.binary_location = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    # chrome_options.binary_location = "/opt/homebrew/bin/chromedriver"
    browser = webdriver.Chrome(options=chrome_options)
    actions = ActionChains(browser)

    return proxy


def click(xpath):
    global browser, actions
    elem = browser.find_element(by='xpath', value=xpath)
    actions.move_to_element(elem)
    actions.click()
    actions.perform()
    return elem


def login_wordstat(user, pas):
    global browser, actions
    browser.get("https://wordstat.yandex.ru/")

    click("/html/body/div[1]/table/tbody/tr/td[6]/table/tbody/tr[1]/td[2]/a/span")

    WebDriverWait(browser, 10).until(
            EC.presence_of_element_located(('xpath', "//*[@id=\"b-domik_popup-username\"]"))  # wait until the lowest table is downloaded
        )

    elem = click("//*[@id=\"b-domik_popup-username\"]")

    for symbol in user:
        elem.send_keys(symbol)
        sleep(random()*0.6)



    elem = click("//*[@id=\"b-domik_popup-password\"]")

    for symbol in pas:
        elem.send_keys(symbol)
        sleep(random()*0.6)

    click("/html/body/form/table/tbody/tr[2]/td[2]/div/div[5]/span[1]/input")


def wait(xpath, max_wait=3):
    try:
        a = WebDriverWait(browser, max_wait).until(
                    EC.presence_of_element_located(('xpath', xpath))  # wait until the lowest table is downloaded
                )
        return a
    except TimeoutException:
        return None


def solver228():
    a = wait("//*[@id=\"root\"]/div/div/form/div[2]/div/div/div[1]")
    # click on checkbox
    if a:
        print("[solver] Click on checkbox")
        click("//*[@id=\"root\"]/div/div/form/div[2]/div/div/div[1]")

    # wait img
    a = wait("//*[@id=\"advanced-captcha-form\"]/div/div[1]/img")

    if a:
        print("[solver] Fetch img")
        img_elem = browser.find_element(by='xpath', value="//*[@id=\"advanced-captcha-form\"]/div/div[1]/img")

        url = img_elem.get_attribute('src')
        resp = requests.get(url)
        uid = re.findall(r'.*/[0-9]+/([0-9a-z_]+)', url)[0]

        with open(f'res/data/captcha/{uid}.png', 'wb') as f:
            f.write(resp.content)

        print(f"[solver] Send img: {uid}")
        _id = solver.send(file=f"res/data/captcha/{uid}.png")

        done = False
        code = ''
        while not done:
            try:
                code = solver.get_result(_id)
                done = True
            except:
                pass
            sleep(2)
        print(f"[solver] FUXK ME 228: {code}")

        WebDriverWait(browser, 3).until(
            EC.presence_of_element_located(('xpath', "/html/body/div[1]/div/div/form/div/div[2]/span/input"))
            # wait until the lowest table is downloaded
        )
        elem = click("/html/body/div[1]/div/div/form/div/div[2]/span/input")
        for symbol in code:
            elem.send_keys(symbol)
            sleep(random() * 0.15)
        print(f"[solver] entered code")

    WebDriverWait(browser, 1).until(
        EC.presence_of_element_located(('xpath', "//*[@id=\"advanced-captcha-form\"]/div/div[3]/button[3]"))
        # wait until the lowest table is downloaded
    )
    click("//*[@id=\"advanced-captcha-form\"]/div/div[3]/button[3]")
    print(f"[solver] SOLVED!")


def get(q, proxy, useragent, rec=0):
    if rec > 2:
        raise Exception("MOM GAY")
    global browser, actions
    browser.get("https://wordstat.yandex.ru/")

    click(
        "/html/body/div[1]/table/tbody/tr/td[4]/div/div/form/table/tbody/tr[2]/td[1]/table/tbody/tr/td[1]/ul/li[3]/label/input")

    elem = click("//*[@class=\"b-form-input__input\"]")
    try:
        for symbol in q:
            elem.send_keys(symbol)
            sleep(random() * 0.1)
    except StaleElementReferenceException:
        solver228()
        get(q, rec=rec + 1)

    proxy.new_har(options={
        'captureContent': True,
        'captureHeaders': True
    })

    click("/html/body/div[1]/table/tbody/tr/td[4]/div/div/form/table/tbody/tr[1]/td[2]/span/input")

    try:
        print("Wait for no res text")
        WebDriverWait(browser, 5).until(
            EC.presence_of_element_located(('xpath', "/html/body/div[2]/div/div/table/tbody/tr/td[4]/div/div/div"))
            # wait until the lowest table is downloaded
        )
        elem = browser.find_element(by='xpath', value="/html/body/div[2]/div/div/table/tbody/tr/td[4]/div/div/div")
        print(elem, elem.text)
        if 'нигде не встречается' in elem.text:
            return None
    except NoSuchElementException as e:
        print(e)
        pass
    except TimeoutException:
        print("Timeout waiting text")
        pass

    a = wait("//*[@id=\"root\"]/div/div/form/div[2]/div/div/div[1]", max_wait=0.2)
    if a:
        solver228()
        get(q, rec=rec + 1)

    WebDriverWait(browser, 10).until(
        EC.presence_of_element_located(('xpath', "/html/body/div[2]/div/div/div[3]/div[3]"))
        # wait until the lowest table is downloaded
    )
    sleep(0.5)
    result = proxy.har

    txt = None

    for entry in result['log']['entries']:
        request = entry['request']
        response = entry['response']

        # print(request)

        if '/stat/history' in request['url']:
            txt = response
            break
    dat = json.loads(txt['content']['text'])

    key = js2py.eval_js(dat['key'])
    return json.loads(unquote(decode_wordstat(dat['data'], useragent, key)))


if __name__ == '__main__':
    proxy = activate_and_login()
    user, pas = "@yandex.ru", ""
    login_wordstat(user, pas)

    d = pd.read_csv('queries.csv').drop(['Unnamed: 0'], axis=1)
    d_grouped = pd.DataFrame()
    col_first = list(d['brand_match'].value_counts().to_dict().keys())[6:]
    col_last = list(d['brand_match'].value_counts().to_dict().keys())[:6]

    for i in col_first:
        d_grouped = pd.concat([d_grouped, d[d['brand_match'] == i]])
    for i in col_last:
        d_grouped = pd.concat([d_grouped, d[d['brand_match'] == i]])

    d_grouped['parse_data'] = ''
    last_idx = 0
    for idx, row in d_grouped.iterrows():
        if idx < last_idx:
            continue
        data = get(row.KEYWORD)
        d_grouped.at[idx, 'ws'] = str(data)
        last_idx += 1
        sleep(random() * 1)
