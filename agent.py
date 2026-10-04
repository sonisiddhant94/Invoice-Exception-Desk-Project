"""
Exception Desk — agent logic

This is the reusable "brain" of the project. The Streamlit UI
(app.py) imports diagnose_exception() from here rather than
duplicating any of this.
"""

import os
import json
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()  # reads .env and loads GEMINI_API_KEY into the environment

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
MODEL = "gemini-2.5-flash"

# --- FAKE ERP DATA ---
PURCHASE_ORDERS = {
    "PO-1001": {"po_id": "PO-1001", "vendor": "Acme Packaging Co",
                "line_items": [{"item": "Corrugated boxes, 12x12", "quantity": 500, "unit_price": 2.10}]},
    "PO-1002": {"po_id": "PO-1002", "vendor": "Northwind Steel Supply",
                "line_items": [{"item": "Steel rod, 10mm", "quantity": 200, "unit_price": 14.50}]},
}

GOODS_RECEIPTS = {
    "PO-1001": {"po_id": "PO-1001", "quantity_received": 500},
    "PO-1002": {"po_id": "PO-1002", "quantity_received": 180},
}

INVOICES = {
    "INV-9001": {"invoice_id": "INV-9001", "po_id": "PO-1001", "vendor": "Acme Packaging Co",
                 "quantity_billed": 500, "unit_price": 2.10},
    "INV-9002": {"invoice_id": "INV-9002", "po_id": "PO-1002", "vendor": "Northwind Steel Supply",
                 "quantity_billed": 200, "unit_price": 14.50},
}

def get_purchase_order(po_id: str) -> dict:
    return PURCHASE_ORDERS.get(po_id, {"error": f"No PO found for {po_id}"})

def get_goods_receipt(po_id: str) -> dict:
    return GOODS_RECEIPTS.get(po_id, {"error": f"No goods receipt found for {po_id}"})

# --- TOOL DEFINITIONS ---
get_po_tool = types.FunctionDeclaration(
    name="get_purchase_order",
    description="Fetch a purchase order's details by its PO ID.",
    parameters={
        "type": "OBJECT",
        "properties": {"po_id": {"type": "STRING", "description": "e.g. PO-1001"}},
        "required": ["po_id"],
    },
)

get_gr_tool = types.FunctionDeclaration(
    name="get_goods_receipt",
    description="Fetch the goods receipt (quantity actually received) for a PO ID.",
    parameters={
        "type": "OBJECT",
        "properties": {"po_id": {"type": "STRING", "description": "e.g. PO-1001"}},
        "required": ["po_id"],
    },
)

tools = types.Tool(function_declarations=[get_po_tool, get_gr_tool])

AVAILABLE_TOOLS = {
    "get_purchase_order": get_purchase_order,
    "get_goods_receipt": get_goods_receipt,
}

# --- STRUCTURED OUTPUT SCHEMA ---
DECISION_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "variance_type": {"type": "STRING", "enum": ["quantity_mismatch", "price_mismatch", "no_variance", "insufficient_data"]},
        "evidence": {"type": "STRING"},
        "confidence": {"type": "NUMBER"},
        "recommended_action": {"type": "STRING", "enum": ["auto_resolve", "route_to_human_approval", "request_more_info"]},
    },
    "required": ["variance_type", "evidence", "confidence", "recommended_action"],
}

# --- THE AGENT LOOP ---
def diagnose_exception(invoice_id: str) -> dict:
    invoice = INVOICES[invoice_id]

    contents = [
        types.Content(role="user", parts=[types.Part.from_text(
            text=f"Diagnose this invoice exception. Use the available tools to "
                 f"fetch the PO and goods receipt before concluding anything:\n"
                 f"{json.dumps(invoice, indent=2)}"
        )])
    ]

    for _ in range(5):
        response = client.models.generate_content(
            model=MODEL,
            contents=contents,
            config=types.GenerateContentConfig(tools=[tools]),
        )

        calls = response.function_calls
        if not calls:
            break

        contents.append(response.candidates[0].content)

        result_parts = []
        for call in calls:
            result = AVAILABLE_TOOLS[call.name](**call.args)
            result_parts.append(types.Part.from_function_response(name=call.name, response={"result": result}))
        contents.append(types.Content(role="user", parts=result_parts))

    final = client.models.generate_content(
        model=MODEL,
        contents=contents + [types.Content(role="user", parts=[types.Part.from_text(
            text="Now give your final diagnosis in the required structured format."
        )])],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=DECISION_SCHEMA,
        ),
    )
    return json.loads(final.text)