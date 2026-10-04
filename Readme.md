# Exception Desk

An AI agent that investigates accounts-payable invoice exceptions,
specifically cases where the quantity billed on an invoice doesn't
match what was actually received.

## The problem
In procure-to-pay, invoices that fail three-way match get stuck in
manual review queues. Resolving them takes an analyst pulling the
purchase order and goods receipt and comparing them by hand.

## What it does
Given an invoice, the agent uses tool-calling to look up the related
purchase order and goods receipt itself, reasons over them, and
returns a structured decision: variance type, evidence, confidence,
and recommended action (auto-resolve, route to a human, or request
more info).

## Status
Working prototype with a Streamlit UI. Uses seeded sample data for
two invoices (one clean, one with a short receipt).
Next: more variance types and a small evaluation set to measure accuracy.

## Stack
Python, Google Gemini API (function calling + structured output), Streamlit

## Run locally
1. `pip install google-genai streamlit python-dotenv`
2. Create a `.env` file containing `GEMINI_API_KEY=your_key`
3. `streamlit run app.py`