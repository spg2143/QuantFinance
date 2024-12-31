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
    
def asset_score(returns, window):
    """This function calculates the asset score of the returns.

    Args:
        returns (pd.Series): pd.Series
        window (int): int

    Returns:
        pd.Series: pd.Series
    """
    
    # Check the cleanliness of the returns
    returns = check_return_cleanliness(returns)
    
    # Calculate the asset score
    
    ### TBD: Implement the asset score calculation
    asset_score = returns.rolling(window).mean() / returns.rolling(window).std()
    
    return asset_score