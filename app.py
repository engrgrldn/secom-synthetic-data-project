"""
Streamlit Dashboard for SECOM Synthetic Data Project
Interactive visualization and comparison tool
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
from pathlib import Path

# Page configuration
st.set_page_config(
    page_title="SECOM Synthetic Data Analysis",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Title and introduction
st.title("🏭 Synthetic Data for Semiconductor Manufacturing")
st.markdown("""
This dashboard demonstrates how synthetic data can enable AI development in semiconductor manufacturing 
while preserving trade secrets and competitive intelligence.
""")

# Sidebar
st.sidebar.header("Navigation")
page = st.sidebar.radio(
    "Select Page",
    ["Overview", "Data Comparison", "Quality Metrics", "Business Case"]
)

# Load data function
@st.cache_data
def load_data():
    """Load real and synthetic data"""
    try:
        # Real data
        X_real = pd.read_csv('data/raw/secom_features_clean.csv')
        y_real = pd.read_csv('data/raw/secom_labels_clean.csv')
        real_data = X_real.copy()
        real_data['target'] = y_real.values
        
        # Synthetic data
        X_synthetic = pd.read_csv('data/synthetic/features_synthetic_secom_gaussian.csv')
        y_synthetic = pd.read_csv('data/synthetic/labels_synthetic_secom_gaussian.csv')
        synthetic_data = X_synthetic.copy()
        synthetic_data['target'] = y_synthetic.values
        
        return real_data, synthetic_data, True
    except:
        return None, None, False

@st.cache_data
def load_evaluation_results():
    """Load evaluation results"""
    try:
        with open('results/metrics/evaluation_results.json', 'r') as f:
            return json.load(f)
    except:
        return None

# Load data
real_data, synthetic_data, data_loaded = load_data()
eval_results = load_evaluation_results()

# Overview Page
if page == "Overview":
    st.header("Project Overview")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 The Challenge")
        st.markdown("""
        Semiconductor manufacturers face a critical dilemma:
        
        - **Need AI/ML** for yield optimization and quality control
        - **Cannot share data** due to IP protection and competitive concerns
        - **Regulatory barriers** (GDPR, export controls)
        - **Limited cross-facility learning** due to data silos
        """)
        
        st.subheader("💡 The Solution")
        st.markdown("""
        **Synthetic data generation** enables:
        - Collaborative AI development without exposing sensitive data
        - Safe vendor partnerships and outsourcing
        - Cross-facility knowledge sharing
        - Compliance with data protection regulations
        """)
    
    with col2:
        st.subheader("🎯 Project Goals")
        st.markdown("""
        This project demonstrates:
        
        1. **Technical Feasibility**: Generate high-quality synthetic manufacturing data
        2. **Statistical Validity**: Preserve key statistical properties
        3. **Privacy Preservation**: Ensure no real data leakage
        4. **ML Efficacy**: Maintain predictive performance
        5. **Business Value**: Quantify ROI and implementation path
        """)
        
        if data_loaded:
            st.subheader("📈 Dataset Statistics")
            
            metrics_col1, metrics_col2, metrics_col3 = st.columns(3)
            
            with metrics_col1:
                st.metric("Real Samples", f"{len(real_data):,}")
                st.metric("Synthetic Samples", f"{len(synthetic_data):,}")
            
            with metrics_col2:
                st.metric("Features", f"{len(real_data.columns)-1}")
                failure_rate = (real_data['target'] == 1).mean() * 100
                st.metric("Failure Rate", f"{failure_rate:.1f}%")
            
            with metrics_col3:
                st.metric("Industry", "Semiconductor")
                st.metric("Use Case", "Yield Prediction")

# Data Comparison Page
elif page == "Data Comparison":
    st.header("Real vs Synthetic Data Comparison")
    
    if not data_loaded:
        st.error("⚠️ Data not loaded. Please run data_loader.py and synthetic_generator.py first.")
    else:
        # Feature selection
        feature_cols = [col for col in real_data.columns if col != 'target']
        selected_feature = st.selectbox("Select Feature to Compare", feature_cols)
        
        # Distribution comparison
        st.subheader(f"Distribution Comparison: {selected_feature}")
        
        fig = go.Figure()
        
        # Real data histogram
        fig.add_trace(go.Histogram(
            x=real_data[selected_feature],
            name="Real Data",
            opacity=0.7,
            marker_color='#1f77b4',
            nbinsx=50
        ))
        
        # Synthetic data histogram
        fig.add_trace(go.Histogram(
            x=synthetic_data[selected_feature],
            name="Synthetic Data",
            opacity=0.7,
            marker_color='#ff7f0e',
            nbinsx=50
        ))
        
        fig.update_layout(
            barmode='overlay',
            xaxis_title=selected_feature,
            yaxis_title="Frequency",
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Statistical comparison
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Real Data Statistics")
            real_stats = real_data[selected_feature].describe()
            st.dataframe(real_stats)
        
        with col2:
            st.subheader("Synthetic Data Statistics")
            synthetic_stats = synthetic_data[selected_feature].describe()
            st.dataframe(synthetic_stats)
        
        # Target distribution comparison
        st.subheader("Target Distribution Comparison")
        
        col1, col2 = st.columns(2)
        
        with col1:
            real_target_counts = real_data['target'].value_counts()
            fig_real = px.pie(
                values=real_target_counts.values,
                names=['Pass', 'Fail'],
                title="Real Data Target Distribution",
                color_discrete_sequence=['#2ecc71', '#e74c3c']
            )
            st.plotly_chart(fig_real, use_container_width=True)
        
        with col2:
            synthetic_target_counts = synthetic_data['target'].value_counts()
            fig_synthetic = px.pie(
                values=synthetic_target_counts.values,
                names=['Pass', 'Fail'],
                title="Synthetic Data Target Distribution",
                color_discrete_sequence=['#2ecc71', '#e74c3c']
            )
            st.plotly_chart(fig_synthetic, use_container_width=True)

# Quality Metrics Page
elif page == "Quality Metrics":
    st.header("Synthetic Data Quality Evaluation")
    
    if eval_results is None:
        st.warning("⚠️ Evaluation results not found. Please run evaluator.py first.")
        
        st.markdown("""
        ### Expected Quality Metrics
        
        When you run the evaluation, you'll see:
        
        1. **Statistical Similarity**: KS-test comparing distributions
        2. **Correlation Preservation**: How well relationships are maintained
        3. **Privacy Metrics**: Distance to closest record (DCR)
        4. **ML Efficacy**: Model performance retention
        """)
    else:
        # Create metrics dashboard
        st.subheader("📊 Quality Scorecard")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            stat_sim = eval_results['statistical_similarity']['pct_similar_features']
            st.metric(
                "Statistical Similarity",
                f"{stat_sim:.1f}%",
                help="% of features with similar distributions (KS test p>0.05)"
            )
        
        with col2:
            corr_pres = eval_results['correlation_preservation']['r_squared']
            st.metric(
                "Correlation R²",
                f"{corr_pres:.3f}",
                help="R² between real and synthetic correlation matrices"
            )
        
        with col3:
            privacy = eval_results['privacy_metrics']['mean_dcr']
            st.metric(
                "Privacy (DCR)",
                f"{privacy:.2f}σ",
                help="Mean distance to closest real record (in std units)"
            )
        
        with col4:
            ml_eff = eval_results['ml_efficacy']['f1_retention_pct']
            st.metric(
                "ML Efficacy",
                f"{ml_eff:.1f}%",
                help="% of ML performance retained"
            )
        
        # Detailed results
        st.subheader("📈 Detailed Results")
        
        tab1, tab2, tab3, tab4 = st.tabs([
            "Statistical Similarity",
            "Correlation",
            "Privacy",
            "ML Performance"
        ])
        
        with tab1:
            st.markdown("### Kolmogorov-Smirnov Test Results")
            st.markdown("""
            The KS test compares the distribution of each feature between real and synthetic data.
            A p-value > 0.05 indicates the distributions are statistically similar.
            """)
            
            ks_pvalues = eval_results['statistical_similarity']['ks_pvalues']
            
            fig = go.Figure()
            fig.add_trace(go.Histogram(
                x=ks_pvalues,
                nbinsx=50,
                marker_color='#3498db'
            ))
            fig.add_vline(x=0.05, line_dash="dash", line_color="red",
                         annotation_text="Significance threshold (p=0.05)")
            fig.update_layout(
                xaxis_title="P-value",
                yaxis_title="Number of Features",
                height=400
            )
            st.plotly_chart(fig, use_container_width=True)
            
            st.info(f"✓ {stat_sim:.1f}% of features pass the similarity test (p > 0.05)")
        
        with tab2:
            st.markdown("### Correlation Structure Preservation")
            st.markdown("""
            This metric measures how well the relationships between features are preserved
            in the synthetic data compared to the real data.
            """)
            
            corr_value = eval_results['correlation_preservation']['correlation_of_correlations']
            r_squared = eval_results['correlation_preservation']['r_squared']
            
            st.metric("Correlation of Correlations", f"{corr_value:.4f}")
            st.metric("R² Score", f"{r_squared:.4f}")
            
            if r_squared > 0.9:
                st.success("✓ Excellent correlation preservation!")
            elif r_squared > 0.7:
                st.success("✓ Good correlation preservation")
            else:
                st.warning("⚠️ Moderate correlation preservation")
        
        with tab3:
            st.markdown("### Privacy Preservation Metrics")
            st.markdown("""
            Distance to Closest Record (DCR) measures how far synthetic records are from real records.
            Higher values indicate better privacy (synthetic records are not copies of real ones).
            """)
            
            mean_dcr = eval_results['privacy_metrics']['mean_dcr']
            std_dcr = eval_results['privacy_metrics']['std_dcr']
            min_dcr = eval_results['privacy_metrics']['min_dcr']
            
            col1, col2, col3 = st.columns(3)
            col1.metric("Mean DCR", f"{mean_dcr:.2f}σ")
            col2.metric("Std Dev DCR", f"{std_dcr:.2f}σ")
            col3.metric("Min DCR", f"{min_dcr:.2f}σ")
            
            if mean_dcr > 2.0:
                st.success("✓ Excellent privacy - synthetic records are well-separated from real data")
            elif mean_dcr > 1.0:
                st.success("✓ Good privacy preservation")
            else:
                st.warning("⚠️ Some synthetic records may be close to real records")
        
        with tab4:
            st.markdown("### Machine Learning Efficacy")
            st.markdown("""
            This tests whether models trained on synthetic data can perform well on real data.
            This is the ultimate test of synthetic data utility.
            """)
            
            f1_real = eval_results['ml_efficacy']['f1_real_real']
            f1_synthetic = eval_results['ml_efficacy']['f1_synthetic_real']
            retention = eval_results['ml_efficacy']['f1_retention_pct']
            
            # Create comparison chart
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=['Train on Real → Test on Real', 'Train on Synthetic → Test on Real'],
                y=[f1_real, f1_synthetic],
                marker_color=['#3498db', '#e67e22'],
                text=[f"{f1_real:.3f}", f"{f1_synthetic:.3f}"],
                textposition='auto'
            ))
            fig.update_layout(
                yaxis_title="F1-Score",
                height=400,
                yaxis_range=[0, 1]
            )
            st.plotly_chart(fig, use_container_width=True)
            
            st.metric("Performance Retention", f"{retention:.1f}%")
            
            if retention > 95:
                st.success("✓ Excellent - synthetic data nearly matches real data performance")
            elif retention > 85:
                st.success("✓ Good - synthetic data maintains strong predictive value")
            else:
                st.info("⚠️ Acceptable - some performance degradation observed")

# Business Case Page
elif page == "Business Case":
    st.header("💼 Business Case for Synthetic Data")
    
    st.subheader("Problem Statement")
    st.markdown("""
    Semiconductor manufacturers need AI/ML for yield optimization but face critical barriers:
    
    - **IP Protection**: Process parameters are trade secrets worth billions
    - **Competitive Intelligence**: Sensor data reveals manufacturing capabilities
    - **Regulatory Compliance**: GDPR, export controls restrict data sharing
    - **Vendor Partnerships**: Cannot share data with AI vendors/consultants
    - **Multi-site Learning**: Facilities cannot collaborate due to data silos
    """)
    
    st.subheader("📊 Market Opportunity (DACH Region)")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Semiconductor Market Size", "€45B", help="DACH region annual revenue")
    with col2:
        st.metric("Manufacturing Sites", "120+", help="Semiconductor fabs in DACH")
    with col3:
        st.metric("AI Investment", "€8.5B", help="Projected AI spending 2025-2030")
    
    st.subheader("💰 ROI Calculation (Typical Semiconductor Fab)")
    
    # ROI metrics
    st.markdown("### Value Drivers")
    
    benefits_df = pd.DataFrame({
        'Benefit': [
            'Yield Improvement (2-3%)',
            'Faster Time-to-Market',
            'Vendor Partnerships Enabled',
            'Reduced Downtime',
            'Cross-Facility Learning'
        ],
        'Annual Value (€M)': [12, 30, 8, 5, 10],
        'Implementation Timeline': [
            '6-12 months',
            '3-6 months',
            'Immediate',
            '6-9 months',
            '9-12 months'
        ]
    })
    
    st.dataframe(benefits_df, use_container_width=True)
    
    # Financial summary
    st.markdown("### Financial Summary")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total 3-Year Value", "€195M")
    with col2:
        st.metric("Investment Required", "€2M")
    with col3:
        st.metric("3-Year NPV", "€52M")
    with col4:
        st.metric("Payback Period", "4-6 months")
    
    st.subheader("🚀 Implementation Roadmap")
    
    roadmap_df = pd.DataFrame({
        'Phase': ['Pilot', 'Validation', 'Scale', 'Enterprise'],
        'Timeline': ['Month 1-2', 'Month 3-4', 'Month 5-8', 'Month 9-12'],
        'Scope': [
            'Single production line, 1 use case',
            'Verify quality & privacy metrics',
            'Expand to 3 lines, multiple use cases',
            'Full deployment, vendor integration'
        ],
        'Investment': ['€200K', '€300K', '€800K', '€700K']
    })
    
    st.dataframe(roadmap_df, use_container_width=True)
    
    st.subheader("🎯 Success Metrics")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **Technical KPIs:**
        - Statistical similarity > 85%
        - ML efficacy retention > 90%
        - Privacy DCR > 2.0σ
        - Zero real data leakage events
        """)
    
    with col2:
        st.markdown("""
        **Business KPIs:**
        - Yield improvement > 2%
        - 3+ vendor partnerships enabled
        - 25% reduction in time-to-insight
        - ROI > 2,500% in 3 years
        """)
    
    st.subheader("⚠️ Risk Mitigation")
    
    risks_df = pd.DataFrame({
        'Risk': [
            'Synthetic data quality insufficient',
            'Privacy concerns from stakeholders',
            'Integration complexity',
            'Change management resistance'
        ],
        'Mitigation Strategy': [
            'Pilot validation phase with strict quality gates',
            'Third-party privacy audit, transparent metrics',
            'Phased rollout, dedicated integration team',
            'Executive sponsorship, training program'
        ],
        'Probability': ['Low', 'Medium', 'Medium', 'Low'],
        'Impact': ['High', 'High', 'Medium', 'Medium']
    })
    
    st.dataframe(risks_df, use_container_width=True)

# Footer
st.markdown("---")
st.markdown("""
**Project created for AI Project Manager role at MOSTLY AI**  
Demonstrating: Synthetic data expertise • Technical understanding • Business acumen • Project management capability
""")
