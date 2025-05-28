import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse, Rectangle, Polygon

# Reference values
CTRL_pH = 7.4
CTRL_HCO3 = 24
CTRL_PCO2 = 40

def interpret_abg_disorder(pH, paCO2, hco3):
    pH_low = pH < 7.35
    pH_high = pH > 7.45
    pCO2_low = paCO2 < 36
    pCO2_high = paCO2 > 44
    hco3_low = hco3 < 22
    hco3_high = hco3 > 26

    # SINGLE DISORDERS
    if pH_low and hco3_low and not pCO2_high:
        return ("Type: Metabolic Acidosis\n"
                "Primary: ↓ HCO₃⁻\n"
                "Compensation: ↓ PaCO₂")
    elif pH_high and hco3_high and not pCO2_low:
        return ("Type: Metabolic Alkalosis\n"
                "Primary: ↑ HCO₃⁻\n"
                "Compensation: ↑ PaCO₂")
    elif pH_low and pCO2_high and not hco3_low:
        return ("Type: Respiratory Acidosis\n"
                "Primary: ↑ PaCO₂\n"
                "Compensation: ↑ HCO₃⁻")
    elif pH_high and pCO2_low and not hco3_high:
        return ("Type: Respiratory Alkalosis\n"
                "Primary: ↓ PaCO₂\n"
                "Compensation: ↓ HCO₃⁻")
    # MIXED DISORDERS
    if pH_low and pCO2_high and hco3_low:
        return ("Type: Respiratory Acidosis with Metabolic Acidosis\n"
                "Primary: ↑ PaCO₂ (Respiratory Acidosis)\n"
                "Concurrent: ↓ HCO₃⁻ (Metabolic Acidosis)\n"
                "Both drive ↓ pH")
    if pH_high and pCO2_low and hco3_high:
        return ("Type: Respiratory Alkalosis with Metabolic Alkalosis\n"
                "Primary: ↓ PaCO₂ (Respiratory Alkalosis)\n"
                "Concurrent: ↑ HCO₃⁻ (Metabolic Alkalosis)\n"
                "Both drive ↑ pH")
    if (not pH_low and not pH_high) and pCO2_high and hco3_high:
        return ("Type: Respiratory Acidosis with Metabolic Alkalosis\n"
                "Primary: ↑ PaCO₂ (Respiratory Acidosis)\n"
                "Concurrent: ↑ HCO₃⁻ (Metabolic Alkalosis)\n"
                "pH near normal: opposing effects")
    if (not pH_low and not pH_high) and pCO2_low and hco3_low:
        return ("Type: Respiratory Alkalosis with Metabolic Acidosis\n"
                "Primary: ↓ PaCO₂ (Respiratory Alkalosis)\n"
                "Concurrent: ↓ HCO₃⁻ (Metabolic Acidosis)\n"
                "pH near normal: opposing effects")
    if (not pH_low and not pH_high) and (abs(hco3-24) < 2):
        return ("Type: Metabolic Acidosis with Metabolic Alkalosis\n"
                "Primary: HCO₃⁻ ~ normal\n"
                "Both metabolic processes oppose; check clinical context")
    # Fully compensated or normal
    if (not pH_low and not pH_high):
        if (not pCO2_low and not pCO2_high) and (not hco3_low and not hco3_high):
            return ("Type: Normal acid-base status\n"
                    "All parameters within normal range")
        if hco3_high:
            return ("Type: Metabolic Alkalosis (compensated)\n"
                    "Primary: ↑ HCO₃⁻\n"
                    "Compensation: ↑ PaCO₂")
        if hco3_low:
            return ("Type: Metabolic Acidosis (compensated)\n"
                    "Primary: ↓ HCO₃⁻\n"
                    "Compensation: ↓ PaCO₂")
        if pCO2_high:
            return ("Type: Respiratory Acidosis (compensated)\n"
                    "Primary: ↑ PaCO₂\n"
                    "Compensation: ↑ HCO₃⁻")
        if pCO2_low:
            return ("Type: Respiratory Alkalosis (compensated)\n"
                    "Primary: ↓ PaCO₂\n"
                    "Compensation: ↓ HCO₃⁻")
    return ("Type: Complex or unclassified\n"
            "Check input values and clinical context")

def anion_gap_and_delta(na, cl, hco3):
    ag = na - (cl + hco3)
    delta_ag = ag - 12
    delta_hco3 = 24 - hco3
    delta_ratio = None
    if delta_hco3 != 0:
        delta_ratio = delta_ag / delta_hco3
    if delta_ratio is not None and delta_hco3 > 0:
        if delta_ratio < 1.0:
            ratio_text = "ΔAG/Δ[HCO₃⁻] < 1: Concurrent non-anion gap metabolic acidosis"
        elif delta_ratio > 2.0:
            ratio_text = "ΔAG/Δ[HCO₃⁻] > 2: Concurrent metabolic alkalosis"
        else:
            ratio_text = "ΔAG/Δ[HCO₃⁻] 1–2: Pure anion gap metabolic acidosis"
    else:
        ratio_text = "ΔAG/Δ[HCO₃⁻] not applicable"
    return ag, delta_ratio, ratio_text

def calc_pH(hco3, pco2):
    pKa = 6.1
    s = 0.03
    return pKa + np.log10(hco3 / (s * pco2))

