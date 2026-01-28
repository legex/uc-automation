"""
Utility functions for number processing.
"""
import pandas as pd

def batch_numbers_by_region(numbercsv):
    """
    Docstring for batch_numbers_by_region
    
    :param numbercsv: CSV file containing phone numbers and their associated regions.
    :return: Dictionary mapping regions to lists of phone numbers.
    """
    csv = pd.read_csv(numbercsv, dtype={'ContactNumber': str})
    number_by_region = {}
    for _, row in csv.iterrows():
        region = row['Country']
        number = "+"+row['ContactNumber']
        if region in number_by_region:
            number_by_region[region].append(number)
        else:
            number_by_region[region] = [number]
    return number_by_region
