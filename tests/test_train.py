import pandas as pd
import trainers.train as train


def test_train_and_register_model(monkeypatch):
    df = pd.DataFrame({
        'temp': [20.0, 21.0, 22.0, 23.0],
        'humidity': [50, 55, 60, 65],
        'pressure': [1005, 1007, 1009, 1011],
        'wind_speed': [3.0, 4.0, 2.5, 1.2],
        'pm2_5': [12.0, 14.0, 15.0, 13.0],
        'pm10': [20.0, 25.0, 22.0, 21.0],
        'no2': [10.0, 11.0, 9.0, 8.0],
        'o3': [5.0, 6.0, 7.0, 8.0],
        'hour': [10, 11, 12, 13],
        'day': [1, 1, 1, 1],
        'month': [6, 6, 6, 6],
        'aqi': [2, 3, 2, 4],
    })

    monkeypatch.setattr(train, 'fetch_features_dataframe', lambda: df)
    monkeypatch.setattr(train.mlflow, 'set_experiment', lambda name: None)

    class DummyRunInfo:
        def __init__(self):
            self.run_id = 'test-run-id'

    class DummyRunContext:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        @property
        def info(self):
            return DummyRunInfo()

    def fake_start_run(run_name=None):
        return DummyRunContext()

    monkeypatch.setattr(train.mlflow, 'start_run', fake_start_run)
    monkeypatch.setattr(train.mlflow, 'log_param', lambda *args, **kwargs: None)
    monkeypatch.setattr(train.mlflow, 'log_metric', lambda *args, **kwargs: None)
    monkeypatch.setattr(train.mlflow.sklearn, 'log_model', lambda *args, **kwargs: None)
    monkeypatch.setattr(train, 'register_model', lambda run_id: {'registered': True})

    result = train.train_and_register_model()
    assert 'metrics' in result
    assert result['metrics']['mae'] >= 0
    assert result['run_id'] == 'test-run-id'
