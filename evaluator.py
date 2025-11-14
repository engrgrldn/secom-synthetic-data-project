"""
Evaluator for Synthetic Data Quality
Compares real and synthetic data using statistical tests and ML efficacy
"""

import pandas as pd
import numpy as np
from pathlib import Path
from scipy import stats
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, f1_score, roc_auc_score, confusion_matrix
from sklearn.preprocessing import StandardScaler
import pickle
import json

class SyntheticDataEvaluator:
    """Evaluate quality of synthetic data"""
    
    def __init__(self):
        self.real_data = None
        self.synthetic_data = None
        self.evaluation_results = {}
        
    def load_data(self, real_features_path, real_labels_path, 
                  synthetic_features_path, synthetic_labels_path):
        """Load real and synthetic data"""
        try:
            # Load real data
            X_real = pd.read_csv(real_features_path)
            y_real = pd.read_csv(real_labels_path)
            self.real_data = X_real.copy()
            self.real_data['target'] = y_real.values
            
            # Load synthetic data
            X_synthetic = pd.read_csv(synthetic_features_path)
            y_synthetic = pd.read_csv(synthetic_labels_path)
            self.synthetic_data = X_synthetic.copy()
            self.synthetic_data['target'] = y_synthetic.values
            
            print(f"✓ Loaded data for evaluation")
            print(f"  Real: {self.real_data.shape}")
            print(f"  Synthetic: {self.synthetic_data.shape}")
            
            return True
            
        except Exception as e:
            print(f"✗ Error loading data: {e}")
            return False
    
    def statistical_similarity(self):
        """
        Test statistical similarity between real and synthetic data
        Uses Kolmogorov-Smirnov test
        """
        print("\n" + "="*60)
        print("1. Statistical Similarity Tests")
        print("="*60)
        
        results = {}
        feature_cols = [col for col in self.real_data.columns if col != 'target']
        
        ks_pvalues = []
        similar_features = 0
        
        for col in feature_cols:
            # KS test
            ks_stat, ks_pval = stats.ks_2samp(
                self.real_data[col].dropna(),
                self.synthetic_data[col].dropna()
            )
            ks_pvalues.append(ks_pval)
            
            # Consider similar if p > 0.05
            if ks_pval > 0.05:
                similar_features += 1
        
        results['ks_pvalues'] = ks_pvalues
        results['mean_ks_pvalue'] = np.mean(ks_pvalues)
        results['median_ks_pvalue'] = np.median(ks_pvalues)
        results['pct_similar_features'] = (similar_features / len(feature_cols)) * 100
        
        print(f"Kolmogorov-Smirnov Test:")
        print(f"  Mean p-value: {results['mean_ks_pvalue']:.4f}")
        print(f"  Median p-value: {results['median_ks_pvalue']:.4f}")
        print(f"  Features statistically similar (p>0.05): {similar_features}/{len(feature_cols)} ({results['pct_similar_features']:.1f}%)")
        
        self.evaluation_results['statistical_similarity'] = results
        return results
    
    def correlation_preservation(self):
        """
        Test if correlation structure is preserved
        """
        print("\n" + "="*60)
        print("2. Correlation Structure Preservation")
        print("="*60)
        
        feature_cols = [col for col in self.real_data.columns if col != 'target']
        
        # Calculate correlation matrices
        real_corr = self.real_data[feature_cols].corr()
        synthetic_corr = self.synthetic_data[feature_cols].corr()
        
        # Flatten upper triangles
        real_corr_flat = real_corr.values[np.triu_indices_from(real_corr.values, k=1)]
        synthetic_corr_flat = synthetic_corr.values[np.triu_indices_from(synthetic_corr.values, k=1)]
        
        # Calculate correlation between correlations
        corr_corr = np.corrcoef(real_corr_flat, synthetic_corr_flat)[0, 1]
        
        # R-squared
        r_squared = corr_corr ** 2
        
        results = {
            'correlation_of_correlations': corr_corr,
            'r_squared': r_squared
        }
        
        print(f"Correlation between real and synthetic correlation matrices:")
        print(f"  Correlation: {corr_corr:.4f}")
        print(f"  R²: {r_squared:.4f}")
        
        if r_squared > 0.9:
            print(f"  ✓ Excellent correlation preservation")
        elif r_squared > 0.7:
            print(f"  ✓ Good correlation preservation")
        else:
            print(f"  ⚠ Moderate correlation preservation")
        
        self.evaluation_results['correlation_preservation'] = results
        return results
    
    def privacy_metrics(self):
        """
        Calculate privacy metrics
        - Distance to Closest Record (DCR)
        - Nearest neighbor distance ratio
        """
        print("\n" + "="*60)
        print("3. Privacy Preservation Metrics")
        print("="*60)
        
        feature_cols = [col for col in self.real_data.columns if col != 'target']
        
        # Standardize data for distance calculations
        scaler = StandardScaler()
        real_scaled = scaler.fit_transform(self.real_data[feature_cols])
        synthetic_scaled = scaler.transform(self.synthetic_data[feature_cols])
        
        # Calculate DCR for sample of synthetic records (computationally expensive for all)
        sample_size = min(100, len(self.synthetic_data))
        sample_indices = np.random.choice(len(self.synthetic_data), sample_size, replace=False)
        
        dcr_values = []
        for idx in sample_indices:
            synthetic_point = synthetic_scaled[idx]
            # Calculate distances to all real points
            distances = np.linalg.norm(real_scaled - synthetic_point, axis=1)
            min_distance = np.min(distances)
            dcr_values.append(min_distance)
        
        # Calculate statistics
        mean_dcr = np.mean(dcr_values)
        std_dcr = np.std(dcr_values)
        min_dcr = np.min(dcr_values)
        
        results = {
            'mean_dcr': mean_dcr,
            'std_dcr': std_dcr,
            'min_dcr': min_dcr,
            'mean_dcr_in_std_units': mean_dcr  # Already in standardized units
        }
        
        print(f"Distance to Closest Record (DCR):")
        print(f"  Mean: {mean_dcr:.4f} std units")
        print(f"  Std Dev: {std_dcr:.4f}")
        print(f"  Min: {min_dcr:.4f}")
        
        if mean_dcr > 2.0:
            print(f"  ✓ Excellent privacy - synthetic records are distant from real records")
        elif mean_dcr > 1.0:
            print(f"  ✓ Good privacy preservation")
        else:
            print(f"  ⚠ Some synthetic records may be too close to real records")
        
        self.evaluation_results['privacy_metrics'] = results
        return results
    
    def ml_efficacy(self):
        """
        Test ML efficacy - can models trained on synthetic data perform well?
        """
        print("\n" + "="*60)
        print("4. Machine Learning Efficacy")
        print("="*60)
        
        feature_cols = [col for col in self.real_data.columns if col != 'target']
        
        # Prepare data
        X_real = self.real_data[feature_cols]
        y_real = self.real_data['target']
        
        X_synthetic = self.synthetic_data[feature_cols]
        y_synthetic = self.synthetic_data['target']
        
        # Split real data for testing
        X_train_real, X_test_real, y_train_real, y_test_real = train_test_split(
            X_real, y_real, test_size=0.3, random_state=42, stratify=y_real
        )
        
        # Model 1: Trained on real data, tested on real data (baseline)
        print("\nScenario 1: Train on Real → Test on Real (Baseline)")
        model_real = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)
        model_real.fit(X_train_real, y_train_real)
        
        y_pred_real = model_real.predict(X_test_real)
        f1_real_real = f1_score(y_test_real, y_pred_real, average='weighted')
        
        try:
            auc_real_real = roc_auc_score(y_test_real, model_real.predict_proba(X_test_real)[:, 1])
        except:
            auc_real_real = None
        
        print(f"  F1-Score: {f1_real_real:.4f}")
        if auc_real_real:
            print(f"  AUC-ROC: {auc_real_real:.4f}")
        
        # Model 2: Trained on synthetic data, tested on real data
        print("\nScenario 2: Train on Synthetic → Test on Real (Key Test)")
        model_synthetic = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)
        model_synthetic.fit(X_synthetic, y_synthetic)
        
        y_pred_synthetic = model_synthetic.predict(X_test_real)
        f1_synthetic_real = f1_score(y_test_real, y_pred_synthetic, average='weighted')
        
        try:
            auc_synthetic_real = roc_auc_score(y_test_real, model_synthetic.predict_proba(X_test_real)[:, 1])
        except:
            auc_synthetic_real = None
        
        print(f"  F1-Score: {f1_synthetic_real:.4f}")
        if auc_synthetic_real:
            print(f"  AUC-ROC: {auc_synthetic_real:.4f}")
        
        # Calculate performance retention
        f1_retention = (f1_synthetic_real / f1_real_real) * 100
        
        print(f"\nPerformance Retention: {f1_retention:.1f}%")
        
        if f1_retention > 95:
            print(f"  ✓ Excellent - synthetic data nearly matches real data")
        elif f1_retention > 85:
            print(f"  ✓ Good - synthetic data maintains strong predictive value")
        elif f1_retention > 70:
            print(f"  ⚠ Acceptable - some degradation in performance")
        else:
            print(f"  ✗ Poor - significant performance loss")
        
        results = {
            'f1_real_real': f1_real_real,
            'f1_synthetic_real': f1_synthetic_real,
            'f1_retention_pct': f1_retention,
            'auc_real_real': auc_real_real,
            'auc_synthetic_real': auc_synthetic_real
        }
        
        self.evaluation_results['ml_efficacy'] = results
        return results
    
    def run_full_evaluation(self):
        """Run all evaluation metrics"""
        print("\n" + "="*70)
        print("COMPREHENSIVE SYNTHETIC DATA QUALITY EVALUATION")
        print("="*70)
        
        # Run all tests
        self.statistical_similarity()
        self.correlation_preservation()
        self.privacy_metrics()
        self.ml_efficacy()
        
        # Overall assessment
        print("\n" + "="*70)
        print("OVERALL ASSESSMENT")
        print("="*70)
        
        # Calculate overall score
        scores = []
        
        stat_sim = self.evaluation_results['statistical_similarity']['pct_similar_features']
        if stat_sim > 85:
            scores.append(('Statistical Similarity', '✓ Excellent', stat_sim))
        elif stat_sim > 70:
            scores.append(('Statistical Similarity', '✓ Good', stat_sim))
        else:
            scores.append(('Statistical Similarity', '⚠ Moderate', stat_sim))
        
        corr_pres = self.evaluation_results['correlation_preservation']['r_squared']
        if corr_pres > 0.9:
            scores.append(('Correlation Preservation', '✓ Excellent', corr_pres * 100))
        elif corr_pres > 0.7:
            scores.append(('Correlation Preservation', '✓ Good', corr_pres * 100))
        else:
            scores.append(('Correlation Preservation', '⚠ Moderate', corr_pres * 100))
        
        privacy = self.evaluation_results['privacy_metrics']['mean_dcr']
        if privacy > 2.0:
            scores.append(('Privacy Preservation', '✓ Excellent', privacy))
        elif privacy > 1.0:
            scores.append(('Privacy Preservation', '✓ Good', privacy))
        else:
            scores.append(('Privacy Preservation', '⚠ Moderate', privacy))
        
        ml_eff = self.evaluation_results['ml_efficacy']['f1_retention_pct']
        if ml_eff > 95:
            scores.append(('ML Efficacy', '✓ Excellent', ml_eff))
        elif ml_eff > 85:
            scores.append(('ML Efficacy', '✓ Good', ml_eff))
        else:
            scores.append(('ML Efficacy', '⚠ Acceptable', ml_eff))
        
        for metric, assessment, value in scores:
            print(f"{metric:.<30} {assessment}")
        
        return self.evaluation_results
    
    def save_results(self, output_path='results/metrics/evaluation_results.json'):
        """Save evaluation results to JSON"""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(self.evaluation_results, f, indent=2)
        
        print(f"\n✓ Evaluation results saved to {output_path}")


def main():
    """Main evaluation function"""
    print("="*70)
    print("SECOM Synthetic Data Evaluation")
    print("="*70)
    
    # Initialize evaluator
    evaluator = SyntheticDataEvaluator()
    
    # Load data
    success = evaluator.load_data(
        real_features_path='data/raw/secom_features_clean.csv',
        real_labels_path='data/raw/secom_labels_clean.csv',
        synthetic_features_path='data/synthetic/features_synthetic_secom_gaussian.csv',
        synthetic_labels_path='data/synthetic/labels_synthetic_secom_gaussian.csv'
    )
    
    if not success:
        print("\nFailed to load data. Please run data_loader.py and synthetic_generator.py first.")
        return
    
    # Run full evaluation
    results = evaluator.run_full_evaluation()
    
    # Save results
    evaluator.save_results()
    
    print("\n" + "="*70)
    print("Evaluation complete!")
    print("="*70)


if __name__ == "__main__":
    main()
