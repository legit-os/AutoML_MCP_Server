import pandas as pd
from matplotlib.figure import Figure


def detect_type(obj):

    if isinstance(obj, pd.DataFrame):
        return "dataframe"

    if isinstance(obj, Figure):
        return "figure"

    if isinstance(obj, list):
        return "list"

    if isinstance(obj, dict):
        return "dict"

    if isinstance(obj, (int, float)):
        return "kpi"

    return None
