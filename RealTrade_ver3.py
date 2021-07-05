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
        self.ticker = "KRW-BTT"
    
        self.open = deque(maxlen=3)
        self.high = deque(maxlen=2)
        self.low  = deque(maxlen=2)

        df = pyupbit.get_ohlcv(self.ticker, interval = 'minute1', to = '20221231 22:00:00')
        self.open.extend(df['open'][ :-1])
        self.high.extend(df['high'][ :-1])
        self.low.extend(df['low'][ :-1])   
        print(self.open, self.high, self.low, df.iloc[-1])
                   
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
                    print(price)
                    high_price = self.q.get()
                    print(high_price)
                    low_price = self.q.get()
                    print(low_price)
                    
                wait_flag = False

                if hold_flag == False and wait_flag == False and \
                self.open[0] >= self.open[1] and self.open[1] > self.open[2] and \
                self.open[2] >= self.low[1]:
                    buy_volume = int(cash*0.9995 / self.open[2])
                    buy_price = upbit.buy_limit_order(self.ticker, self.open[2], buy_volume)
                    print("매수 주문", buy_price)
                    print(self.open[0], self.open[1], self.open[2], self.low[1])
                    time.sleep(60)
                    hold_flag = True
                
                if hold_flag == True:
                    uncomp = upbit.get_order(self.ticker)
                    if len(uncomp) == 0:
                        print("매수완료", buy_price)
                        hold_flag = False
                        wait_flag = True
                
                if hold_flag == False and wait_flag == True and \
                self.open[0] < self.open[1] and self.open[1] <= self.open[2] and \
                self.open[2] <= self.high[1]:
                    volume = upbit.get_balance(self.ticker)
                    result_sell = upbit.sell_limit_order(self.ticker, self.open[2], volume)
                    print("매도 주문", result_sell)
                    print(self.open[0], self.open[1], self.open[2], self.high[1])
                    time.sleep(1)
                    hold_flag = True
                

                if hold_flag == True:
                    uncomp = upbit.get_order(self.ticker)
                    if len(uncomp) == 0:
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
            df = pyupbit.get_ohlcv("KRW-BTT", interval = 'minute1', to = '20221231 22:00:00')
            print(df)
            price = df.iloc[-1][0]
            high_price = df.iloc[-2][1]
            low_price = df.iloc[-2][2]
            self.q.put(price)
            self.q.put(high_price)
            self.q.put(low_price)
            time.sleep(60)

q = queue.Queue()
Producer(q).start()
Consumer(q).start()
