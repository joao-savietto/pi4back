"""
Script to analyze temperature and humidity dataset statistics 
for anomaly detection model improvement.
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy import stats
import json

def load_and_preprocess_data(csv_path):
    """Load and preprocess the CSV data"""
    # Load data from CSV file (assuming it has temperature and humidity columns)
    df = pd.read_csv(csv_path)
    
    # Ensure required columns exist
    if 'temperature' not in df.columns or 'humidity' not in df.columns:
        raise ValueError("CSV must contain 'temperature' and 'humidity' columns")
    
    # Convert timestamp to datetime if it exists
    if 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('timestamp').reset_index(drop=True)
    
    return df

def calculate_dataset_statistics(df):
    """Calculate comprehensive statistics for dataset"""
    # Basic statistics
    temperature_stats = {
        'mean': float(df['temperature'].mean()),
        'std': float(df['temperature'].std()),
        'min': float(df['temperature'].min()),
        'max': float(df['temperature'].max()),
        'median': float(df['temperature'].median()),
        'q25': float(df['temperature'].quantile(0.25)),
        'q75': float(df['temperature'].quantile(0.75))
    }
    
    humidity_stats = {
        'mean': float(df['humidity'].mean()),
        'std': float(df['humidity'].std()),
        'min': float(df['humidity'].min()),
        'max': float(df['humidity'].max()),
        'median': float(df['humidity'].median()),
        'q25': float(df['humidity'].quantile(0.25)),
        'q75': float(df['humidity'].quantile(0.75))
    }
    
    # Distribution analysis
    temperature_skewness = float(stats.skew(df['temperature']))
    humidity_skewness = float(stats.skew(df['humidity']))
    
    return {
        'temperature': temperature_stats,
        'humidity': humidity_stats,
        'skewness': {
            'temperature': temperature_skewness,
            'humidity': humidity_skewness
        }
    }

def identify_normal_ranges(df):
    """Identify normal operating ranges for anomaly detection"""
    # Calculate 95% confidence intervals (±2 standard deviations)
    temp_mean = df['temperature'].mean()
    temp_std = df['temperature'].std()
    
    hum_mean = df['humidity'].mean()
    hum_std = df['humidity'].std()
    
    # Normal ranges based on statistical bounds
    normal_temp_range = [temp_mean - 2*temp_std, temp_mean + 2*temp_std]
    normal_hum_range = [hum_mean - 2*hum_std, hum_mean + 2*hum_std]
    
    return {
        'temperature': {
            'normal_min': float(normal_temp_range[0]),
            'normal_max': float(normal_temp_range[1]),
            'mean': float(temp_mean),
            'std': float(temp_std)
        },
        'humidity': {
            'normal_min': float(normal_hum_range[0]),
            'normal_max': float(normal_hum_range[1]),
            'mean': float(hum_mean),
            'std': float(hum_std)
        }
    }

def detect_outliers(df):
    """Detect and analyze outliers using IQR method"""
    # Using Interquartile Range (IQR) for outlier detection
    temp_q1 = df['temperature'].quantile(0.25)
    temp_q3 = df['temperature'].quantile(0.75)
    temp_iqr = temp_q3 - temp_q1
    temp_lower_bound = temp_q1 - 1.5 * temp_iqr
    temp_upper_bound = temp_q3 + 1.5 * temp_iqr
    
    hum_q1 = df['humidity'].quantile(0.25)
    hum_q3 = df['humidity'].quantile(0.75)
    hum_iqr = hum_q3 - hum_q1
    hum_lower_bound = hum_q1 - 1.5 * hum_iqr
    hum_upper_bound = hum_q3 + 1.5 * hum_iqr
    
    # Find outliers
    temp_outliers = df[(df['temperature'] < temp_lower_bound) | (df['temperature'] > temp_upper_bound)]
    hum_outliers = df[(df['humidity'] < hum_lower_bound) | (df['humidity'] > hum_upper_bound)]
    
    # Convert outlier samples to serializable format
    def make_serializable(df_subset):
        if len(df_subset) == 0:
            return []
        # Convert to dict and handle datetime serialization
        records = df_subset.to_dict('records')
        for record in records:
            for key, value in record.items():
                if isinstance(value, pd.Timestamp):
                    record[key] = str(value)
                elif pd.isna(value):
                    record[key] = None
        return records
    
    return {
        'temperature': {
            'count': len(temp_outliers),
            'bounds': [float(temp_lower_bound), float(temp_upper_bound)],
            'outlier_samples': make_serializable(temp_outliers)
        },
        'humidity': {
            'count': len(hum_outliers),
            'bounds': [float(hum_lower_bound), float(hum_upper_bound)],
            'outlier_samples': make_serializable(hum_outliers)
        }
    }

def generate_anomaly_profiles(df):
    """Generate statistical profiles for different types of anomalies"""
    # Create bins for temperature and humidity with safer approach
    try:
        # Safe binning with explicit bounds to avoid empty bins
        temp_min, temp_max = df['temperature'].min(), df['temperature'].max()
        hum_min, hum_max = df['humidity'].min(), df['humidity'].max()
        
        # Create more robust bins that guarantee non-empty groups
        if temp_max > temp_min:
            temp_bins = pd.cut(df['temperature'], 
                              bins=5, 
                              labels=['Very Low', 'Low', 'Normal', 'High', 'Very High'],
                              include_lowest=True)
        else:
            # Fallback for constant values
            temp_bins = pd.Series(['Normal'] * len(df))
            
        if hum_max > hum_min:
            hum_bins = pd.cut(df['humidity'], 
                             bins=5, 
                             labels=['Very Low', 'Low', 'Normal', 'High', 'Very High'],
                             include_lowest=True)
        else:
            # Fallback for constant values
            hum_bins = pd.Series(['Normal'] * len(df))
            
    except Exception as e:
        print(f"Error creating bins: {e}")
        # Default fallback
        temp_bins = pd.Series(['Normal'] * len(df))
        hum_bins = pd.Series(['Normal'] * len(df))

    # Group by bins to analyze patterns with explicit error handling
    try:
        # Use a simpler approach - manual grouping
        temperature_profiles = {}
        humidity_profiles = {}
        
        categories = ['Very Low', 'Low', 'Normal', 'High', 'Very High']
        
        for category in categories:
            temp_mask = (temp_bins == category) & (~df['temperature'].isna())
            hum_mask = (hum_bins == category) & (~df['humidity'].isna())
            
            if temp_mask.any():
                subset_temp = df[temp_mask]['temperature']
                temperature_profiles[category] = {
                    'mean': float(subset_temp.mean()),
                    'std': float(subset_temp.std()),
                    'count': int(len(subset_temp))
                }
                
            if hum_mask.any():
                subset_hum = df[hum_mask]['humidity']
                humidity_profiles[category] = {
                    'mean': float(subset_hum.mean()),
                    'std': float(subset_hum.std()),
                    'count': int(len(subset_hum))
                }
        
        return {
            'temperature_profiles': temperature_profiles,
            'humidity_profiles': humidity_profiles
        }
        
    except Exception as e:
        print(f"Error in generating profiles: {e}")
        # Return empty but structured results
        return {
            'temperature_profiles': {},
            'humidity_profiles': {}
        }

def analyze_dataset(csv_path):
    """Complete analysis of the dataset"""
    
    # Load and preprocess
    df = load_and_preprocess_data(csv_path)
    
    print("Dataset Analysis Report")
    print("=" * 50)
    print(f"Total measurements: {len(df)}")
    
    if 'timestamp' in df.columns:
        print(f"Time range: {df['timestamp'].min()} to {df['timestamp'].max()}")
    
    # Check for missing values
    print(f"\nMissing values:")
    print(df.isnull().sum())
    
    # Handle potential issues with data types
    try:
        df['temperature'] = pd.to_numeric(df['temperature'], errors='coerce')
        df['humidity'] = pd.to_numeric(df['humidity'], errors='coerce')
        
        # Drop rows with NaN values in critical columns
        original_count = len(df)
        df = df.dropna(subset=['temperature', 'humidity'])
        if len(df) < original_count:
            print(f"Warning: Removed {original_count - len(df)} rows with missing data")
            
    except Exception as e:
        print(f"Error handling data types: {e}")
    
    # Check for valid numeric ranges (remove extreme outliers that might be errors)
    try:
        temp_q1 = df['temperature'].quantile(0.25)
        temp_q3 = df['temperature'].quantile(0.75)
        temp_iqr = temp_q3 - temp_q1
        temp_lower_bound = temp_q1 - 1.5 * temp_iqr
        temp_upper_bound = temp_q3 + 1.5 * temp_iqr
        
        hum_q1 = df['humidity'].quantile(0.25)
        hum_q3 = df['humidity'].quantile(0.75)
        hum_iqr = hum_q3 - hum_q1
        hum_lower_bound = hum_q1 - 1.5 * hum_iqr
        hum_upper_bound = hum_q3 + 1.5 * hum_iqr
        
        # Filter out extreme outliers (but keep some context)
        initial_count = len(df)
        df = df[
            (df['temperature'] >= temp_lower_bound) & 
            (df['temperature'] <= temp_upper_bound) &
            (df['humidity'] >= hum_lower_bound) & 
            (df['humidity'] <= hum_upper_bound)
        ]
        
        if len(df) < initial_count:
            print(f"Warning: Removed {initial_count - len(df)} extreme outliers")
            
    except Exception as e:
        print(f"Error filtering outliers: {e}")
    
    # Calculate statistics
    stats = calculate_dataset_statistics(df)
    normal_ranges = identify_normal_ranges(df)
    outliers = detect_outliers(df)
    profiles = generate_anomaly_profiles(df)
    
    # Print results
    print("\nTemperature Statistics:")
    for key, value in stats['temperature'].items():
        if isinstance(value, float):
            print(f"  {key}: {value:.2f}")
        else:
            print(f"  {key}: {value}")
            
    print("\nHumidity Statistics:")
    for key, value in stats['humidity'].items():
        if isinstance(value, float):
            print(f"  {key}: {value:.2f}")
        else:
            print(f"  {key}: {value}")
    
    print(f"\nTemperature Skewness: {stats['skewness']['temperature']:.3f}")
    print(f"Humidity Skewness: {stats['skewness']['humidity']:.3f}")
    
    print("\nNormal Ranges (±2σ):")
    print(f"  Temperature: [{normal_ranges['temperature']['normal_min']:.2f}, {normal_ranges['temperature']['normal_max']:.2f}]")
    print(f"  Humidity: [{normal_ranges['humidity']['normal_min']:.2f}, {normal_ranges['humidity']['normal_max']:.2f}]")
    
    print("\nOutlier Analysis:")
    print(f"  Temperature outliers: {outliers['temperature']['count']}")
    print(f"  Humidity outliers: {outliers['humidity']['count']}")
    
    # Save analysis results
    analysis_results = {
        'dataset_info': {
            'total_measurements': len(df),
            'time_range': str(df['timestamp'].min()) + ' to ' + str(df['timestamp'].max()) if 'timestamp' in df.columns else 'N/A'
        },
        'statistics': stats,
        'normal_ranges': normal_ranges,
        'outliers': outliers,
        'profiles': profiles
    }
    
    # Add a check for datetime objects in the result before saving
    def make_all_serializable(obj):
        if isinstance(obj, dict):
            return {key: make_all_serializable(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [make_all_serializable(item) for item in obj]
        elif isinstance(obj, pd.Timestamp):
            return str(obj)
        elif isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        else:
            return obj
    
    # Make sure all objects are serializable
    serializable_results = make_all_serializable(analysis_results)
    
    with open('dataset_analysis.json', 'w') as f:
        json.dump(serializable_results, f, indent=2)
        
    print("\nAnalysis results saved to dataset_analysis.json")
    
    return analysis_results

# Run the analysis if this file is executed directly
if __name__ == "__main__":
    # Replace with your actual CSV path
    csv_file_path = "measurements.csv"  # Update this path
    
    try:
        results = analyze_dataset(csv_file_path)
        print("\nAnalysis completed successfully!")
    except Exception as e:
        print(f"Error during analysis: {e}")
        import traceback
        traceback.print_exc()