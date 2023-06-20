import bt
from sqlalchemy import create_engine
import pandas as pd
import matplotlib.pyplot as plt

engine = create_engine('mysql+pymysql://root:sukjune990821!@127.0.0.1:3306/stock_db')
price = pd.read_sql('select * from sample_etf;', con=engine)
price = price.set_index(['Date'])
engine.dispose()

data = price[['SPY', 'TLT','IEF','GLD', 'DBC']].dropna()

aw = bt.Strategy('All Weather',[
    bt.algos.SelectAll(),
    bt.algos.WeighSpecified(SPY=0.5, TLT=0.2, IEF =0.1, GLD = 0.1, DBC = 0.1),
    bt.algos.RunQuarterly(),
    bt.algos.Rebalance()
])
aw_backtest = bt.Backtest(aw, data)
aw_result = bt.run(aw_backtest)

aw_result.plot(figsize=(10,6), title='All Weather', legend=False)
plt.show()