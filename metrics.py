import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

def plot_returns(returns, benchmark=None):
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
    returns.plot(label='Algorithm', color='blue')
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
