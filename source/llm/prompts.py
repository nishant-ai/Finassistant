def create_vector_query_prompt(question: str, num_queries: int = 3) -> str:
    """
    Creates a specific prompt to generate multiple vector search queries.

    Args:
        question: The original user question.
        num_queries: The number of search queries to generate.

    Returns:
        A formatted prompt string to be sent to the LLM.
    """
    return f"""
You are an expert AI at query expansion for financial document retrieval. 
Your task is to take a user's question and generate {num_queries} distinct, concise, and keyword-rich search queries.
The queries should be optimized to find the most relevant text chunks in a vector database containing SEC filings.
Focus on key terms, entities, and financial concepts.
Output ONLY the queries as a numbered list, with no preamble or explanation.

--- USER QUESTION ---
{question}
"""

def create_synthesis_prompt(question: str, context: str) -> str:
    """
    Creates a specific prompt for synthesizing an answer from retrieved context.

    Args:
        question: The original user question.
        context: The text context retrieved from the vector store.

    Returns:
        A formatted prompt string to be sent to the LLM.
    """
    return f"""
You are a highly specialized AI assistant for financial analysis. Your goal is to answer the user's question with precision and conciseness.

You MUST answer the question based *exclusively* on the provided 'CONTEXT' below. Do not use any external knowledge or make assumptions.
If the information in the 'CONTEXT' is insufficient to answer the question, you must explicitly state that the answer cannot be found in the provided text.

--- CONTEXT FROM SEC FILING ---
{context}

--- USER QUESTION ---
{question}

--- ANSWER ---
"""