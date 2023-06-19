import riskfolio as rp
import matplotlib.pyplot as plt
import seaborn as sns
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
port = rp.Portfolio(returns=rets)

method_mu = 'hist'
method_cov = 'hist'

port.assets_stats(method_mu=method_mu, method_cov=method_cov)

model = 'Classic' #역사적 데이터
rm = 'MV' #위험 측정 방법, MV는 표준편차
obj = 'Sharpe' #목적함수
hist = True #역사적 데이터 사용
rf = 0 #무위험 수익률
l = 0 #위험 회피 계수

w = port.optimization(model=model, rm=rm, obj=obj, rf=rf, l=l, hist=hist)
round(w,4)
points = 50
frontier = port.efficient_frontier(model=model, rm=rm, points=points, rf=rf, hist=hist)

label = 'Max Risk Adjusted Return Portfolio'
mu = port.mu
cov =port.cov
returns =port.returns
ax =rp.plot_frontier(w_frontier=frontier, mu=mu, cov=cov, returns=returns, rm=rm, rf=rf, alpha = 0.05, cmap='viridis', w=w,
                     label=label, marker='*', s=16, c='r', height = 6, width = 10, ax = None)
plt.show()
