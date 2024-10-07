import os
import io
import time
from twocaptcha import TwoCaptcha
import logging
from fake_useragent import UserAgent
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from PIL import Image
import tempfile
from selenium.webdriver.common.by import By
import random

# Configuração do logger
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

API_KEY = os.getenv('API_KEY')


def setup_options_browser():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument(f"user-agent={get_random_user_agent()}")
    return options


def get_random_user_agent():
    user_agent = UserAgent()
    return user_agent.random


def solve_captcha(image_path):
    solver = TwoCaptcha(API_KEY)
    try:
        result = solver.normal(image_path)
        return result['code']  # Retorna a solução do CAPTCHA
    except Exception as e:
        logging.info(f"Ocorreu um erro ao resolver o CAPTCHA: {e}")
        return None


def scrape_marketwatch_data(stock_symbol):
    options = setup_options_browser()
    driver = webdriver.Firefox(options=options)
    time.sleep(2)

    try:
        driver.get(f"https://www.marketwatch.com/investing/stock/{stock_symbol}")
        time.sleep(5)  # Esperar um pouco para garantir que a página carregue

        if "ct.captcha-delivery" in driver.page_source:
            logging.info("CAPTCHA detectado. Enviando para resolução.")
            screenshot = driver.get_screenshot_as_png()
            full_screenshot = Image.open(io.BytesIO(screenshot))

            # Criar um arquivo temporário para a imagem
            with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as temp_file:
                full_screenshot.save(temp_file, format='PNG')
                temp_file_path = temp_file.name

            # Resolver o CAPTCHA
            captcha_solution = solve_captcha(temp_file_path)
            if captcha_solution:
                logging.info(f"Solução do CAPTCHA: {captcha_solution}")
                iframe = WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located((By.TAG_NAME, "iframe"))
                )

                # Mudar o contexto para o iframe
                driver.switch_to.frame(iframe)
                # Encontrar o campo de entrada do CAPTCHA
                captcha_input = driver.find_element(By.XPATH, "//input[@type='text' or @name='captcha']")
                captcha_input.send_keys(captcha_solution)  # Inserir a solução do CAPTCHA

                # Encontrar o botão de envio e clicar
                submit_button = driver.find_element(By.XPATH, "//input[@type='submit' or @value='Submit']")
                submit_button.click()

                logging.info("Formulário de CAPTCHA enviado.")
                time.sleep(5)  # Esperar a página carregar após o envio do CAPTCHA

            else:
                logging.info("Falha ao resolver o CAPTCHA.")
        else:
            logging.info("Nenhum CAPTCHA detectado.")

        print(driver.page_source)  # Exibe o conteúdo da página

    except Exception as e:
        logging.info(f"Ocorreu um erro: {e}")
    finally:
        driver.quit()