def plot_davenport(ctrl_pH, ctrl_hco3, patient_pH, patient_hco3):
    fig, ax = plt.subplots(figsize=(6.5, 5))
    # Zones
    norm = Ellipse((7.4, 24), 0.1, 7, color='lightgreen', alpha=0.6, zorder=1, label='Normal')
    ax.add_patch(norm)
    ax.add_patch(Rectangle((7.05, 4), 0.33, 12, color='gold', alpha=0.45, label='Metabolic Acidosis', zorder=1))
    ax.add_patch(Rectangle((7.37, 27), 0.26, 16, color='cyan', alpha=0.45, label='Metabolic Alkalosis', zorder=1))
    ax.add_patch(Rectangle((7.0, 24), 0.37, 22, color='orange', alpha=0.36, label='Respiratory Acidosis', zorder=1))
    ax.add_patch(Rectangle((7.37, 4), 0.33, 20, color='pink', alpha=0.37, label='Respiratory Alkalosis', zorder=1))
    pts = np.array([[7.0, 4], [7.2, 4], [7.2, 10], [7.0, 10]])
    ax.add_patch(Polygon(pts, closed=True, color='gray', alpha=0.40, zorder=0, label='Mixed Disorder'))
    pts2 = np.array([[7.55, 40], [7.7, 40], [7.7, 48], [7.55, 48]])
    ax.add_patch(Polygon(pts2, closed=True, color='gray', alpha=0.40, zorder=0))

    # Isobars
    isobars = [20, 40, 60]
    colors = ['orange', 'blue', 'red']
    labels = ['PaCO₂ = 20', 'PaCO₂ = 40', 'PaCO₂ = 60']
    pKa = 6.1
    s = 0.03
    pH_range = np.linspace(7.0, 7.7, 200)
    for paCO2, color, label in zip(isobars, colors, labels):
        hco3_curve = (10 ** (pH_range - pKa)) * s * paCO2
        ax.plot(pH_range, hco3_curve, color=color, lw=2, label=label)
    # Arrow/points
    ax.scatter([ctrl_pH], [ctrl_hco3], color='green', s=100, zorder=5)
    ax.text(ctrl_pH+0.012, ctrl_hco3+1, 'C', fontsize=17, color='green', fontweight='bold')
    ax.scatter([patient_pH], [patient_hco3], color='purple', s=100, zorder=5)
    ax.text(patient_pH+0.012, patient_hco3+1, 'B', fontsize=17, color='purple', fontweight='bold')
    ax.annotate("", xy=(patient_pH, patient_hco3), xytext=(ctrl_pH, ctrl_hco3),
                arrowprops=dict(arrowstyle="->", lw=2.5, color='black'))
    ax.set_title("Davenport Diagram with Clinical Zones", fontsize=13, weight='bold')
    ax.set_xlabel("pH", fontsize=11)
    ax.set_ylabel("[HCO₃⁻] (mEq/L)", fontsize=11)
    ax.set_xlim(7.0, 7.7)
    ax.set_ylim(0, 48)
    ax.grid(True, linestyle="--", linewidth=0.6, alpha=0.6)
    custom_lines = [Rectangle((0,0),1,1, color='lightgreen', alpha=0.6),
                    Rectangle((0,0),1,1, color='gold', alpha=0.45),
                    Rectangle((0,0),1,1, color='cyan', alpha=0.45),
                    Rectangle((0,0),1,1, color='orange', alpha=0.36),
                    Rectangle((0,0),1,1, color='pink', alpha=0.37),
                    Rectangle((0,0),1,1, color='gray', alpha=0.40)]
    ax.legend(custom_lines,
              ['Normal', 'Metabolic Acidosis', 'Metabolic Alkalosis', 'Respiratory Acidosis', 'Respiratory Alkalosis', 'Mixed Disorder'],
              fontsize=8, loc='upper left')
    return fig

# -- STREAMLIT APP BODY --
st.title("Pediatric ABG Interpreter – Web Version")

col1, col2 = st.columns(2)
with col1:
    paCO2 = st.number_input("PaCO₂ (mmHg)", min_value=10.0, max_value=120.0, value=40.0, step=0.1)
    hco3 = st.number_input("HCO₃⁻ (mEq/L)", min_value=5.0, max_value=50.0, value=24.0, step=0.1)
with col2:
    na = st.number_input("Na⁺ (mEq/L)", min_value=100.0, max_value=180.0, value=140.0, step=0.1)
    cl = st.number_input("Cl⁻ (mEq/L)", min_value=50.0, max_value=150.0, value=104.0, step=0.1)

if st.button("Interpret ABG"):
    patient_pH = calc_pH(hco3, paCO2)
    st.markdown(f"**Calculated Patient pH:** {patient_pH:.2f}")
    interpretation = interpret_abg_disorder(patient_pH, paCO2, hco3)
    st.markdown(f"**Acid-base Interpretation:**\n```\n{interpretation}\n```")

    ag, delta_ratio, ratio_text = anion_gap_and_delta(na, cl, hco3) if hco3 < 22 else (None, None, "")
    if ag is not None:
        st.markdown(f"**Anion gap:** {ag:.1f} (normal ≈12)")
    if ag is not None:
        st.markdown(f"**ΔAG/Δ[HCO₃⁻]:** {ratio_text}")
    fig = plot_davenport(CTRL_pH, CTRL_HCO3, patient_pH, hco3)
    st.pyplot(fig)
else:
    st.info("Enter values and click Interpret ABG to see the interpretation and diagram.")
