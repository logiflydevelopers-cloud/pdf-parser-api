from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from app.repos.pinecone_repo import PineconeRepo
from dotenv import load_dotenv
load_dotenv()  

llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0.2
)

emb = OpenAIEmbeddings(
    model="text-embedding-3-small"
)

NO_ANSWER = "Not enough information in the summary to answer that."

def answer_question(summary: str, question: str, pdfId: str):
    """
    1) Try answering ONLY from summary
    2) If summary lacks answer → fallback to Pinecone RAG
    """

    # ---------------------------
    # STEP 1: SUMMARY-ONLY ANSWER
    # ---------------------------
    summary_prompt = f"""
You must answer ONLY using the summary below.

If the summary does not contain the answer,
respond EXACTLY with this sentence and nothing else:
"{NO_ANSWER}"

SUMMARY:
{summary}

QUESTION:
{question}
"""

    summary_ans = llm.invoke(summary_prompt).content.strip()

    if summary_ans == NO_ANSWER:
        # FALLBACK REQUIRED
        pass
    else:
        return summary_ans, "summary", []

    # ---------------------------
    # STEP 2: RAG FALLBACK
    # ---------------------------
    q_vec = emb.embed_query(question)

    res = PineconeRepo().query(
        vector=q_vec,
        pdfId=pdfId,
        top_k=6
    )

    if not res.matches:
        return (
            "Not enough information in the document to answer that.",
            "rag",
            []
        )

    context_blocks = []
    sources = []
    used_pages = set()

    for m in res.matches:
        text = m.metadata.get("text", "").strip()
        page = m.metadata.get("page")

        if not text:
            continue

        context_blocks.append(f"(p. {page})\n{text}")
        used_pages.add(page)

        sources.append({
            "page": page,
            "chunkId": m.metadata.get("chunkId"),
            "score": round(m.score, 4)
        })

    context = "\n\n---\n\n".join(context_blocks)

    rag_prompt = f"""
Answer using ONLY the provided context.
Use the summary only for high-level framing.
If the answer is not supported, say:
"Not enough information in the document to answer that."

Include citations like (p. X).

SUMMARY:
{summary}

CONTEXT:
{context}

QUESTION:
{question}
"""

    rag_answer = llm.invoke(rag_prompt).content.strip()

    if used_pages:
        rag_answer += "\n\nSources: " + ", ".join(
            f"p. {p}" for p in sorted(used_pages)
        )

    return rag_answer, "rag", sources
