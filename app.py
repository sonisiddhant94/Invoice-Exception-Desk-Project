import streamlit as st
from agent import diagnose_exception, INVOICES

st.set_page_config(page_title="Exception Desk", page_icon="📋")
st.title("📋 Exception Desk")
st.caption("AI agent for AP invoice-exception diagnosis")

invoice_id = st.selectbox("Select an invoice to diagnose:", list(INVOICES.keys()))

st.subheader("Invoice")
st.json(INVOICES[invoice_id])

if st.button("Diagnose Exception"):
    with st.spinner("Agent is investigating — fetching PO and goods receipt..."):
        decision = diagnose_exception(invoice_id)

    st.subheader("Agent's Decision")

    if decision["variance_type"] == "no_variance":
        st.success(f"✅ No variance detected — {decision['recommended_action']}")
    else:
        st.warning(f"⚠️ {decision['variance_type']} detected — {decision['recommended_action']}")

    st.write("**Evidence:**", decision["evidence"])
    st.write("**Confidence:**", decision["confidence"])

    with st.expander("Full structured output"):
        st.json(decision)