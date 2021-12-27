import json
import random
import re
import string
import time

import boto3

from seleniumwire import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


def main(event, context):
    """
    This function will update authentication headers for the API by running
    a headless Chromium session and pulling the correct values
    """

    confirmation_number = ''.join(random.choices(string.ascii_uppercase, k=6))
    first_name = ''.join(random.choices(string.ascii_lowercase, k=random.randrange(4, 10))).capitalize()
    last_name = ''.join(random.choices(string.ascii_lowercase, k=random.randrange(4, 10))).capitalize()

    options = Options()
    options.binary_location = '/opt/headless-chromium'
    options.headless = True
    options.add_argument('user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15) '
                         'AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.5 Safari/605.1.15')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-gpu-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument("--single-process")
    options.add_argument("--homedir=/tmp")
    options.add_argument('window-size=1920x1080')

    driver = webdriver.Chrome(
        "/opt/chromedriver",
        options=options,
        # fix issue if we don't have permissions for default storage location
        seleniumwire_options={'request_storage': 'memory'}
    )
    driver.scopes = ["page/check-in"]
    driver.get("https://mobile.southwest.com/check-in")

    # fill out the form once the form fields become available
    element = WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.NAME, "recordLocator")))
    element.send_keys(confirmation_number)

    WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.NAME, "firstName"))).send_keys(first_name)
    WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.NAME, "lastName"))).send_keys(last_name)

    element.submit()

    # give the form time to submit before checking headers
    time.sleep(10)

    headers = {}
    print(driver.requests[0].headers)

    for key, value in driver.requests[0].headers.items():
        if re.match(r"x-api-key|x-user-experience-id|x-channel-id|^[\w-]+?-\w$", key, re.I):
            headers[key] = value

    print(f"headers={headers})")

    if not headers:
        driver.quit()
        raise SystemExit("Failed to retrieve headers")

    ssm = boto3.client('ssm')
    ssm.put_parameter(
        Name='/southwest/headers',
        Value=json.dumps(headers),
        Type='String',
        Overwrite=True,
        # use Advanced tier because the headers can be > 4k
        Tier='Advanced'
    )

    driver.quit()
