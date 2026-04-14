import json
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.figure import Figure


def serialize_dataframe(df: pd.DataFrame, path: Path):

    data = {
        "columns": list(df.columns),
        "rows": df.to_dict(orient="records")
    }

    with open(path, "w") as f:
        json.dump(data, f)


def serialize_list(data, path: Path):

    with open(path, "w") as f:
        json.dump(data, f)


def serialize_dict(data, path: Path):

    with open(path, "w") as f:
        json.dump(data, f)


def serialize_number(num, path: Path):

    with open(path, "w") as f:
        json.dump({"value": num}, f)


def serialize_figure(fig: Figure, path: Path):

    fig.savefig(path)
    plt.close(fig)
