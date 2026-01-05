import os

APP_NAME = "PDF Parser API"
API_PREFIX = "/v1"

# External services (will be used later)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_HOST = os.getenv("PINECONE_HOST")

FIRESTORE_PROJECT = os.getenv("FIRESTORE_PROJECT")
