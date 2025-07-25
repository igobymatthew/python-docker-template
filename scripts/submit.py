import os
import pandas as pd
from kaggle.api.kaggle_api_extended import KaggleApi


def submit(file_path: str, message: str = "Initial submission") -> None:
    api = KaggleApi()
    api.authenticate()
    api.competition_submit(
        competition="jigsaw-agile-community-rules",
        file_name=file_path,
        message=message,
    )

