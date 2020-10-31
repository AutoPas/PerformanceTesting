import mongoengine as me
import pandas as pd

# Empty Commit List of Dicts
dummyOptions = []

COLORS = ["#f1a208", "#32639a", "#03cea4", "#fb4d3d", "#30bced", "#690375", "#e3ecf3"]
DYNAMIC_OPTIONS = ['Container', 'Traversal', 'LoadEstimator', 'DataLayout', 'Newton3', 'CellSizeFactor']


def aggregate_results(results: me.QuerySet) -> pd.DataFrame:
    """
    Aggregate Results into pandas Dataframe
    Args:
        results: queryset

    Returns:
        df: Dataframe
    """

    temp_dict = {}

    for i, r in enumerate(results):
        data = r.__dict__
        data['minTime'] = r.minTime
        temp_dict[i] = data

    df = pd.DataFrame.from_dict(temp_dict)
    try:
        df = df.drop(['_cls', '_dynamic_lock', '_fields_ordered'])
    except KeyError:
        pass
    df = df.transpose()
    return df
