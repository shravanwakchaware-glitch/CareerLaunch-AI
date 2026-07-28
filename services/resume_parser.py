import fitz
from docx import Document
import os


def extract_resume_text(file_path):
    """
    Extract text from a PDF or DOCX resume.
    """

    extension = os.path.splitext(file_path)[1].lower()

    text = ""

    if extension == ".pdf":

        document = fitz.open(file_path)

        for page in document:
            text += page.get_text()

        document.close()

    elif extension == ".docx":

        document = Document(file_path)

        for paragraph in document.paragraphs:
            text += paragraph.text + "\n"

    return text.strip()