import os
from dotenv import load_dotenv
import vertexai
from pinecone import Pinecone

load_dotenv()

PROJECT_ID = os.getenv("PROJECT_ID")
LOCATION = os.getenv("REGION")
GOOGLE_APPLICATION_CREDENTIALS = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_ENV = os.getenv("PINECONE_ENV")
INDEX_NAME = os.getenv("INDEX_NAME")

vertexai.init(project=PROJECT_ID, location=LOCATION)

pc = Pinecone(api_key=PINECONE_API_KEY, environment=PINECONE_ENV)
pinecone_index = pc.Index(INDEX_NAME)
