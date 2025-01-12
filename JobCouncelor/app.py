"""Job Councelor for Data Science Jobs
"""

import os
import time
from dotenv import load_dotenv
import gradio as gr
from openai import OpenAI
import pandas as pd

# Updated imports for newer LangChain versions
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain.text_splitter import CharacterTextSplitter
from langchain.schema import Document
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import FAISS
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationalRetrievalChain
from langchain_core.callbacks import StdOutCallbackHandler
from langchain.prompts import PromptTemplate
from langchain.prompts.chat import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
)

load_dotenv()
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
MODEL = "gpt-4o-mini"
DB_NAME = "vector_db"

def read_job_data(file_path: str) -> pd.DataFrame:
    df = pd.read_csv(file_path)
    print(f"Successfully loaded {len(df)} job entries")
    return df

def prepare_documents(df: pd.DataFrame) -> list[Document]:
    documents = []
    for index, row in df.iterrows():
        documents.append(Document(page_content=f"Title: {row['title']}\nEmployer: {row['company']}\nDescription: {row['description']}", 
                                  metadata={"title": row['title'], "company": row['company']}))
    return documents

def create_vector_db(documents: list[Document]) -> None:
    """Create a vector database from the documents (from scratch)
    """
    text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    texts = text_splitter.split_documents(documents)
    embeddings = OpenAIEmbeddings()
    vectorstore = FAISS.from_documents(texts, embeddings)
    vectorstore.save_local(DB_NAME)
    print(f"Vector database created and saved to {DB_NAME}")
    return vectorstore

def _create_prompt_template(system_template: str) -> ChatPromptTemplate:

    messages = [
        SystemMessagePromptTemplate.from_template(system_template),
        HumanMessagePromptTemplate.from_template("{question}")
    ]
    return ChatPromptTemplate.from_messages(messages)

def create_chat_assistant(vectorstore: FAISS, verbose: bool = False) -> ConversationalRetrievalChain:
    """Create chat assistant by using a retrieval chain from the vector database. 
    """
    memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
    system_prompt = """You are a helpful job counselor specializing in data science positions. 
    Engage in a friendly and conversational manner. When discussing job positions, weave the key details naturally into your responses without listing them numerically but highlight the most important words. 
    Ask questions to get more information from the user and keep the conversation going. Keep your responses concise, try to be less than 700 characters.
    If the user asks about a specific job position, provide a detailed answer including the company name, job title, and key requirements or responsibilities.
    Use the following pieces of context to answer the user's questions:
    {context}
    """
    prompt = _create_prompt_template(system_prompt)
    retrieval_chain = ConversationalRetrievalChain.from_llm(
        llm=ChatOpenAI(model=MODEL),
        retriever=vectorstore.as_retriever(search_kwargs={"k": 10} ),
        memory=memory,
        combine_docs_chain_kwargs={"prompt": prompt},
        callbacks=[StdOutCallbackHandler()] if verbose else []
    )
    return retrieval_chain


def main() -> None:
    df = read_job_data("data/jobs.csv")
    documents = prepare_documents(df)
    vectorstore = create_vector_db(documents)
    chat_assistant = create_chat_assistant(vectorstore, verbose=False) 

    # UI
    def chat_wrapper(message: str, history: list) -> str:
        result = chat_assistant.invoke({"question": message})
        return result["answer"]

    gr.ChatInterface(
        fn=chat_wrapper,
        title="Job Councelor",
    ).launch()


if __name__ == "__main__":
    main()        