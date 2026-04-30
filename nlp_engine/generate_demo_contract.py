"""
ForeSight — Demo Contract PDF Generator
Generates a synthetic Apex Manufacturing buyer agreement containing
all 4 dark-pattern clause types for guaranteed 100% detection recall.
"""

import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer

OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "demo_contract.pdf")

CONTRACT_SECTIONS = [
    ("SUPPLY AGREEMENT", None, True),
    ("Between:", None, False),
    ("", "Apex Manufacturing Pvt Ltd (hereinafter referred to as 'Buyer'), GSTIN: 27AADCA1234F1ZP, having its registered office at Plot 45, MIDC Industrial Area, Pune, Maharashtra 411019", False),
    ("AND", None, False),
    ("", "Rohan's Precision Components (hereinafter referred to as 'Supplier'), GSTIN: 27AABCU9603R1ZM, having its registered office at Unit 12, Bhosari Industrial Estate, Pune, Maharashtra 411026", False),
    ("1. SCOPE OF SUPPLY", None, False),
    ("", "The Supplier agrees to manufacture and deliver precision auto-ancillary components as specified in Annexure A, subject to the quality standards outlined in Annexure B. All deliveries shall be made to the Buyer's designated facility within the agreed lead times.", False),
    ("2. PRICING AND PAYMENT TERMS", None, False),
    ("", "2.1 The agreed unit prices are as specified in the Purchase Order. All prices are exclusive of GST.", False),
    ("", "2.2 Payment shall be made within forty-five (45) days from the date of receipt of a valid invoice, subject to the conditions specified herein.", False),
    ("", "2.3 DISPUTE RESOLUTION AND PAYMENT: In the event that any dispute, claim, or objection is raised by the Buyer regarding the quality, quantity, or specification of goods delivered, payment shall be suspended and withheld in its entirety until such dispute is resolved to the Buyer's satisfaction. The Buyer reserves the right to hold all outstanding payments, including those unrelated to the disputed consignment, pending full resolution.", False),
    ("3. INVOICING REQUIREMENTS", None, False),
    ("", "3.1 All invoices must comply with GST regulations and include: PO number, delivery challan reference, HSN codes, and applicable tax breakdowns.", False),
    ("", "3.2 INVOICING DEFECT CLAUSE: Any invoice found to contain a defect, error, discrepancy, or non-conformity — including but not limited to incorrect HSN codes, missing references, calculation errors, or formatting issues — shall be rejected and returned to the Supplier. Upon such rejection, the forty-five (45) day payment period shall reset and recommence from the date of receipt of the corrected invoice. The payment clock shall restart in full regardless of the nature or materiality of the defect identified.", False),
    ("4. SET-OFF AND DEDUCTIONS", None, False),
    ("", "4.1 The Buyer may set off, deduct, or offset any amounts claimed to be owed by the Supplier against any future payments, purchase orders, or outstanding amounts payable to the Supplier. This right of set-off extends to any claim, whether liquidated or unliquidated, arising from any transaction between the parties, and may be exercised without prior notice to the Supplier.", False),
    ("5. FORCE MAJEURE", None, False),
    ("", "5.1 Neither party shall be liable for delays caused by force majeure events. For the purposes of this Agreement, force majeure includes but is not limited to: natural disasters, war, terrorism, pandemic, epidemic, government regulations, market conditions, economic downturn, business disruption, changes in demand, supply chain disruption, raw material shortage, currency fluctuation, or any other event beyond the reasonable control of the affected party.", False),
    ("", "5.2 In the event of force majeure, the Buyer may defer all payment obligations for the duration of the force majeure event plus an additional ninety (90) day recovery period.", False),
    ("6. QUALITY AND INSPECTION", None, False),
    ("", "6.1 All goods are subject to inspection by the Buyer within 30 days of delivery. The Buyer's quality standards shall prevail in case of any disagreement.", False),
    ("7. TERM AND TERMINATION", None, False),
    ("", "7.1 This Agreement shall be effective for a period of twenty-four (24) months from the date of execution.", False),
    ("", "7.2 Either party may terminate this Agreement with ninety (90) days written notice.", False),
    ("8. GOVERNING LAW", None, False),
    ("", "This Agreement shall be governed by the laws of India. Any disputes shall be subject to the exclusive jurisdiction of the courts of Pune, Maharashtra.", False),
]


def generate_demo_contract():
    """Generate the demo contract PDF with all 4 dark patterns embedded."""
    doc = SimpleDocTemplate(OUTPUT_PATH, pagesize=A4, topMargin=0.75*inch, bottomMargin=0.75*inch)
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle("ContractTitle", parent=styles["Title"], fontSize=16, spaceAfter=6)
    heading_style = ParagraphStyle("ContractHeading", parent=styles["Heading2"], fontSize=12, spaceBefore=14, spaceAfter=4)
    body_style = ParagraphStyle("ContractBody", parent=styles["Normal"], fontSize=10, leading=14, spaceAfter=6)
    party_style = ParagraphStyle("PartyStyle", parent=styles["Normal"], fontSize=10, leading=13, spaceAfter=4)

    story = []

    for heading, body, is_title in CONTRACT_SECTIONS:
        if is_title:
            story.append(Paragraph(heading, title_style))
            story.append(Spacer(1, 12))
        elif heading and not body:
            story.append(Paragraph(heading, heading_style if heading[0].isdigit() or heading == "AND" or heading == "Between:" else party_style))
        elif body:
            if heading:
                story.append(Paragraph(heading, heading_style))
            story.append(Paragraph(body, body_style))

    story.append(Spacer(1, 30))
    story.append(Paragraph("_________________________&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;_________________________", body_style))
    story.append(Paragraph("For Apex Manufacturing Pvt Ltd&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;For Rohan's Precision Components", body_style))
    story.append(Paragraph("(Authorized Signatory)&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;(Authorized Signatory)", body_style))
    story.append(Spacer(1, 20))
    story.append(Paragraph("Date: 15 March 2025&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Place: Pune, Maharashtra", body_style))

    doc.build(story)
    return OUTPUT_PATH


if __name__ == "__main__":
    path = generate_demo_contract()
    print(f"Demo contract generated: {path}")

    # Verify detection
    from nlp_engine.contract_detector import extract_pdf_text, detect_dark_patterns
    text = extract_pdf_text(path)
    print(f"Extracted {len(text)} characters\n")

    results = detect_dark_patterns(text)
    for r in results:
        sev = "RED" if r["severity"] == "Critical" else "YELLOW"
        print(f"  [{sev}] {r['type']}: {r['impact']}")
    print(f"\nDetected: {len(results)}/4 patterns")
