# InvoiceProcessor.GenAI

AI-assisted invoice processing automation built with UiPath REFramework.

This project processes invoice PDFs end-to-end: reads invoice documents, extracts structured invoice data using a Groq-hosted LLM, validates business rules, writes results to Excel, and separates successful and failed invoices with clear audit logs.

---

## 1. Project Overview

`InvoiceProcessor.GenAI` is a production-style UiPath automation designed for invoice intake and extraction.

The bot treats each invoice PDF as a transaction and processes it through the REFramework lifecycle:

1. Initialise configuration and dependencies
2. Pick one invoice from the inbox
3. Extract PDF text
4. Send invoice text to Groq LLM
5. Validate extracted invoice data
6. Write valid data to Excel
7. Move successful invoices to `Processed`
8. Move failed invoices to `Failed`
9. Log outcomes for review and audit

---

## 2. Business Purpose

Manual invoice processing is slow, repetitive, and error-prone. This automation demonstrates how RPA and GenAI can work together to support finance operations.

The bot helps with:

- Invoice data extraction
- Supplier invoice digitisation
- Line-item capture
- Basic finance validation
- Exception handling
- Audit-ready output generation
- Human review routing for failed invoices

---

## 3. Key Features

- UiPath REFramework state-machine architecture
- Config-driven design using `Data/Config.xlsx`
- PDF text extraction with OCR fallback
- Groq LLM integration through HTTP Request
- Structured JSON invoice extraction
- Business rule validation
- Excel output for invoices and line items
- Success and failure folder routing
- Business vs system exception handling
- Retry handling for transient errors
- Failure logging to CSV
- Queue-ready architecture for future Orchestrator deployment

---

## 4. Technology Stack

| Area | Tool |
|---|---|
| RPA Platform | UiPath Studio 2026 |
| Framework | Robotic Enterprise Framework |
| GenAI Provider | Groq API |
| LLM Model | llama-3.3-70b-versatile |
| PDF Processing | UiPath.PDF.Activities |
| Excel Output | UiPath.Excel.Activities |
| API Integration | UiPath.WebAPI.Activities |
| Data Format | JSON |
| Output Storage | Excel workbook and CSV logs |

---

## 5. Business Process Flow

```text
Supplier invoice PDF received
        ↓
PDF placed in Data/Inbox
        ↓
Bot picks invoice as a transaction
        ↓
Bot extracts raw text from PDF
        ↓
Groq LLM converts text into structured JSON
        ↓
Bot validates required fields and totals
        ↓
If valid:
    Write data to Output/invoices.xlsx
    Move PDF to Data/Processed
        ↓
If invalid:
    Move PDF to Data/Failed
    Log reason in Output/logs/failures.csv
        ↓
Bot continues with next invoice

REFramework initialisation, configuration loading, folder setup, workbook setup, and Groq API handling in progress.