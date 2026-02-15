import os
from pypdf import PdfReader
from docx import Document

def extract_text_from_pdf(pdf_path):
    try:
        reader = PdfReader(pdf_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text
    except Exception as e:
        return f"Error reading PDF {pdf_path}: {e}"

def extract_text_from_docx(docx_path):
    try:
        doc = Document(docx_path)
        text = ""
        for para in doc.paragraphs:
            text += para.text + "\n"
        return text
    except Exception as e:
        return f"Error reading DOCX {docx_path}: {e}"

files = [
    "/Users/arsenijsojkin/PycharmProjects/GalileoskyTenParser/Для Алексея Меркурий 230.docx",
    "/Users/arsenijsojkin/PycharmProjects/GalileoskyTenParser/electricity-meters-mercury-230ar-03r.pdf",
    "/Users/arsenijsojkin/PycharmProjects/GalileoskyTenParser/galileosky-protocol.pdf",
    "/Users/arsenijsojkin/PycharmProjects/GalileoskyTenParser/gs-10.pdf"
]

for file_path in files:
    print(f"--- Extracting from {os.path.basename(file_path)} ---")
    if file_path.endswith(".pdf"):
        print(extract_text_from_pdf(file_path)[:2000]) # Limit output
    elif file_path.endswith(".docx"):
        print(extract_text_from_docx(file_path))
    print("\n" + "="*50 + "\n")
