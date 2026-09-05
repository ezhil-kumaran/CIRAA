from typing import List
import logfire
from langchain_text_splitters import RecursiveCharacterTextSplitter

def chunk_text(text: str, chunk_size: int = 1500, chunk_overlap: int = 200) -> List[str]:
    """
    Splits text recursively using paragraphs, lines, sentences, and words.
    Ensures chunks do not exceed the specified size while preserving context overlap.
    """
    with logfire.span("Text Chunking", text_length=len(text)):
        if not text.strip(): 
            return []
            
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        valid_chunks = splitter.split_text(text)
        logfire.info(f"Generated {len(valid_chunks)} chunks")
        return valid_chunks
