import bt
from sqlalchemy import create_engine
import pandas as pd
import matplotlib.pyplot as plt

engine = create_engine('mysql+pymysql://root:sukjune990821!@127.0.0.1:3306/stock_db')
price = pd.read_sql('select * from sample_etf;', con=engine)
price = price.set_index(['Date'])
engine.dispose()

strategy = bt.Strategy("Asset_Ew", [
    bt.algos.SelectAll(),
    bt.algos.WeighEqually(),
    bt.algos.RunMonthly(),
    bt.algos.Rebalance()
])

data = price.dropna()

backtest = bt.Backtest(strategy, data)
result = bt.run(backtest)

result['Asset_Ew'].plot()
result.prices.to_returns()
result.display()
plt.show()