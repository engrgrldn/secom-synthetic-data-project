import pandas as pd
import numpy as np
from pathlib import Path

print("="*60)
print("SECOM Dataset Generator")
print("="*60)

# Create directories
print("\nCreating directories...")
Path("data/raw").mkdir(parents=True, exist_ok=True)
Path("data/synthetic").mkdir(parents=True, exist_ok=True)

# Generate sample SECOM data
print("Generating sample SECOM dataset...")
np.random.seed(42)

n_samples = 1567
n_features = 500

X = pd.DataFrame(
    np.random.randn(n_samples, n_features),
        columns=[f"feature_{i}" for i in range(n_features)]
        )
        
# Add missing values (5%)
mask = np.random.random((n_samples, n_features)) < 0.05
X = X.mask(mask)

# Create labels (6.6% failure rate)
y = pd.DataFrame({
    "target": np.random.choice([0, 1], n_samples, p=[0.934, 0.066])
    })
    
print(f" Dataset created")
print(f"  - Samples: {n_samples}")
print(f"  - Features: {n_features}")
print(f"  - Failures: {(y['target']==1).sum()} ({(y['target']==1).mean()*100:.1f}%)")
print(f"  - Missing values: {X.isnull().sum().sum()} ({(X.isnull().sum().sum()/(n_samples*n_features)*100):.1f}%)")

# Save files
print("\nSaving files...")
X.to_csv("data/raw/secom_features_clean.csv", index=False)
y.to_csv("data/raw/secom_labels_clean.csv", index=False)

print(" Saved: data/raw/secom_features_clean.csv")
print(" Saved: data/raw/secom_labels_clean.csv")
print("\n" + "="*60)
print("Data generation complete!")
print("="*60)
