import base64
from docx import Document
import io

def word_to_base64(file_path : str) -> str:
    """
    Converts a Word document to base64 string for HTTP transmission
    
    Parameters:
        file_path (str): Path to the Word document
        
    Returns:
        str: Base64 encoded string of the document
    """
    try:
        # Create a bytes buffer
        buffer = io.BytesIO()
        
        # Load and save the document to the buffer
        doc = Document(file_path)
        doc.save(buffer)
        
        # Get the bytes value and encode to base64
        doc_bytes = buffer.getvalue()
        base64_encoded = base64.b64encode(doc_bytes).decode('utf-8')
        
        return base64_encoded
        
    except Exception as e:
        raise Exception(f"Error processing document: {str(e)}")
    finally:
        buffer.close()