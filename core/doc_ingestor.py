"""PDF, DOCX, and TXT text extraction for document ingestion."""

import io


def extract_text(uploaded_file):
    """Extract text from an uploaded file (PDF, DOCX, or TXT).

    Returns extracted text as a string.
    """
    name = uploaded_file.name.lower()

    if name.endswith(".pdf"):
        return _extract_pdf(uploaded_file)
    elif name.endswith(".docx"):
        return _extract_docx(uploaded_file)
    elif name.endswith(".txt"):
        return uploaded_file.read().decode("utf-8", errors="replace")
    else:
        raise ValueError(f"Unsupported document type: {name}")


def _extract_pdf(uploaded_file):
    """Extract text from a PDF file."""
    try:
        from PyPDF2 import PdfReader

        reader = PdfReader(io.BytesIO(uploaded_file.read()))
        pages = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                pages.append(text)
        return "\n\n".join(pages)
    except ImportError:
        try:
            import fitz  # pymupdf

            doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
            pages = []
            for page in doc:
                pages.append(page.get_text())
            doc.close()
            return "\n\n".join(pages)
        except ImportError:
            raise ImportError("Neither PyPDF2 nor pymupdf is installed. Install one to process PDFs.")


def _extract_docx(uploaded_file):
    """Extract text from a DOCX file."""
    from docx import Document

    doc = Document(io.BytesIO(uploaded_file.read()))
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    return "\n\n".join(paragraphs)
