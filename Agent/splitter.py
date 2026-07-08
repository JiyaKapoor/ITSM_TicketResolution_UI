import re
import yaml
from langchain_core.documents import Document
from langchain_qdrant import QdrantVectorStore
from langchain_mistralai import MistralAIEmbeddings
from qdrant_client import QdrantClient
from qdrant_client.models import Distance,VectorParams
import os
from dotenv import load_dotenv
load_dotenv()
# our first aim is to extract the metadata from the document and to specifically extract description from the doc
Qdrant_url=os.getenv("Qdrant_url")
Qdrant_api_key=os.getenv("Qdrant_api_key")

client=QdrantClient(url=Qdrant_url,api_key=Qdrant_api_key)
embeddings=MistralAIEmbeddings(model="mistral-embed",api_key=os.getenv("MISTRAL_API_KEY"))

vector_store=QdrantVectorStore(
        client=client,
        embedding=embeddings,
        collection_name="ITSM_KnowledgeBase"
    )
def extract_description_resoltuion(knowledge_article):
    metadata={}
    content=""
    if(knowledge_article.startswith("---")):
        parts=knowledge_article.split("---",2) # here 2 means we need to stop after finding the second occurence of ---
        metadata=yaml.safe_load(parts[1]) # yaml.safe_load(content) allows us to parse YAML content in python obje like dict
        content=parts[2]
    description=metadata.gt("description").strip()    
    # now we will use regex to fetch the resolution from these tickets 
    resolution=re.search(r"#Resolution.*",content)
    combined_content=f"Issue Description: {description} , Resolution:{resolution}"
    return Document(page_content=combined_content,metadata=metadata)

def save_to_qdrant(langchain_document):
    vector_store.add_documents([langchain_document])