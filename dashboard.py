import streamlit as st
import pandas as pd
import asyncio
import os
import pickle
from commander import Commander
from analyst import generate_code

# Page Config
st.set_page_config(page_title="Assured Sentinel", layout="wide")
st.title("🛡️ Assured Sentinel: Conformal Security Guardrail")

# Sidebar: Configuration
st.sidebar.header("Configuration")
threshold_input = st.sidebar.slider("Risk Threshold (alpha)", 0.0, 1.0, 0.15)
model_name = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4o")
st.sidebar.info(f"Model: {model_name}")

# Load Calibration Data (Visualization)
if os.path.exists("calibration_data.pkl"):
    with open("calibration_data.pkl", "rb") as f:
        cal_data = pickle.load(f)
    st.sidebar.success(f"Calibration Loaded (n={len(cal_data['scores'])})")
    
    # Show Histogram
    st.subheader("Calibration Distribution (Non-Conformity Scores)")
    df_scores = pd.DataFrame(cal_data['scores'], columns=["Score"])
    st.bar_chart(df_scores)
else:
    st.sidebar.warning("No calibration data found. Run calibration.py first.")

# Main Interface
query = st.text_input("Enter a coding task:", "Write a function to calculate factorial.")

if st.button("Generate & Assure"):
    # 1. Initialize Commander
    commander = Commander(default_threshold=threshold_input)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🤖 Analyst (Generator)")
        status_text = st.empty()
        status_text.text("Generating...")
        
        # Run Async Code Generation
        try:
            candidate_code = asyncio.run(generate_code(query))
            st.code(candidate_code, language='python')
            status_text.text("Generation Complete.")
        except Exception as e:
            st.error(f"Analyst Error: {e}")
            st.stop()

    with col2:
        st.markdown("### 👮 Commander (Verifier)")
        
        # Verify
        decision = commander.verify(candidate_code)
        
        # Display Metrics
        st.metric("Non-Conformity Score", f"{decision['score']:.4f}", delta_color="inverse")
        st.metric("Threshold (q_hat)", f"{commander.threshold:.4f}")
        
        # Visual Decision
        if decision['status'] == "PASS":
            st.success("✅ ASSURED: Code fits within safety distribution.")
        else:
            st.error(f"🛑 REJECTED: {decision['reason']}")
            st.warning("Triggering Correction Loop... (See Console/Logs)")

st.markdown("---")
st.caption("Assured Sentinel v1.0 | Split Conformal Prediction Architecture")