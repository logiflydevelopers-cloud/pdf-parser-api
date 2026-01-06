from pinecone import Pinecone
import os
import uuid

# --------------------------------------------------
# Pinecone client (env vars injected by Render)
# --------------------------------------------------
pc = Pinecone(api_key=os.environ["PINECONE_API_KEY"])
index = pc.Index(host=os.environ["PINECONE_HOST"])


class PineconeRepo:
    """
    Namespace strategy:
      - namespace = userId  (recommended)
      - filter by pdfId
    """

    def upsert_chunks(
        self,
        *,
        userId: str,
        pdfId: str,
        embeddings: list[list[float]],
        chunks: list[dict],
    ):
        """
        chunks = [
          { "text": "...", "page": 1 }
        ]
        """

        vectors = []

        for i, (vec, chunk) in enumerate(zip(embeddings, chunks)):
            vectors.append({
                "id": f"{pdfId}_c{i}",
                "values": vec,
                "metadata": {
                    "userId": userId,
                    "pdfId": pdfId,
                    "page": chunk["page"],
                    "chunkId": f"c{i}",
                    "text": chunk["text"],   # 👈 IMPORTANT
                },
            })

        index.upsert(
            vectors=vectors,
            namespace=userId   # 👈 NOT __default__
        )

    def query(
        self,
        *,
        userId: str,
        pdfId: str,
        vector: list[float],
        top_k: int = 6,
    ):
        return index.query(
            vector=vector,
            top_k=top_k,
            namespace=userId,              
            filter={"pdfId": pdfId},       
            include_metadata=True,
        )

    def delete_pdf(self, *, userId: str, pdfId: str):
        """
        Optional helper to delete all chunks for a PDF
        """
        index.delete(
            filter={"pdfId": pdfId},
            namespace=userId
        )
