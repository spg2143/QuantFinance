import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

def plot_returns(returns, benchmark=None,  **kwargs):
    """
    Plots the cumulative returns of the algorithm against a benchmark.

    Parameters
    ----------
    returns : pd.Series
        The returns of the algorithm.
    benchmark : pd.Series, optional
        The returns of the benchmark.
    """
    # cumulative returns
    returns = (returns + 1).cumprod()

    plt.figure(figsize=(16, 8))
    returns.plot(label='Algorithm', **kwargs)
    if benchmark is not None:
        benchmark.plot(label='Benchmark', color='red')
    plt.legend()
    plt.ylabel('Cumulative returns')
    plt.show()

def value_at_risk(returns, confidence_level=0.95):
    """
    This function calculates the Value at Risk (VaR) of the returns.

    Args:
        returns (_type_): pd.Series
        confidence_level (float, optional):float. Defaults to 0.95.
    """
    
    # Calculate the VaR
    return np.percentile(returns, 100 * (1 - confidence_level))

def momentum_signal(returns):
    pass

def drawdown(returns):
    cum_ret = returns.add(1).cumprod()
    running_max = cum_ret.cummax()
    drawdown = (cum_ret - running_max) / running_max
    return drawdown

def max_drawdown(returns):
    return drawdown(returns).min()

def sharpe_ratio(returns, risk_free_rate=0):
    return (returns.mean() - risk_free_rate) / returns.std()

def sortino_ratio(returns, risk_free_rate=0):
    return (returns.mean() - risk_free_rate) / returns[returns < 0].std()