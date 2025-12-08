import fitz  # PyMuPDF

def dump_first_pages(pdf_path):
    try:
        doc = fitz.open(pdf_path)
        print(f"--- DUMPING CONTENT OF {pdf_path} ---")
        for i in range(14, 18):
            print(f"\n--- PAGE {i+1} ---")
            print(doc[i].get_text())
    except Exception as e:
        print(f"Error: {e}")

pdf_path = r"c:\Users\narva\projects\CATIE\PARES\backend\documents\orgs\TIERRA VIVA\20210421_PLAN ESTRATEGICO TIERRA VIVA 2021-2025.pdf"
dump_first_pages(pdf_path)
