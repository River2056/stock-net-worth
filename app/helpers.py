import requests
from bs4 import BeautifulSoup
import json
import time


def get_current_stock_info(stock):
    url = 'https://tw.stock.yahoo.com/q/q?s=' + stock
    res = requests.get(url)
    soup = BeautifulSoup(res.content, 'html.parser')
    # time.sleep(1)
    return soup


def get_current_stock_price(soup):
    current_price = float(soup.findAll('b')[1].get_text())
    return current_price


def get_stock_name(soup):
    td_tag = soup.find('td', {'width': 105})
    name_tag = td_tag.find('a')
    name = '{}-{}'.format(name_tag.get_text()[0:4], name_tag.get_text()[4:])
    return name


def get_trade_amount(soup):
    table_tag = soup.find('table', {'border': 2})
    tr_tags = table_tag.find_all('tr')
    th_head_tags = tr_tags[0].find_all('th', {'align': 'center'})
    td_tags = tr_tags[1].find_all('td', {'align': 'center'})
    return int(td_tags[6].get_text().replace(',', ''))


# 5MA突破20MA黃金交叉
def get_golden_cross_5MA_over_20MA():
    url = 'https://tw.screener.finance.yahoo.net/screener/ws?PickID=100205&PickCount=1700&f=j'
    list_req = requests.get(url)
    soup = BeautifulSoup(list_req.content, "html.parser")
    get_json = json.loads(soup.text)
    time.sleep(1)
    return get_json


# 5MA跌破20MA死亡交叉
def get_dead_cross_5MA_below_20MA():
    url = 'https://tw.screener.finance.yahoo.net/screener/ws?PickID=100209&PickCount=20&f=j&443'
    list_req = requests.get(url)
    soup = BeautifulSoup(list_req.content, "html.parser")
    get_json = json.loads(soup.text)
    time.sleep(1)
    return get_json


# 股本大於20億
def get_share_holding_amount_greater_than_2billion():
    url = 'https://tw.screener.finance.yahoo.net/screener/ws?PickID=100538,100539,100540,100541&f=j&796'
    list_req = requests.get(url)
    soup = BeautifulSoup(list_req.content, "html.parser")
    get_json = json.loads(soup.text)
    time.sleep(1)
    return get_json


def get_value_stocks_info():
    url = 'https://www.twse.com.tw/exchangeReport/BWIBBU_d?response=json&date=&selectType=&_=' + str(time.time())
    res = requests.get(url)
    soup = BeautifulSoup(res.text, 'html.parser')
    get_json = json.loads(soup.text)
    time.sleep(1)
    return get_json
