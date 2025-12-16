from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score
import joblib

# --- 1. Separate Features (X) and Target (y) ---
X_train = train_data.drop('Swap_Fixed_Rate', axis=1)
y_train = train_data['Swap_Fixed_Rate']
X_test = test_data.drop('Swap_Fixed_Rate', axis=1)
y_test = test_data['Swap_Fixed_Rate']

# --- 2. Define Preprocessing Steps ---
numerical_features = ['Benchmark_Rate', 'Market_Volatility']
categorical_features = ['Maturity_Years']

preprocessor = ColumnTransformer(
transformers=[
('num', StandardScaler(), numerical_features),
# Use OneHotEncoder for the categorical Maturity_Years
('cat', OneHotEncoder(handle_unknown='ignore'), categorical_features)
],
remainder='drop'
)

model_filename = 'swap_price_predictor_rf.joblib'

rf_model = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)

pipeline = Pipeline(steps=[
('preprocessor', preprocessor),
('regressor', rf_model)
])


print("Starting training...")
pipeline.fit(X_train, y_train)
print("Training Complete.")


y_pred = pipeline.predict(X_test)
r2 = r2_score(y_test, y_pred)
print(f"Model R-squared on test data: {r2:.4f}")


joblib.dump(pipeline, model_filename)
print(f"Trained pipeline saved as: {model_filename}")