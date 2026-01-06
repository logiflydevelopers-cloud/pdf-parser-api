from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.repos.pinecone_repo import PineconeRepo

# --------------------------------------------------
# Embedding model
# --------------------------------------------------
emb = OpenAIEmbeddings(model="text-embedding-3-small")


def build_embeddings(
    *,
    userId: str,
    pdfId: str,
    page_texts: list[str],
):
    """
    Builds Pinecone embeddings for a PDF.

    - namespace = userId
    - filter by pdfId
    - stores chunk text + page in metadata
    """

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1600,
        chunk_overlap=200,
        separators=["\n\n", "\n", " ", ""],
    )

    chunks = []
    for page_idx, text in enumerate(page_texts):
        if not text.strip():
            continue

        page_chunks = splitter.split_text(text)
        for c in page_chunks:
            chunks.append({
                "text": c,
                "page": page_idx + 1
            })

    if not chunks:
        return

    texts = [c["text"] for c in chunks]

    # Correct method for documents
    vectors = emb.embed_documents(texts)

    PineconeRepo().upsert_chunks(
        userId=userId,
        pdfId=pdfId,
        embeddings=vectors,
        chunks=chunks
    )
