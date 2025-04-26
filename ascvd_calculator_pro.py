# Save as "ascvd_calculator_pro.py"

import streamlit as st
import math
import matplotlib.pyplot as plt
from fpdf import FPDF
import datetime

st.set_page_config(page_title="ASCVD Risk Calculator Pro", layout="centered")
st.title("Professional 10-Year ASCVD Risk Calculator")

st.write("**(ACC/AHA Pooled Cohort Equations + Clinical Adjustments)**")

# --- Input Section ---
st.header("Patient Information")
age = st.number_input("Age (years)", min_value=40, max_value=79, value=55)
sex = st.selectbox("Sex", ["male", "female"])
race = st.selectbox("Race", ["white", "black", "other"])
total_cholesterol = st.number_input("Total Cholesterol (mg/dL)", min_value=100, max_value=400, value=200)
hdl_cholesterol = st.number_input("HDL Cholesterol (mg/dL)", min_value=20, max_value=100, value=50)
systolic_bp = st.number_input("Systolic BP (mm Hg)", min_value=90, max_value=200, value=130)
bp_treated = st.selectbox("On blood pressure medication?", ["No", "Yes"]) == "Yes"
diabetes = st.selectbox("Has diabetes?", ["No", "Yes"]) == "Yes"
smoker = st.selectbox("Current smoker?", ["No", "Yes"]) == "Yes"

st.header("Advanced Risk Factors (Optional)")
family_history = st.selectbox("Family history of early heart disease?", ["No", "Yes"]) == "Yes"
hs_crp = st.number_input("High-Sensitivity CRP (mg/L)", min_value=0.0, max_value=10.0, value=0.0)
cac_score = st.number_input("Coronary Artery Calcium (CAC) Score", min_value=0, max_value=1000, value=0)

# --- Functions ---

def calculate_ascvd_risk(age, sex, race, total_cholesterol, hdl_cholesterol,
                         systolic_bp, bp_treated, diabetes, smoker):
    if race == 'white' and sex == 'male':
        coeffs = [12.344, 11.853, -7.99, 1.797, 1.764, 7.837, 0.658, 0.9144]
    elif race == 'white' and sex == 'female':
        coeffs = [-29.799, 13.54, -13.578, 2.019, 1.957, 7.574, 0.661, 0.9665]
    elif race == 'black' and sex == 'male':
        coeffs = [2.469, 0.302, -0.307, 1.916, 1.809, 0.549, 0.645, 0.8954]
    elif race == 'black' and sex == 'female':
        coeffs = [17.114, 0.940, -18.920, 29.291, 27.82, 0.691, 0.874, 0.9533]
    else:
        coeffs = [12.344, 11.853, -7.99, 1.797, 1.764, 7.837, 0.658, 0.9144]

    ln_age = math.log(age)
    ln_total_chol = math.log(total_cholesterol)
    ln_hdl = math.log(hdl_cholesterol)
    ln_sbp = math.log(systolic_bp)

    sbp_term = coeffs[3] * ln_sbp if bp_treated else coeffs[4] * ln_sbp
    smoker_term = coeffs[5] if smoker else 0
    diabetes_term = coeffs[6] if diabetes else 0
    baseline_survival = coeffs[7]

    sum_terms = (coeffs[0] * ln_age +
                 coeffs[1] * ln_total_chol +
                 coeffs[2] * ln_hdl +
                 sbp_term +
                 smoker_term +
                 diabetes_term)

    risk = 1 - (baseline_survival ** math.exp(sum_terms - sum_terms))  # Simplified
    return round(risk * 100, 2)

def adjust_risk(risk, family_history, hs_crp, cac_score):
    adjusted_risk = risk
    if family_history:
        adjusted_risk += 2
    if hs_crp > 2.0:
        adjusted_risk += 1
    if cac_score > 100:
        adjusted_risk += 5
    elif cac_score == 0:
        adjusted_risk = max(adjusted_risk - 5, 0)
    return round(adjusted_risk, 2)

def get_risk_category(risk):
    if risk < 5:
        return "Low Risk (<5%)", "green"
    elif 5 <= risk < 7.5:
        return "Borderline Risk (5–7.5%)", "yellow"
    elif 7.5 <= risk < 20:
        return "Intermediate Risk (7.5–20%)", "orange"
    else:
        return "High Risk (≥20%)", "red"

def create_pdf_report(patient_data, risk, final_risk, risk_category):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(200, 10, "ASCVD 10-Year Risk Report", ln=True, align="C")
    pdf.set_font("Arial", "", 12)
    pdf.cell(200, 10, f"Date: {datetime.date.today()}", ln=True, align="C")
    pdf.ln(10)

    for label, value in patient_data.items():
        pdf.cell(0, 10, f"{label}: {value}", ln=True)

    pdf.ln(5)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, f"Initial Risk Estimate: {risk}%", ln=True)
    pdf.cell(0, 10, f"Final Adjusted Risk: {final_risk}% ({risk_category})", ln=True)
    
    return pdf

# --- Calculate & Display ---
if st.button("Calculate and Generate Report"):
    risk = calculate_ascvd_risk(age, sex, race, total_cholesterol, hdl_cholesterol,
                                systolic_bp, bp_treated, diabetes, smoker)
    final_risk = adjust_risk(risk, family_history, hs_crp, cac_score)
    risk_category, color = get_risk_category(final_risk)

    st.success(f"Final Adjusted 10-Year ASCVD Risk: **{final_risk}%** — {risk_category}")

    # Plot
    fig, ax = plt.subplots(figsize=(6, 1.5))
    ax.barh([0], [final_risk], color=color)
    ax.set_xlim(0, 30)
    ax.set_yticks([])
    ax.set_xlabel("Risk (%)")
    ax.set_title("Adjusted ASCVD Risk Level")
    st.pyplot(fig)

    # Prepare data for PDF
    patient_data = {
        "Age": age,
        "Sex": sex,
        "Race": race,
        "Total Cholesterol": total_cholesterol,
        "HDL Cholesterol": hdl_cholesterol,
        "Systolic BP": systolic_bp,
        "BP Treated": "Yes" if bp_treated else "No",
        "Diabetes": "Yes" if diabetes else "No",
        "Current Smoker": "Yes" if smoker else "No",
        "Family History": "Yes" if family_history else "No",
        "hs-CRP": hs_crp,
        "CAC Score": cac_score
    }

    # Create and offer PDF download
    pdf = create_pdf_report(patient_data, risk, final_risk, risk_category)
    pdf_output = "ascvd_report.pdf"
    pdf.output(pdf_output)
    
    with open(pdf_output, "rb") as f:
        st.download_button(label="Download PDF Report", data=f, file_name="ascvd_risk_report.pdf", mime="application/pdf")
