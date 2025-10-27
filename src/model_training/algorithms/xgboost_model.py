import xgboost as xgb
import pandas as pd
from typing import Dict, Any

class XGBoostModel:
    def __init__(self, params: Dict[str, Any]):
        self.params = params
        self.model = None

    def train(self, X_train: pd.DataFrame, y_train: pd.Series):
        dtrain = xgb.DMatrix(X_train, label=y_train)
        self.model = xgb.train(self.params, dtrain, num_boost_round=self.params.get('num_boost_round', 100))
        return self.model

    def predict(self, X_test: pd.DataFrame) -> pd.Series:
        if not self.model:
            raise RuntimeError("Model not trained yet. Call train() first.")
        dtest = xgb.DMatrix(X_test)
        return pd.Series(self.model.predict(dtest), index=X_test.index)

    def save_model(self, path: str):
        if not self.model:
            raise RuntimeError("Model not trained yet. Cannot save.")
        self.model.save_model(path)

    def load_model(self, path: str):
        self.model = xgb.Booster()
        self.model.load_model(path)

    def get_feature_importance(self) -> Dict[str, float]:
        if not self.model:
            return {}
        return self.model.get_score(importance_type='weight')