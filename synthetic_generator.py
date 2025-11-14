"""
Synthetic Data Generator for SECOM Dataset
Uses SDV (Synthetic Data Vault) library to generate synthetic manufacturing data
"""

import pandas as pd
import numpy as np
from pathlib import Path
from sdv.single_table import GaussianCopulaSynthesizer, CTGANSynthesizer
from sdv.metadata import SingleTableMetadata
import pickle
import time

class SyntheticDataGenerator:
    """Generate synthetic data using various methods"""
    
    def __init__(self, data_dir='data'):
        self.data_dir = Path(data_dir)
        self.synthetic_dir = self.data_dir / 'synthetic'
        self.synthetic_dir.mkdir(parents=True, exist_ok=True)
        
        self.real_data = None
        self.synthetic_data = None
        self.metadata = None
        self.synthesizer = None
        
    def load_real_data(self, features_path='data/raw/secom_features_clean.csv', 
                       labels_path='data/raw/secom_labels_clean.csv'):
        """Load cleaned real data"""
        try:
            X = pd.read_csv(features_path)
            y = pd.read_csv(labels_path)
            
            # Combine features and labels
            self.real_data = X.copy()
            self.real_data['target'] = y.values
            
            print(f"✓ Loaded real data: {self.real_data.shape}")
            print(f"  - Features: {len(X.columns)}")
            print(f"  - Target distribution: {self.real_data['target'].value_counts().to_dict()}")
            
            return True
            
        except Exception as e:
            print(f"✗ Error loading data: {e}")
            return False
    
    def prepare_metadata(self):
        """Prepare metadata for SDV"""
        if self.real_data is None:
            print("No data loaded. Call load_real_data() first.")
            return False
        
        # Create metadata
        self.metadata = SingleTableMetadata()
        self.metadata.detect_from_dataframe(self.real_data)
        
        # Ensure target is categorical
        self.metadata.update_column('target', sdtype='categorical')
        
        print("✓ Metadata prepared")
        return True
    
    def train_gaussian_copula(self, enforce_min_max=True):
        """
        Train Gaussian Copula synthesizer (fast, good for tabular data)
        
        Args:
            enforce_min_max: Whether to enforce min/max bounds
        """
        print("\n" + "="*60)
        print("Training Gaussian Copula Synthesizer")
        print("="*60)
        
        start_time = time.time()
        
        # Create synthesizer
        self.synthesizer = GaussianCopulaSynthesizer(
            metadata=self.metadata,
            enforce_min_max_values=enforce_min_max,
            default_distribution='norm'
        )
        
        # Train
        print("Training in progress...")
        self.synthesizer.fit(self.real_data)
        
        training_time = time.time() - start_time
        print(f"✓ Training completed in {training_time:.2f} seconds")
        
        return self.synthesizer
    
    def train_ctgan(self, epochs=300, batch_size=500):
        """
        Train CTGAN synthesizer (slower, can capture complex patterns)
        
        Args:
            epochs: Number of training epochs
            batch_size: Batch size for training
        """
        print("\n" + "="*60)
        print("Training CTGAN Synthesizer")
        print("="*60)
        print(f"Configuration: {epochs} epochs, batch size {batch_size}")
        print("Note: This may take 5-10 minutes...")
        
        start_time = time.time()
        
        # Create synthesizer
        self.synthesizer = CTGANSynthesizer(
            metadata=self.metadata,
            epochs=epochs,
            batch_size=batch_size,
            verbose=True
        )
        
        # Train
        print("Training in progress...")
        self.synthesizer.fit(self.real_data)
        
        training_time = time.time() - start_time
        print(f"✓ Training completed in {training_time:.2f} seconds")
        
        return self.synthesizer
    
    def generate_synthetic_data(self, n_samples=None, method='gaussian_copula'):
        """
        Generate synthetic data
        
        Args:
            n_samples: Number of samples to generate (None = same as real data)
            method: 'gaussian_copula' or 'ctgan'
        
        Returns:
            Synthetic dataframe
        """
        if n_samples is None:
            n_samples = len(self.real_data)
        
        print(f"\nGenerating {n_samples} synthetic samples...")
        
        # Train if not already trained
        if self.synthesizer is None:
            self.prepare_metadata()
            if method == 'gaussian_copula':
                self.train_gaussian_copula()
            elif method == 'ctgan':
                self.train_ctgan()
        
        # Generate synthetic data
        start_time = time.time()
        self.synthetic_data = self.synthesizer.sample(num_rows=n_samples)
        generation_time = time.time() - start_time
        
        print(f"✓ Generated {len(self.synthetic_data)} synthetic samples in {generation_time:.2f} seconds")
        print(f"  - Synthetic target distribution: {self.synthetic_data['target'].value_counts().to_dict()}")
        
        return self.synthetic_data
    
    def save_synthetic_data(self, filename='synthetic_secom.csv'):
        """Save synthetic data to disk"""
        if self.synthetic_data is None:
            print("No synthetic data generated. Call generate_synthetic_data() first.")
            return False
        
        try:
            # Separate features and labels
            X_synthetic = self.synthetic_data.drop(columns=['target'])
            y_synthetic = self.synthetic_data['target']
            
            # Save
            X_path = self.synthetic_dir / f'features_{filename}'
            y_path = self.synthetic_dir / f'labels_{filename}'
            
            X_synthetic.to_csv(X_path, index=False)
            y_synthetic.to_csv(y_path, index=False)
            
            print(f"✓ Saved synthetic data:")
            print(f"  - Features: {X_path}")
            print(f"  - Labels: {y_path}")
            
            # Save synthesizer
            model_path = self.synthetic_dir / f'synthesizer_{filename.replace(".csv", ".pkl")}'
            self.synthesizer.save(str(model_path))
            print(f"  - Model: {model_path}")
            
            return True
            
        except Exception as e:
            print(f"✗ Error saving synthetic data: {e}")
            return False
    
    def get_generation_info(self):
        """Get information about the synthetic data generation"""
        if self.synthetic_data is None:
            return None
        
        info = {
            'n_synthetic_samples': len(self.synthetic_data),
            'n_real_samples': len(self.real_data),
            'n_features': len(self.synthetic_data.columns) - 1,  # Exclude target
            'real_target_dist': self.real_data['target'].value_counts().to_dict(),
            'synthetic_target_dist': self.synthetic_data['target'].value_counts().to_dict(),
            'synthesizer_type': type(self.synthesizer).__name__
        }
        
        return info


