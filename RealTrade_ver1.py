import threading
import pyupbit
import time
import queue
from collections import deque
import numpy as np
import pandas as pd

# 구매가 k-2 > k-1일 때, k-1의 시가와 k-1 저가 사이에 k 번째의 시가가 존재하면 k번째 가격에 구매
# 판매가 k-2 < k-1일 때, k-1의 시가와 k-1 고가 사이에 k 번째의 시가가 존재하면 k번째 가격에 판매

access = 'AyOvsN69OM6Fm5q0xloOUfOUF7JHZKwx24cGtd4C'
secret = 'jyI16WSDxxdoYQ4fEpCceUxjdjYlF9B26h4gVR4E'

class Consumer(threading.Thread):
    def __init__(self, q):
        super().__init__()
        self.q = q
        self.ticker = "KRW-DOGE"
    
        self.open = deque(maxlen=2)
        self.high = deque(maxlen=1)
        self.low  = deque(maxlen=1)

        df = pyupbit.get_ohlcv(self.ticker, interval = 'minute1', to = '20221231 22:00:00')
        self.open.extend(df['close'])
        self.high.extend(df['high'])
        self.low.extend(df['low'])

    def run(self):
        price = None
        high_price = None
        low_price = None

        hold_flag = False
        wait_flag = False
        
        upbit = pyupbit.Upbit(access, secret)
        print("autotrade start")
        cash = upbit.get_balance()
        print("보유현금: ", cash)

        while True:
            try:
                if not self.q.empty():
                    if price != None and high_price != None and low_price != None:
                    
                        self.open.append(price)
                        self.high.append(high_price)
                        self.low.append(low_price)
                    
                    price = self.q.get()
                    high_price = self.q.get()
                    low_price = self.q.get()
                    
                wait_flag = False

                if hold_flag == False and wait_flag == False and \
                self.open[0] >= self.open[1] and self.open[1] >= price and \
                price >= self.low[0]:
                    buy_volume = int(cash*0.9995 / price)
                    buy_price = upbit.buy_limit_order(self.ticker,price, buy_volume)
                    print("매수 주문", buy_price)
                    print(self.open[0], self.open[1], price, self.low[0])
                    time.sleep(61)
                    hold_flag = True
                
                if hold_flag == True:
                    uncomp = upbit.get_order(self.ticker)
                    if len(uncomp) == 0 and upbit.get_balance()<1:
                        print("매수완료", buy_price)
                        hold_flag = False
                        wait_flag = True
                
                if hold_flag == False and wait_flag == True and \
                self.open[0] <= self.open[1] and self.open[1] <= price and \
                price <= self.high[0] and self.low[0] != self.high[0]:
                    volume = upbit.get_balance(self.ticker)
                    result_sell = upbit.sell_limit_order(self.ticker, price, volume)
                    print("매도 주문", result_sell)
                    print(self.open[0], self.open[1], price, self.high[0])
                    time.sleep(61)
                    hold_flag = True
                

                if hold_flag == True:
                    uncomp = upbit.get_order(self.ticker)
                    if len(uncomp) == 0 and upbit.get_balance()>1:
                        cash = upbit.get_balance()
                        print("매도완료", cash)
                        hold_flag = False
                        wait_flag = False

            except:
                print("error")

            time.sleep(0.2)   

class Producer(threading.Thread):
    def __init__(self, q):
        super().__init__()
        self.q = q
    
    def run(self):
        while True:
            price = pyupbit.get_current_price("KRW-DOGE")
            df = pyupbit.get_ohlcv("KRW-DOGE", interval = 'minute1', to = '20221231 22:00:00')
            high_price = df.iloc[1][-2]
            low_price = df.iloc[2][-2]
            self.q.put(price)
            self.q.put(high_price)
            self.q.put(low_price)

            time.sleep(60)

q = queue.Queue()
Producer(q).start()
Consumer(q).start()
