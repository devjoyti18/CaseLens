# from langchain_ollama import ChatOllama
# from langchain_core.messages import SystemMessage, HumanMessage

# # Initialize LLM once
# llm = ChatOllama(
#     model="mistral", 
#     temperature=0
# )


# def generate_answer(query: str, documents) -> str:
    
#     #Converts retrieved chunks into a grounded answer
    
#     if not documents:
#         return "I don't have enough information to answer that question based on the provided documents."

#     context = "\n\n".join(doc.page_content for doc in documents)

#     messages = [
#         SystemMessage(
#             content=(
#                 "You are a legal assistant. "
#                 "Answer the question using ONLY the provided context. "
#                 "If the answer is not present, say you do not know."
#             )
#         ),
#         HumanMessage(
#             content=f"""     
#         Question:
#         {query}

#         Context:
#         {context}
#         """
#         )
#     ]

#     response = llm.invoke(messages)
#     return response.content





















# #VERSION 2.1 -> Uses Ollama and local RAM

# from langchain_ollama import ChatOllama
# from langchain_core.messages import SystemMessage, HumanMessage

# SYSTEM_PROMPT = """You are an expert legal assistant helping lawyers query their previous case documents.

# Your behaviour rules:
# - Answer using ONLY the provided context. Never use outside knowledge.
# - If the answer is not in the context, say: "The provided case documents do not contain sufficient information to answer this question."
# - Always cite the specific case (appellant v. respondent), citation, and page number your answer draws from.
# - If multiple cases are relevant, address each separately and clearly.
# - Use precise legal language. Do not simplify or paraphrase holdings.
# - If asked what a court decided, quote the holding directly from the context.
# - Never speculate or infer beyond what is explicitly stated in the context.
# """

# # Initialize LLM once
# # llm = ChatOllama(
# #     model="mistral",
# #     temperature=0,          # deterministic — critical for legal accuracy
# #     num_ctx=4096,           # extend context window to fit multiple chunks
# # )

# llm = ChatOllama(
#     model="phi3",
#     temperature=0,
#     num_ctx=4096,
# )


# def generate_answer(query: str, documents) -> str:
#     """
#     Generate a grounded legal answer from retrieved chunks.

#     Args:
#         query:     The lawyer's natural language question.
#         documents: Retrieved Document chunks from retrieve_chunks().
#     """

#     if not documents:
#         return "The provided case documents do not contain sufficient information to answer this question."

#     # Build context with source metadata so the LLM can cite correctly
#     context_parts = []
#     for i, doc in enumerate(documents, 1):
#         m = doc.metadata
#         header = (
#             f"[Source {i}] "
#             f"{m.get('appellant', 'Unknown')} v. {m.get('respondent', 'Unknown')} | "
#             f"Citation: {m.get('citation', 'N/A')} | "
#             f"Date: {m.get('judgment_date', 'N/A')} | "
#             f"Outcome: {m.get('outcome', 'N/A')} | "
#             f"Section: {m.get('section_type', 'N/A')} | "
#             f"Page: {m.get('page', 'N/A')}"
#         )
#         context_parts.append(f"{header}\n{doc.page_content}")

#     context = "\n\n---\n\n".join(context_parts)

#     messages = [
#         SystemMessage(content=SYSTEM_PROMPT),
#         HumanMessage(content=(
#             f"Question:\n{query}\n\n"
#             f"Case Document Context:\n{context}"
#         )),
#     ]

#     response = llm.invoke(messages)
#     return response.content





#VERSION 2.2 -> Uses Groq and cloud(updated in pipeline.py to use Groq instead of Ollama)
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
from dotenv import load_dotenv
import os

load_dotenv()  # Load environment variables from .env file

# SYSTEM_PROMPT = """You are an expert legal assistant helping lawyers query their previous case documents.

# Your behaviour rules:
# - Answer using ONLY the provided context. Never use outside knowledge.
# - If the answer is not in the context, say: "The provided case documents do not contain sufficient information to answer this question."
# - Always cite the specific case (appellant v. respondent), citation, and page number your answer draws from.
# - If multiple cases are relevant, address each separately and clearly.
# - Use precise legal language. Do not simplify or paraphrase holdings.
# - If asked what a court decided, quote the holding directly from the context.
# - Never speculate or infer beyond what is explicitly stated in the context.
# """

SYSTEM_PROMPT = """You are an expert legal assistant helping lawyers query their previous case documents.

Your behaviour rules:
- You will receive multiple document chunks. First identify which chunks are relevant to the question, ignore the rest.
- Answer using ONLY the relevant chunks. Never use outside knowledge.
- If the answer is not in the context, say: "The provided case documents do not contain sufficient information to answer this question."
- Always cite the specific case (appellant v. respondent), citation, and page number your answer draws from.
- If multiple cases are relevant, address each separately and clearly.
- Use precise legal language. Do not simplify or paraphrase holdings.
- If asked what a court decided, quote the holding directly from the context.
- Never speculate or infer beyond what is explicitly stated in the context.
"""

# Initialize LLM once
llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0,
    api_key=os.getenv("GROQ_API_KEY"),
)


def generate_answer(query: str, documents) -> str:
    """
    Generate a grounded legal answer from retrieved chunks.

    Args:
        query:     The lawyer's natural language question.
        documents: Retrieved Document chunks from retrieve_chunks().
    """

    if not documents:
        return "The provided case documents do not contain sufficient information to answer this question."

    # Build context with source metadata so the LLM can cite correctly
    context_parts = []
    for i, doc in enumerate(documents, 1):
        m = doc.metadata
        header = (
            f"[Source {i}] "
            f"{m.get('appellant', 'Unknown')} v. {m.get('respondent', 'Unknown')} | "
            f"Citation: {m.get('citation', 'N/A')} | "
            f"Date: {m.get('judgment_date', 'N/A')} | "
            f"Outcome: {m.get('outcome', 'N/A')} | "
            f"Section: {m.get('section_type', 'N/A')} | "
            f"Page: {m.get('page', 'N/A')}"
        )
        context_parts.append(f"{header}\n{doc.page_content}")

    context = "\n\n---\n\n".join(context_parts)

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=(
            f"Question:\n{query}\n\n"
            f"Case Document Context:\n{context}"
        )),
    ]

    response = llm.invoke(messages)
    return response.content