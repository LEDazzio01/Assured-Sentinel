"""
Assured Sentinel Dashboard.

A Streamlit-based interactive dashboard for:
- Visualizing calibration data
- Running code verification
- Demonstrating the LLM correction loop

Usage:
    streamlit run assured_sentinel/dashboard/app.py
    # or
    make dashboard
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

import pandas as pd
import streamlit as st

from assured_sentinel import __version__
from assured_sentinel.config import get_settings
from assured_sentinel.core.commander import Commander, JsonCalibrationStore
from assured_sentinel.core.scorer import BanditScorer
from assured_sentinel.models import CalibrationData


# =============================================================================
# Page Configuration
# =============================================================================

st.set_page_config(
    page_title="Assured Sentinel",
    page_icon="🛡️",
    layout="wide",
)

st.title("🛡️ Assured Sentinel: Conformal Security Guardrail")
st.caption(f"v{__version__}")


# =============================================================================
# Cached Resources
# =============================================================================

@st.cache_resource
def get_commander(threshold: float) -> Commander:
    """Get cached Commander instance."""
    commander = Commander()
    commander.threshold = threshold
    return commander


@st.cache_resource
def get_analyst():
    """Get cached Analyst instance (if credentials available)."""
    settings = get_settings()
    if not settings.has_azure_credentials:
        return None
    
    from assured_sentinel.agents.analyst import AzureAnalyst
    return AzureAnalyst()


def load_calibration_data() -> CalibrationData | None:
    """Load calibration data from JSON file."""
    settings = get_settings()
    store = JsonCalibrationStore(settings.calibration_path)
    
    if store.exists():
        return store.load()
    return None


# =============================================================================
# Sidebar
# =============================================================================

st.sidebar.header("⚙️ Configuration")

# Threshold slider
settings = get_settings()
threshold_input = st.sidebar.slider(
    "Risk Threshold (α)",
    min_value=0.0,
    max_value=1.0,
    value=settings.default_threshold,
    step=0.01,
)

# Load calibration data
calibration = load_calibration_data()

if calibration:
    st.sidebar.success(
        f"✓ Calibration loaded\n\n"
        f"- q̂: {calibration.q_hat:.4f}\n"
        f"- α: {calibration.alpha}\n"
        f"- Samples: {calibration.n_samples}\n"
        f"- Date: {calibration.calibrated_at.strftime('%Y-%m-%d')}"
    )
else:
    st.sidebar.warning(
        "⚠️ No calibration data found.\n\n"
        "Run `sentinel calibrate` to generate calibration data."
    )

# Azure credentials check
analyst = get_analyst()
if analyst:
    st.sidebar.success("✓ Azure OpenAI configured")
else:
    st.sidebar.info(
        "ℹ️ Azure OpenAI not configured.\n\n"
        "Set environment variables to enable LLM features."
    )


# =============================================================================
# Main Content - Tabs
# =============================================================================

tab1, tab2, tab3 = st.tabs(["🔍 Verify Code", "📊 Calibration", "🤖 LLM Loop"])


# -----------------------------------------------------------------------------
# Tab 1: Code Verification
# -----------------------------------------------------------------------------

with tab1:
    st.subheader("Code Verification")
    st.markdown(
        "Enter Python code below to verify against the security threshold."
    )
    
    # Code input
    code_input = st.text_area(
        "Python Code",
        value="print('Hello, World!')",
        height=200,
        help="Enter the Python code you want to verify.",
    )
    
    col1, col2 = st.columns([1, 4])
    with col1:
        verify_button = st.button("🔍 Verify", type="primary")
    
    if verify_button and code_input:
        commander = get_commander(threshold_input)
        
        with st.spinner("Analyzing code..."):
            result = commander.verify(code_input)
        
        # Display results
        st.divider()
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "Non-Conformity Score",
                f"{result.score:.4f}",
                delta=None,
            )
        
        with col2:
            st.metric(
                "Threshold (q̂)",
                f"{result.threshold:.4f}",
            )
        
        with col3:
            if result.latency_ms:
                st.metric("Latency", f"{result.latency_ms:.1f}ms")
        
        # Decision display
        if result.passed:
            st.success("✅ **ASSURED**: Code passes security threshold.")
        else:
            st.error(f"🚫 **REJECTED**: {result.reason}")


# -----------------------------------------------------------------------------
# Tab 2: Calibration Visualization
# -----------------------------------------------------------------------------

with tab2:
    st.subheader("Calibration Distribution")
    
    if calibration:
        # Score distribution
        st.markdown("### Non-Conformity Score Distribution")
        
        df_scores = pd.DataFrame(calibration.scores, columns=["Score"])
        
        # Histogram
        st.bar_chart(df_scores["Score"].value_counts().sort_index())
        
        # Statistics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Mean", f"{df_scores['Score'].mean():.3f}")
        with col2:
            st.metric("Median", f"{df_scores['Score'].median():.3f}")
        with col3:
            st.metric("Std Dev", f"{df_scores['Score'].std():.3f}")
        with col4:
            st.metric("q̂ (Threshold)", f"{calibration.q_hat:.3f}")
        
        # Calibration details
        st.markdown("### Calibration Details")
        
        with st.expander("View full calibration data"):
            st.json(calibration.model_dump(mode="json"))
    else:
        st.info(
            "No calibration data available. Run the calibration command:\n\n"
            "```bash\n"
            "sentinel calibrate --alpha 0.1\n"
            "```"
        )


# -----------------------------------------------------------------------------
# Tab 3: LLM Correction Loop
# -----------------------------------------------------------------------------

with tab3:
    st.subheader("LLM Correction Loop")
    
    if analyst is None:
        st.warning(
            "⚠️ Azure OpenAI not configured.\n\n"
            "Set the following environment variables:\n"
            "- `AZURE_OPENAI_ENDPOINT`\n"
            "- `AZURE_OPENAI_API_KEY`\n"
            "- `AZURE_OPENAI_DEPLOYMENT_NAME`"
        )
    else:
        st.markdown(
            "Enter a coding task. The Analyst (LLM) will generate code, "
            "and the Commander will verify it. If rejected, the loop retries."
        )
        
        query = st.text_input(
            "Coding Task",
            value="Write a function to calculate factorial.",
        )
        
        max_retries = st.slider("Max Retries", 1, 5, 3)
        
        if st.button("🚀 Generate & Verify", type="primary"):
            commander = get_commander(threshold_input)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### 🤖 Analyst (Generator)")
                analyst_status = st.empty()
                code_display = st.empty()
            
            with col2:
                st.markdown("### 👮 Commander (Verifier)")
                commander_status = st.empty()
                decision_display = st.empty()
            
            current_prompt = query
            
            for attempt in range(1, max_retries + 1):
                analyst_status.text(f"Attempt {attempt}/{max_retries}: Generating...")
                
                try:
                    candidate_code = asyncio.run(analyst.generate(current_prompt))
                    code_display.code(candidate_code, language="python")
                    analyst_status.text(f"Attempt {attempt}/{max_retries}: Generated")
                except Exception as e:
                    analyst_status.error(f"Error: {e}")
                    break
                
                # Verify
                result = commander.verify(candidate_code)
                
                commander_status.text(
                    f"Score: {result.score:.4f} | Threshold: {result.threshold:.4f}"
                )
                
                if result.passed:
                    decision_display.success(
                        f"✅ ASSURED on attempt {attempt}!"
                    )
                    break
                else:
                    decision_display.error(f"🚫 REJECTED: {result.reason}")
                    current_prompt = (
                        f"{query}\n\n"
                        "IMPORTANT: Avoid security issues like eval(), exec(), "
                        "pickle.loads(), or hardcoded credentials."
                    )
            else:
                decision_display.error(
                    f"❌ Failed after {max_retries} attempts."
                )


# =============================================================================
# Footer
# =============================================================================

st.divider()
st.caption(
    f"Assured Sentinel v{__version__} | "
    "Split Conformal Prediction Architecture | "
    "[Documentation](https://github.com/LEDazzio01/Assured-Sentinel)"
)
