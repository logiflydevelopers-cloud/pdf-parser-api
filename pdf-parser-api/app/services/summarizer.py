from langchain_openai import ChatOpenAI
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.prompts import ChatPromptTemplate
import os
from dotenv import load_dotenv
load_dotenv()  
llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0.2,
    api_key=os.environ["OPENAI_API_KEY"]
)

def summarize(text: str, pages: int, total_words: int):
    splitter = RecursiveCharacterTextSplitter(chunk_size=6000, chunk_overlap=200)
    chunks = splitter.split_text(text)

    map_prompt = ChatPromptTemplate.from_messages([
        ("system", "Summarize into 5–7 bullet points."),
        ("user", "{chunk}")
    ])

    bullets = []
    for c in chunks:
        bullets.append(llm.invoke(map_prompt.format_messages(chunk=c)).content)

    reduce_prompt = ChatPromptTemplate.from_messages([
        ("system", "Combine into final summary."),
        ("user", "\n".join(bullets))
    ])

    return llm.invoke(reduce_prompt.format_messages()).content.strip()