def main():
    """Main function to generate synthetic SECOM data"""
    print("="*70)
    print("SECOM Synthetic Data Generator")
    print("="*70)
    
    # Initialize generator
    generator = SyntheticDataGenerator()
    
    # Load real data
    if not generator.load_real_data():
        print("Failed to load data. Please run data_loader.py first.")
        return
    
    # Prepare metadata
    generator.prepare_metadata()
    
    # Generate synthetic data using Gaussian Copula (faster for prototyping)
    print("\n" + "="*70)
    print("Method 1: Gaussian Copula (Recommended for prototype)")
    print("="*70)
    generator.generate_synthetic_data(method='gaussian_copula')
    generator.save_synthetic_data(filename='synthetic_secom_gaussian.csv')
    
    # Optionally generate using CTGAN (better quality, but slower)
    generate_ctgan = input("\nGenerate synthetic data using CTGAN? (slower but higher quality) [y/N]: ")
    
    if generate_ctgan.lower() == 'y':
        print("\n" + "="*70)
        print("Method 2: CTGAN")
        print("="*70)
        
        # Reset synthesizer
        generator.synthesizer = None
        generator.generate_synthetic_data(method='ctgan', epochs=100)  # Reduced epochs for speed
        generator.save_synthetic_data(filename='synthetic_secom_ctgan.csv')
    
    # Print summary
    info = generator.get_generation_info()
    if info:
        print("\n" + "="*70)
        print("Generation Summary")
        print("="*70)
        print(f"Synthesizer: {info['synthesizer_type']}")
        print(f"Real samples: {info['n_real_samples']}")
        print(f"Synthetic samples: {info['n_synthetic_samples']}")
        print(f"Features: {info['n_features']}")
        print(f"\nTarget Distribution:")
        print(f"  Real: {info['real_target_dist']}")
        print(f"  Synthetic: {info['synthetic_target_dist']}")
    
    print("\n" + "="*70)
    print("Synthetic data generation complete!")
    print("="*70)


if __name__ == "__main__":
    main()
