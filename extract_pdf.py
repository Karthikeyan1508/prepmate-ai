import pdfplumber
import fitz  # PyMuPDF


def extract_text_pdf(file_path, method="pdfplumber"):
    """
    Extracts text from a given PDF file.
    
    Parameters:
        file_path (str): The path to the PDF file.
        method (str): Extraction method ('pdfplumber' or 'pymupdf').
        
    Returns:
        str: Extracted text from the PDF.
    """
    extracted_text = ""

    if method == "pdfplumber":
        try:
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    extracted_text += page.extract_text() + "\n"
        except Exception as e:
            print(f"Error using pdfplumber: {e}")
    
    elif method == "pymupdf":
        try:
            doc = fitz.open(file_path)
            extracted_text = "\n".join([page.get_text("text") for page in doc])
        except Exception as e:
            print(f"Error using pymupdf: {e}")

    return extracted_text.strip() if extracted_text else "No text extracted"

