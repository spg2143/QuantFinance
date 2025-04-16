import numpy as np
import pandas as pd

def check_return_cleanliness(returns):
    """Function to check the cleanliness of the returns.

    Args:
        returns (pd.Series): pandas return time series
    """
    
    # Check for missing values
    if returns.isnull().sum() > 0:
        raise ValueError('Returns contain missing values.')
        
    # Check for duplicate index
    if returns.index.duplicated().sum() > 0:
        raise ValueError('Returns contain duplicate index.')

    # check if index is sorted
    if not returns.index.is_monotonic_increasing:
        returns = returns.sort_index()
        print("Index is not sorted. Sorting the index.")
        return returns
    
    returns.index = pd.to_datetime(returns.index)
    return returns
    
def asset_score(returns, benchmark_returns=None, window=252):
    """This function calculates the asset score of the returns.

    Args:
        returns (pd.Series): pd.Series
        window (int): int

    Returns:
        pd.Series: pd.Series
    """
    
    # Check the cleanliness of the returns
    returns = check_return_cleanliness(returns)
    benchmark_returns = check_return_cleanliness(benchmark_returns)
    
    if benchmark_returns:    
       # Calculate the asset score
       pass