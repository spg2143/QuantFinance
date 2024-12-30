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