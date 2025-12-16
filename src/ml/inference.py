import joblib
import pandas as pd
import numpy as np
import os # Useful for path handling

# --- Configuration ---
MODEL_PATH = 'swap_price_predictor_rf.joblib'

# Initialize a global variable for the loaded model
loaded_pipeline = None

def load_model():
    """Loads the trained model pipeline into memory, checking for file existence."""
    global loaded_pipeline

    if loaded_pipeline is not None:
        return loaded_pipeline # Already loaded

    try:
        # Load the pipeline which handles both preprocessing and prediction
        loaded_pipeline = joblib.load(MODEL_PATH)
        print(f"Model successfully loaded from {MODEL_PATH}")
        return loaded_pipeline
    except FileNotFoundError:
        print(f"ERROR: Model file not found at {os.path.abspath(MODEL_PATH)}. Check your file path.")
        raise FileNotFoundError(f"Missing required model file: {MODEL_PATH}")

def predict_swap_price(benchmark_rate: float, maturity_years: int, market_volatility: float) -> float:
    """
    Predicts the swap fixed rate using the loaded model pipeline.

    NOTE: The backend engineer will call this function from their API route handler.
    """
    global loaded_pipeline

    # Ensure the model is loaded before predicting
    if loaded_pipeline is None:
    try:
        load_model()
    except FileNotFoundError:
        return np.nan # Or raise an appropriate error for the API

    # Create a DataFrame with the EXACT column names the model expects
    input_data = pd.DataFrame({
    'Benchmark_Rate': [benchmark_rate],
    'Maturity_Years': [maturity_years],
    'Market_Volatility': [market_volatility]
    })

    # Predict and return the single result
    predicted_rate = loaded_pipeline.predict(input_data)[0]

    # Return the rate, ensuring it's not negative
    return max(0.0001, predicted_rate)


# --- Example of running a prediction ---
if __name__ == '__main__':
    print("\n--- Testing Prediction Function ---")
    try:
        fixed_rate = predict_swap_price(
        benchmark_rate=0.03, # 3.0%
        maturity_years=10,
        market_volatility=0.012 # 1.2%
        )
        print(f"Predicted Rate: {fixed_rate*100:.4f}%")
    except RuntimeError as e:
        print(f"Test prediction failed (model loading error): {e}")