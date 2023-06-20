import bt
from sqlalchemy import create_engine
import pandas as pd
import matplotlib.pyplot as plt

engine = create_engine('mysql+pymysql://root:sukjune990821!@127.0.0.1:3306/stock_db')
price = pd.read_sql('select * from sample_etf;', con=engine)
price = price.set_index(['Date'])
engine.dispose()

data = price.dropna()

gdaa = bt.Strategy('GDAA', [
    bt.algos.SelectAll(),
    bt.algos.SelectMomentum(n=5, lookback=pd.DateOffset(years=1)),
    bt.algos.WeighERC(lookback=pd.DateOffset(years=1)),
    bt.algos.RunMonthly(),
    bt.algos.Rebalance()
])

gdaa_backtest = bt.Backtest(gdaa, data)
gdaa_result = bt.run(gdaa_backtest)
gdaa_result.plot()
plt.show()