import statsmodels.api as sm
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import roc_auc_score, average_precision_score

def convert_csv_parquet(filename, dtype_arr, usecols) -> None:
    df = pd.read_csv(f'{filename}.csv', dtype=dtype_arr,  usecols=usecols)

    df.to_parquet(f'{filename}.parquet', compression='snappy')

    df_parquet = pd.read_parquet(f'{filename}.parquet')

    assert df.shape == df_parquet.shape, 'Resulting Parquet Shape Not the Same'
    assert df.columns == df_parquet.columns, 'Different Number of Columns in Resulting Parquet'
    assert len(df) == len(df_parquet), 'Different Number of Rows in Resulting Parquet'

def test_model(df_model):
    assert 'gameDateTimeEst_player' in df_model.columns, 'Game Date/Time Not Found'
    assert 'injury_within_14d' in df_model.columns, 'Target Variable for Injury Not Found'
    
    train = df_model[df_model['gameDateTimeEst_player'] < '2023-10-01'].copy()
    test  = df_model[df_model['gameDateTimeEst_player'] >= '2023-10-01'].copy()

    train = train.drop(columns=['gameDateTimeEst_player'])
    test  = test.drop(columns=['gameDateTimeEst_player'])

    X_train = train.drop(columns=['injury_within_14d'])
    y_train = train['injury_within_14d']

    X_test = test.drop(columns=['injury_within_14d'])
    y_test = test['injury_within_14d']

    # -----------------------------
    # 1. Scale (fit ONLY on train)
    # -----------------------------
    scaler = StandardScaler()

    X_train_scaled = pd.DataFrame(
        scaler.fit_transform(X_train),
        columns=X_train.columns,
        index=X_train.index
    )

    X_test_scaled = pd.DataFrame(
        scaler.transform(X_test),
        columns=X_test.columns,
        index=X_test.index
    )

    # -----------------------------
    # 2. Logistic regression (statsmodels)
    # -----------------------------
    X_train_sm = sm.add_constant(X_train_scaled)

    model = sm.Logit(y_train, X_train_sm).fit(disp=0)

    # -----------------------------
    # 3. Predict
    # -----------------------------
    X_test_sm = sm.add_constant(X_test_scaled, has_constant='add')
    preds = model.predict(X_test_sm)

    auc = roc_auc_score(y_test, preds)
    ap = average_precision_score(y_test, preds)

    print("ROC-AUC:", auc)
    print("PR-AUC:", ap)

    # -----------------------------
    # 4. Forest plot data
    # -----------------------------
    params = model.params
    conf = model.conf_int()

    or_df = pd.DataFrame({
        "feature": params.index,
        "OR": np.exp(params.values),
        "lower": np.exp(conf[0].values),
        "upper": np.exp(conf[1].values)
    })

    or_df = or_df[or_df["feature"] != "const"].sort_values("OR")

    # -----------------------------
    # 5. Forest plot
    # -----------------------------
    plt.figure(figsize=(8, max(5, len(or_df) * 0.35)))

    plt.errorbar(
        or_df["OR"],
        or_df["feature"],
        xerr=[
            or_df["OR"] - or_df["lower"],
            or_df["upper"] - or_df["OR"]
        ],
        fmt="o"
    )

    plt.axvline(1, color="black", linestyle="--")
    plt.xlabel("Odds Ratio (standardized features)")
    plt.title("Injury Risk Forest Plot")
    plt.tight_layout()
    plt.show()

    return or_df, auc, ap