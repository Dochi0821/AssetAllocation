import pandas as pd
from alpha_vantage.timeseries import TimeSeries
from datetime import datetime
from flask import Flask, render_template, request

API_KEY = "SFHKOTAHS4UVVJEQ"

app = Flask(__name__)

def backtest(start_date, end_date, weights):
    ts = TimeSeries(key=API_KEY, output_format="pandas")
    spy_data, _ = ts.get_daily_adjusted('SPY', outputsize='full')
    bnd_data, _ = ts.get_daily_adjusted('BND', outputsize='full')

    # 인덱스를 오름차순으로 정렬
    spy_data = spy_data.sort_index(ascending=True)
    bnd_data = bnd_data.sort_index(ascending=True)

    spy_data = spy_data.loc[start_date:end_date]
    bnd_data = bnd_data.loc[start_date:end_date]

    spy_returns = spy_data['5. adjusted close'].pct_change().dropna()
    bnd_returns = bnd_data['5. adjusted close'].pct_change().dropna()

    portfolio_returns = (weights['SPY'] * spy_returns) + (weights['BND'] * bnd_returns)

    cumulative_returns = (1 + portfolio_returns).cumprod()
    total_return = cumulative_returns[-1] - 1
    annualized_return = (1 + total_return) ** (365 / len(portfolio_returns)) - 1

    return {"total_return": total_return, "annualized_return": annualized_return}

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        start_date = request.form["start_date"]
        end_date = request.form["end_date"]
        spy_weight = float(request.form["spy_weight"])
        bnd_weight = float(request.form["bnd_weight"])
        weights = {"SPY": spy_weight, "BND": bnd_weight}

        results = backtest(start_date, end_date, weights)
        return render_template("results.html", results=results)

    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)
