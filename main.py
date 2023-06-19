import pandas as pd
import yfinance as yf
import pymysql
from sqlalchemy import create_engine

con = pymysql.connect(
    user = 'root',
    passwd = 'sukjune990821!',
    host = '127.0.0.1',
    db = 'stock_db',
    charset = 'utf8'
)

mycursor = con.cursor()

tickers = {
    'SPY', # 미국 주식
    'IEV', # 유럽 주식
    'EWJ', # 일본 주식
    'EEM', # 이머징 주식
    'TLT', # 미국 장기채
    'IEF', # 미국 중기채
    'IYR', # 미국 리츠
    'RWX', # 글로벌 리츠
    'GLD', # 금
    'DBC' # 상품
}

all_data = {}
for ticker in tickers:
    all_data[ticker] = yf.download(ticker, start='1993-01-22')

prices = pd.DataFrame(
    {tic: data['Adj Close']
     for tic, data in all_data.items()})

prices = prices.fillna(method = 'ffill')

engine = create_engine('mysql+pymysql://root:sukjune990821!@127.0.0.1:3306/stock_db')
prices.to_sql(name='sample_etf', con=engine, index=True, if_exists='replace')
engine.dispose()

rets = prices.pct_change(1).dropna()

import matplotlib.pyplot as plt
import seaborn as sns

sns.heatmap(rets.corr().round(2), annot = True, annot_kws = {"size" : 16}, cmap='coolwarm')
plt.show()

