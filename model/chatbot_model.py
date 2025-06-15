import os
import re
import ollama
import threading
import time
from shared_utils import *  # Make sure this imports your updated shared_utils.py

# --- GLOBAL CONFIGURATION ---
GENERATION_MODEL = "qwen2:7b-instruct"

# --- CONVERSATION HISTORY (Unchanged) ---
_conversation_lock = threading.Lock()
_conversation_history = {}


def get_conversation_context(session_id, max_history=3):
    with _conversation_lock:
        history = _conversation_history.get(session_id, [])
        recent_history = history[-max_history:]
        context_parts = []
        for entry in recent_history:
            context_parts.append(f"Previous Q: {entry['query']}")
            context_parts.append(f"Previous A: {entry['response'][:200]}...")
        return "\n".join(context_parts)


def save_conversation(session_id, query, response, document):
    with _conversation_lock:
        if session_id not in _conversation_history:
            _conversation_history[session_id] = []
        _conversation_history[session_id].append({
            'query': query,
            'response': response,
            'document': document,
            'timestamp': time.time()
        })
        if len(_conversation_history[session_id]) > 10:
            _conversation_history[session_id] = _conversation_history[session_id][-10:]


# --- FINAL, HYBRID RESPONSE GENERATION ---

def generate_llm_response(query, document_name=None, category=None, session_id=None):
    start_time = time.time()
    clean_query = preprocess_query(query)
    context = None
    conversation_context = ""
    clause_ref = None

    if session_id:
        conversation_context = get_conversation_context(session_id)

    # --- HYBRID RETRIEVAL STRATEGY ---

    # 1. Primary Strategy: Attempt PRECISE clause extraction.
    clause_pattern = r'(\d+(\.\d+)*)'  # More robust pattern for clauses like 10.0, 2.2.1 etc.
    clause_match = re.search(clause_pattern, clean_query)
    if clause_match:
        clause_ref = clause_match.group(1).strip()
        print(f"[DEBUG] Clause pattern matched: {clause_ref}. Attempting precise extraction.")

        search_target_name = document_name or category
        results = extract_clause_section(document_name=document_name, clause_ref=clause_ref, category=category)
        if results:
            context = "\n\n---\n\n".join([f"From document '{res['document']}':\n{res['text']}" for res in results])
            print(f"[DEBUG] SUCCESS: Precisely extracted context for clause {clause_ref}.")

    # 2. Fallback Strategy: If precise extraction failed or wasn't triggered, use SEMANTIC search.
    if not context and (category or document_name):
        print(
            f"[DEBUG] Precise extraction failed or not applicable. Falling back to semantic search for query: '{clean_query}'")
        search_target = category if category else document_name
        best_chunks = semantic_search(clean_query, document_name, top_k=3, category=category)

        if best_chunks:
            context = "\n\n---\n\n".join(best_chunks)
            print(f"[DEBUG] SUCCESS: Found context via semantic search.")

    # 3. Handle "Not Found" case if both strategies fail.
    if not context:
        if clause_ref:
            response_text = f"Information for clause '{clause_ref}' could not be found in the '{category}' documents. Please check the clause number or rephrase your query."
        else:
            response_text = f"Sorry, no relevant information was found for your query: '{query}' in the '{category}' documents. Please try rephrasing."

        if session_id:
            save_conversation(session_id, query, response_text, category)
        return {"response": response_text, "context": "", "document": category}

    # Truncate context if it's too long.
    if len(context) > 7000:  # Increased context size
        context = context[:7000] + "..."

    # --- PROMPT AND LLM CALL (Your excellent prompt is unchanged) ---
    prompt = f"""You are a compliance and policy extraction assistant for Steel Authority of India Limited (SAIL).

{f"Previous conversation context: {conversation_context}" if conversation_context else ""}

Below is an excerpt from an official policy document. Your task is to:

1. Extract and enumerate every single clause, point, subpoint, number, requirement, exception, and procedural step exactly as written in the context. Do NOT summarize, rephrase, or omit anything. Use a numbered or bullet list, preserving the order and wording from the context.
2. For each point and subpoint, provide a clear, plain-language explanation immediately after it.
3. If this appears to be a follow-up question based on the conversation history, remember the previous context and build upon it.
4. DO NOT AT ALL COSTS:
- Give a paraphrased summary
- Omit any point/clause/subpoint/topic/any no.
- Use Inaccurate terms
5. List every clause, rule, and subpoint exactly as written, in the order presented.
6. After each clause, provide a plain-language explanation.

If the context is incomplete, then u have two options:
a) If some partial content is relevant build only upon that and inform the user of in-sufficiency of information.
b) If no content is absolutely not relevant say :"No relevant information found."

Context:
{context}

Question: {query}

Answer:
Firstly, print all content in policy as is no changes at all. Then, immediately after, provide a clear explanation in natural language. Do not skip any clause, subpoint, or number. Do not summarize or omit anything. Please do not skip any point or subpoint or terms.
"""

    print(f"[DEBUG] Sending prompt to Ollama generation model: {GENERATION_MODEL}")
    print("=" * 80)
    print("[DEBUG] CONTEXT SENT TO OLLAMA:")
    print(context)
    print("=" * 80)

    try:
        response = ollama.generate(
            model=GENERATION_MODEL,
            prompt=prompt,
            options={
                "temperature": 0.2,
                "num_predict": 4096,  # Increased prediction length for long policies
                "num_ctx": 8192,  # Increased context window
            }
        )
        response_text = response["response"]
        if session_id:
            save_conversation(session_id, query, response_text, category)
        print(f"[PERF] Total query time: {time.time() - start_time:.2f}s")
        return {"response": response_text, "context": context, "document": category}
    except Exception as e:
        print(f"[ERROR] Ollama generation failed: {e}")
        error_response = "I'm having trouble generating a response. Please try again."
        if session_id:
            save_conversation(session_id, query, error_response, category)
        return {"response": error_response, "context": context, "document": category}

