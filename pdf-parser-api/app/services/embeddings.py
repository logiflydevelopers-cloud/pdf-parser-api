from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.repos.pinecone_repo import PineconeRepo

emb = OpenAIEmbeddings(model="text-embedding-3-small")

def build_embeddings(pdfId, texts):
    splitter = RecursiveCharacterTextSplitter(chunk_size=1600, chunk_overlap=200)
    chunks = splitter.split_text("\n".join(texts))

    vectors = []
    for i, c in enumerate(chunks):
        v = emb.embed_query(c)
        vectors.append({
            "id": f"{pdfId}_c{i}",
            "values": v,
            "metadata": {"pdfId": pdfId, "chunkId": f"c{i}"}
        })

    PineconeRepo().upsert(vectors)
