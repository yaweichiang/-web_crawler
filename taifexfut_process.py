import logging
from time import time, sleep
import requests
from bs4 import BeautifulSoup
from datetime import date, timedelta
from pprint import pprint
import os
import json
from logging import getLogger, handlers
from multiprocessing import Process

logger_p = logging.getLogger('logger_p')
logger_p.setLevel('DEBUG')
formatter = logging.Formatter('%(asctime)s - %(module)s - %(levelname)s - %(message)s')
file_handle = logging.FileHandler('log_p.log')
file_handle.setLevel('DEBUG')
file_handle.setFormatter(formatter)
stream_handle = logging.StreamHandler()
stream_handle.setLevel('ERROR')
stream_handle.setFormatter(formatter)
logger_p.addHandler(stream_handle)
logger_p.addHandler(file_handle)

def craw(date):
    url = 'https://www.taifex.com.tw/cht/3/futContractsDate'
    post_data = {
        'queryDate': date
    }
    # re = requests.get(f'{url}?{date.year}%2F{date.month}%2F{date.day}')
    re =requests.post(url, post_data)
    if re.status_code == requests.codes.ok:
        soup = BeautifulSoup(re.text, 'html.parser')
        tables = soup.find('table', attrs={'width': '920px'})  # class_='table_f'
        try:
            trs = tables.find_all('tr', class_='12bk')
        except AttributeError:
            logger_p.error(f'{date}沒有資料')
            return
        head = ['商品', '身份別', '交易多方口數', '交易多方金額', '交易空方口數', '交易空方金額', '交易多空淨口數', '交易多空淨額',
                '未平倉多方口數', '未平倉多方金額', '未平倉空方口數', '未平倉空方金額', '未平倉淨口數', '未平倉多空淨額']
        data = {}
        name = []
        tr_data = []
        for i in range(len(trs)):
            if i < 3:
                continue
            tr = trs[i].text.split()
            if tr[0] == '期貨小計':
                break
            elif i % 3 == 0:
                name = [tr[1]]
                tr_data = tr[1:3] + [int(d.replace(',', '')) for d in tr[3:]]
            else:
                tr_data = name + [tr[0]] + [int(d.replace(',', '')) for d in tr[1:]]

            product = tr_data[0]
            who = tr_data[1]
            price = {head[i]: tr_data[i] for i in range(2, len(head))}
            if product not in data:  # 商品不存在
                data[product] = {who: price}
            else:
                data[product][who] = price
        # pprint(data)
        path = os.path.join('datas', f'{date.replace("/","_")}.json')
        with open(path, 'w') as f:
            json.dump(data, f)
        logger_p.info(f'{date}有資料')
    else:
        logger_p.warning(f'{date}沒資料')


def main():
    processes = []
    mydate = date.today()
    while mydate >= (date.today() - timedelta(days=730)):

        process = Process(target=craw, args=[mydate.strftime("%Y/%m/%d")])
        process.start()
        processes.append(process)
        # craw(mydate.strftime("%Y/%m/%d"))
        sleep(0.5)
        mydate = mydate - timedelta(days=1)
    for process in processes:
        process.join()

if __name__ == '__main__':
    start_time = time()
    os.makedirs('datas', exist_ok=True)
    main()
    end_time = time()
    logger_p.info(f'執行耗時：{end_time - start_time}')