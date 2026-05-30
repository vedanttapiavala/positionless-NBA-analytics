"""
Using the ten best features from 014_injury_prediction.ipynb to create an actual CatBoost model that can be 
used on the website
"""

import subprocess
import sys

def install_catboost():
    try:
        import catboost
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "catboost"])

import pandas as pd
install_catboost()
from catboost import CatBoostClassifier
from sklearn.impute import SimpleImputer

df = pd.read_parquet('data/Player-Games_Injuries_Travel_Bio.parquet')
top_ten_features = [
    'rolling_7g_three_pointers_attempted',
    'rolling_7g_rebounds',
    'rolling_7g_USG',
    'positionless_index',
    'rolling_7g_blocks',
    'winPercent_team',
    'rolling_7g_points_per36',
    'rolling_7g_minutes',
    'games_last_14d',
    'rolling_7g_assists_per36'
]

# Train on all of the data that we have

imputer = SimpleImputer()
X = df[top_ten_features]
X = imputer.fit_transform(X)
y = df['injury_within_14d'].values
model = CatBoostClassifier(
    iterations=500,
    learning_rate=0.05,
    depth=6,
    loss_function='Logloss',
    eval_metric='AUC',
    verbose=0,
    random_state=42
)

model.fit(X, y)
model.save_model("output/website-catboost-model.cbm")