import os
from dotenv import load_dotenv

from langchain_groq import ChatGroq
from google import genai


# Load environment variables from a .env file
load_dotenv()

def get_gemini_flash_llm(prompt_text: str):
    """Initializes and returns the Google Gemini 1.5 Flash model."""
    # Ensure the Google API key is available
    if not os.getenv("GOOGLE_API_KEY"):
        raise ValueError("GOOGLE_API_KEY not found in environment variables.")
    
    client = genai.Client()
    response = client.models.generate_content(
    
    model="gemini-2.5-flash",
    contents=prompt_text,
    )

    return response.text

def get_llama3_groq_response(prompt_text: str) -> str:
    """
    Invokes the Llama 3 model on Groq with a prompt and returns the text response.

    Args:
        prompt_text: The complete prompt to send to the model.

    Returns:
        The model's generated text response as a string.
    """
    # Ensure the Groq API key is available
    if not os.getenv("GROQ_API_KEY"):
        raise ValueError("GROQ_API_KEY not found in environment variables.")
        
    try:
        # Initialize the ChatGroq model
        llm = ChatGroq(
            model_name="llama-3.1-8b-instant",
            temperature=0
        )
        
        # Invoke the model and get the response
        response = llm.invoke(prompt_text)
        
        # The response object has a 'content' attribute holding the string
        return response.content
        
    except Exception as e:
        print(f"An error occurred with Groq/Llama 3: {e}")
        return ""

# --- Main Execution ---
if __name__ == "__main__":
    # --- Task 1: Generating Vector Search Query with the new function ---
    print("--- Task 1: Generating Vector Search Query with Llama 3 on Groq ---")
    
    # Define the instructions and the user question
    system_prompt = "You are an expert at creating vector search queries. Your task is to take a user's question about an SEC filing and generate a concise, keyword-rich search query to find the most relevant information. Only output the search query, with no preamble."
    user_question = "What were the main financial risks for Tesla mentioned in their last 10-K filing?"
    
    # Combine them into a single prompt string
    full_prompt = f"{system_prompt}\n\nUser Question: {user_question}"
    
    print(f"Original Question: {user_question}")
    
    # Call the new, simplified function
    vector_search_query = get_llama3_groq_response(full_prompt)
    
    if vector_search_query:
        print(f"Generated Search Query: {vector_search_query}\n")


    # --- Task 2: Gemini
    
    user_question = "What were the main financial risks for Tesla mentioned in their last 10-K filing?"
    retrieved_context = """
    Item 1A. Risk Factors.
    Our business is subject to a wide range of risks. The most significant of these include, but are not limited to:
    1. Competition in the automotive market: The automotive market is highly competitive.
    2. Supply chain disruptions: Our production relies on a global supply chain for components.
    3. Regulatory changes: Our business is subject to extensive regulations.
    """

    # We construct the full prompt for the model
    full_prompt = f"""
    You are an AI assistant specializing in financial document analysis. 
    Answer the user's question based *only* on the provided context from the SEC filing.
    
    CONTEXT:
    {retrieved_context}
    
    QUESTION:
    {user_question}
    """
    
    # Get the response
    final_answer = get_gemini_flash_llm(full_prompt)
    
    if final_answer:
        print(f"\nSynthesized Answer:\n{final_answer}")