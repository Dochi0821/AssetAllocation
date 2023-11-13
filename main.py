from flask import Flask, request, jsonify
import pandas as pd
from sqlalchemy import create_engine
import bt
import matplotlib.pyplot as plt
import io
import base64
from matplotlib.backends.backend_agg import FigureCanvas
import matplotlib
matplotlib.use('Agg')

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

@app.route('/')
def index():
    return "Backtesting API!"

@app.route('/backtest/static', methods=['POST'])
def backtest_static():
    return backtest_static_logic(request.json)

@app.route('/backtest/dynamic', methods=['POST'])
def backtest_dynamic():
    data = request.json
    aaAssets = data.get('aaAssets', [])
    startDay = data.get('startDay')
    endDay = data.get('endDay')
    initialCash = data.get('initialCash', 100000)
    rebalancingPeriod = data.get('rebalancingPeriod')
    strategy_type = data.get('strategy_type')

    tickers = [asset['assetName'] for asset in aaAssets]

    if not set(tickers).issubset(AVAILABLE_TICKERS):
        return jsonify({"error": "Invalid tickers selected"}), 400

    if rebalancingPeriod == 'M':
        rebalance_period_num = 1  # 월별
    elif rebalancingPeriod == 'Q':
        rebalance_period_num = 3  # 분기별
    elif rebalancingPeriod == 'Y':
        rebalance_period_num = 12  # 연별
    else:
        rebalance_period_num = 1  # 기본값은 월별

    all_data = {}
    for ticker in tickers:
        df = pd.read_sql(f'select * from {ticker};', con=engine)
        df['Date'] = pd.to_datetime(df['Date'])  # 'Date' 컬럼을 datetime 타입으로 변환
        df = df.drop_duplicates(subset='Date', keep='last')  # 중복된 날짜 제거
        df.set_index('Date', inplace=True)  # 'Date' 컬럼을 인덱스로 설정
        all_data[ticker] = df

    price = pd.DataFrame(
        {tic: data['Adj Close']
         for tic, data in all_data.items()})
    price = price.fillna(method='ffill')

    if strategy_type == "rel":
        momentum = price.pct_change(252).tail(1).transpose()
        momentum = momentum.sort_values(by=momentum.columns[0], ascending=False)
        top_assets = momentum.head(len(tickers) // 2).index.tolist()

        strategy_dynamic = bt.Strategy("Relative_Momentum", [
            bt.algos.SelectThese(top_assets),
            bt.algos.WeighEqually(),
            bt.algos.RunEveryNPeriods(rebalance_period_num, offset=0),
            bt.algos.Rebalance()
        ])
    else:
        momentum = price.pct_change(252)
        strategy_dynamic = bt.Strategy("Absolute_Momentum", [
            bt.algos.SelectWhere(momentum > 0),
            bt.algos.WeighEqually(),
            bt.algos.RunEveryNPeriods(rebalance_period_num, offset=0),
            bt.algos.Rebalance()
        ])

    backtest_dynamic = bt.Backtest(strategy_dynamic, price, initial_capital=initialCash)
    result_dynamic = bt.run(backtest_dynamic)

    fig, ax = plt.subplots()
    result_dynamic.plot(ax=ax)
    buf = io.BytesIO()
    FigureCanvas(fig).print_png(buf)
    buf.seek(0)
    encoded_img = base64.b64encode(buf.getvalue()).decode('utf-8')
    plt.close(fig)

    # 전략 유형에 따라 다른 결과 반환
    if strategy_type == "rel":
        strategy_name = "Relative_Momentum"
    else:
        strategy_name = "Absolute_Momentum"

    return jsonify({
        "returns": result_dynamic.stats[strategy_name]['daily_mean'].round(4),
        "volatility": result_dynamic.stats[strategy_name]['daily_vol'].round(4),
        "sharpe": result_dynamic.stats[strategy_name]['daily_sharpe'].round(4),
        "graph": encoded_img
    })

def backtest_static_logic(data):
    aaAssets = data.get('aaAssets', [])
    startDay = data.get('startDay')
    endDay = data.get('endDay')
    initialCash = data.get('initialCash', 100000)  # 초기 투자 금액 설정
    rebalancingPeriod = data.get('rebalancingPeriod')

    # Extracting tickers and their respective allocations
    tickers = [asset['assetName'] for asset in aaAssets]
    allocations = {asset['assetName']: asset['rate'] for asset in aaAssets}

    if not set(tickers).issubset(AVAILABLE_TICKERS):
        return jsonify({"error": "Invalid tickers selected"}), 400

    # 재배분 주기 설정
    if rebalancingPeriod == 'M':
        rebalance_period_num = 1  # 월별
    elif rebalancingPeriod == 'Q':
        rebalance_period_num = 3  # 분기별
    elif rebalancingPeriod == 'Y':
        rebalance_period_num = 12  # 연별
    else:
        rebalance_period_num = 1  # 기본값은 월별

    all_data = {}
    for ticker in tickers:
        df = pd.read_sql(f'select * from {ticker};', con=engine)
        df['Date'] = pd.to_datetime(df['Date'])  # 'Date' 컬럼을 datetime 타입으로 변환
        df = df.drop_duplicates(subset='Date', keep='last')  # 중복된 날짜 제거
        df.set_index('Date', inplace=True)  # 'Date' 컬럼을 인덱스로 설정
        all_data[ticker] = df

    price = pd.DataFrame(
        {tic: data['Adj Close']
         for tic, data in all_data.items()})
    price = price.fillna(method='ffill')

    # NULL 값을 갖는 행을 찾아 해당 행에서 NULL 값을 갖는 티커의 가중치를 0으로 설정
    null_rows = price.isnull().any(axis=1)
    for idx, row in price[null_rows].iterrows():
        null_tickers = row.index[row.isnull()].tolist()
        for tic in null_tickers:
            allocations[tic] = 0.0

        # 나머지 티커의 가중치를 재조정하여 합계가 1이 되도록 함
        total_alloc = sum(allocations.values())
        for tic, alloc in allocations.items():
            allocations[tic] = alloc / total_alloc

    strategy_static = bt.Strategy("User_Defined", [
        bt.algos.SelectAll(),
        bt.algos.WeighSpecified(**allocations),
        bt.algos.RunEveryNPeriods(rebalance_period_num, offset=0),
        bt.algos.Rebalance()
    ])

    backtest_static = bt.Backtest(strategy_static, price, initial_capital=initialCash)
    result_static = bt.run(backtest_static)

    fig, ax = plt.subplots()
    result_static.plot(ax=ax)
    buf = io.BytesIO()
    FigureCanvas(fig).print_png(buf)
    buf.seek(0)
    encoded_img = base64.b64encode(buf.getvalue()).decode('utf-8')
    plt.close(fig)

    return jsonify({
        "returns": result_static.stats['User_Defined']['daily_mean'].round(4),
        "volatility": result_static.stats['User_Defined']['daily_vol'].round(4),
        "sharpe": result_static.stats['User_Defined']['daily_sharpe'].round(4),
        "graph": encoded_img
    })

if __name__ == '__main__':
    app.run(debug=True)