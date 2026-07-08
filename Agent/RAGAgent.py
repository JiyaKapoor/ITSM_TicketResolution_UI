from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_mistralai import MistralAIEmbeddings
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.models import Distance,VectorParams
import os
from dotenv import load_dotenv
load_dotenv()
gemini_api_key=os.getenv("GEMINI_API_KEY")
embeddings=MistralAIEmbeddings(model="mistral-embed")
Qdrant_url=os.getenv("Qdrant_url")
Qdrant_api_key=os.getenv("Qdrant_api_key")

client=QdrantClient(url=Qdrant_url,api_key=Qdrant_api_key)
embedding=MistralAIEmbeddings(model="mistral-embed",api_key=os.getenv("MISTRAL_API_KEY"))
LLMModel=ChatGoogleGenerativeAI(model="gemini-3.5-flash",api_key=gemini_api_key)


vectorStore=QdrantVectorStore(client=client,embedding=embedding,collection_name="ITSM_KnowledgeBase")

def provide_resolution(user_query):
    # the first step is to index user query 
    retriever=vectorStore.as_retriever(search_kwargs={"k":3})#this returns top 3 closest document
    docs=retriever.invoke(user_query)
    context="\n\n".join(d.page_content for d in docs)
    prompt=f"""You are an ITSM Desk Support Agent and need to provide resolution for the following user query usign the given context only
    user_query:{user_query}  Context:{context}"""
    response=LLMModel.invoke(prompt)
    resolution_text=""
    if isinstance(response.content, list):
        resolution_text = response.content[0]['text']
    else:
        resolution_text = response.content
    return resolution_text
    
    

