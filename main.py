from flask import Flask, request, jsonify
import pandas as pd
import yfinance as yf
from sqlalchemy import create_engine
import bt
import matplotlib.pyplot as plt
import io
import base64
from matplotlib.backends.backend_agg import FigureCanvas
import pymysql
from sqlalchemy import inspect

app = Flask(__name__)

# 사용자가 선택할 수 있는 ETF 티커들
AVAILABLE_TICKERS = {
    'SPY', 'IEV', 'EWJ', 'EEM', 'TLT', 'IEF', 'IYR', 'RWX', 'GLD', 'DBC',
    'QQQ', 'VT', 'VEU', 'EFA', 'VWO', 'IWD', 'AGG', 'SHY', 'SHV', 'BIL',
    'TIP', 'GSC', 'PDBC', 'VNQ', 'SCHH', 'REM'
}

# MySQL 연결 설정
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'passwd': 'sukjune990821!',
    'db': 'stock_db',
    'charset': 'utf8'
}

# SQLAlchemy 엔진 생성
engine = create_engine(f"mysql+pymysql://{DB_CONFIG['user']}:{DB_CONFIG['passwd']}@{DB_CONFIG['host']}/{DB_CONFIG['db']}")

engine.dispose()

@app.route('/backtest_static', methods=['POST'])
def backtest_static():
    data = request.json
    tickers = data.get('tickers', [])
    user_allocation = data.get('allocation', {})
    start_date = data.get('start_date')
    end_date = data.get('end_date')
    initial_capital = data.get('initial_capital', 100000)  # 초기 투자 금액
    rebalance_period = data.get('rebalance_period', 'M')  # 재배분 주기

    if not set(tickers).issubset(AVAILABLE_TICKERS):
        return jsonify({"error": "Invalid tickers selected"}), 400

    # 재배분 주기 설정
    if rebalance_period == 'M':
        rebalance_period_num = 1  # 월별
    elif rebalance_period == 'Q':
        rebalance_period_num = 3  # 분기별
    elif rebalance_period == 'Y':
        rebalance_period_num = 12  # 연별
    else:
        rebalance_period_num = 1  # 기본값은 월별

    all_data = {}
    for ticker in tickers:
        all_data[ticker] = pd.read_sql(f'select * from {ticker};', con=engine)

    price = pd.DataFrame(
        {tic: data['Adj Close']
         for tic, data in all_data.items()})
    price = price.fillna(method='ffill')

    strategy_static = bt.Strategy("User_Defined", [
        bt.algos.SelectAll(),
        bt.algos.WeighSpecified(**user_allocation),
        bt.algos.RunEveryNPeriods(n_periods=rebalance_period_num, offset=0),
        bt.algos.Rebalance()
    ])

    backtest_static = bt.Backtest(strategy_static, price, initial_capital=initial_capital)
    result_static = bt.run(backtest_static)

    fig, ax = plt.subplots()
    result_static.plot(ax=ax)
    buf = io.BytesIO()
    FigureCanvas(fig).print_png(buf)
    buf.seek(0)
    encoded_img = base64.b64encode(buf.getvalue()).decode('utf-8')
    plt.close(fig)

    return jsonify({
        "returns": result_static.stats['daily_mean'].round(4),
        "volatility": result_static.stats['daily_vol'].round(4),
        "sharpe": result_static.stats['daily_sharpe'].round(4),
        "graph": encoded_img
    })

@app.route('/backtest_dynamic', methods=['POST'])
def backtest_dynamic():
    data = request.json
    tickers = data.get('tickers', [])
    start_date = data.get('start_date')
    end_date = data.get('end_date')
    initial_capital = data.get('initial_capital', 100000)  # 초기 투자 금액
    rebalance_period = data.get('rebalance_period', 'M')  # 재배분 주기

    if not set(tickers).issubset(AVAILABLE_TICKERS):
        return jsonify({"error": "Invalid tickers selected"}), 400

    # 재배분 주기 설정
    if rebalance_period == 'M':
        rebalance_period_num = 1  # 월별
    elif rebalance_period == 'Q':
        rebalance_period_num = 3  # 분기별
    elif rebalance_period == 'Y':
        rebalance_period_num = 12  # 연별
    else:
        rebalance_period_num = 1  # 기본값은 월별

    all_data = {}
    for ticker in tickers:
        all_data[ticker] = pd.read_sql(f'select * from {ticker};', con=engine)

    price = pd.DataFrame(
        {tic: data['Adj Close']
         for tic, data in all_data.items()})
    price = price.fillna(method='ffill')

    momentum = price.pct_change(90)

    class WeighMomentum(bt.Algo):
        def __init__(self, momentum):
            self.momentum = momentum

        def __call__(self, target):
            if target.now in self.momentum.index:
                weights = self.momentum.loc[target.now]
                weights = weights.dropna()
                target.temp['weights'] = weights
            return True

    strategy_dynamic = bt.Strategy("Momentum", [
        bt.algos.SelectAll(),
        WeighMomentum(momentum),
        bt.algos.RunEveryNPeriods(n_periods=rebalance_period_num, offset=0),
        bt.algos.Rebalance()
    ])

    backtest_dynamic = bt.Backtest(strategy_dynamic, price, initial_capital=initial_capital)
    result_dynamic = bt.run(backtest_dynamic)

    fig, ax = plt.subplots()
    result_dynamic.plot(ax=ax)
    buf = io.BytesIO()
    FigureCanvas(fig).print_png(buf)
    buf.seek(0)
    encoded_img = base64.b64encode(buf.getvalue()).decode('utf-8')
    plt.close(fig)

    return jsonify({
        "returns": result_dynamic.stats['daily_mean'].round(4),
        "volatility": result_dynamic.stats['daily_vol'].round(4),
        "sharpe": result_dynamic.stats['daily_sharpe'].round(4),
        "graph": encoded_img
    })

if __name__ == '__main__':
    app.run(debug=True)