import time
import logfire
from app.config import settings
from app.agents.state import AgentState
from app.gateway import portkey_client, extract_cache_status


def generate_node(state: AgentState):
    """
    Synthesizes a response using both Documentation Context AND Conversation History.
    Uses the native Portkey client (not LangChain) so we can read the
    x-portkey-cache-status response header and surface Cache: Hit in the UI.
    """
    query = state["current_query"]

    history_str = ""
    for msg in state["messages"][:-1]:
        role = "User" if msg["role"] == "user" else "Assistant"
        history_str += f"{role}: {msg['content']}\n"

    user_msg = state["messages"][-1]["content"] if state["messages"] else ""

    if query == "CONVERSATIONAL":
        logfire.info("Generating conversational CloudSec IR response using memory.")
        prompt = f"""
        You are CloudSec IR Lead, an expert Cloud Incident Response Specialist.
        Answer the security analyst's latest message politely using the CONVERSATION HISTORY below.

        CONVERSATION HISTORY:
        {history_str}

        LATEST MESSAGE:
        "{user_msg}"
        """
    else:
        logfire.info("Generating technical CloudSec IR RAG response.")
        max_context_chars = 6000
        full_context = ""

        for doc in state["documents"]:
            if len(full_context) + len(doc) < max_context_chars:
                full_context += doc + "\n\n"
            else:
                logfire.warning("Context truncated to fit Groq TPM limits.")
                break

        prompt = f"""
        You are CloudSec IR Lead, a Senior Cloud Security Incident Investigator.
        Answer the incident response question using ONLY the CLOUD SECURITY CONTEXT provided below.
        
        Structuring Guidelines:
        - Provide structured response: Incident Summary, Evidence/Log Analysis, Likely Attack Path / ATT&CK Mapping, Immediate Containment Steps, and Eradication/Recovery.
        - Separate clear facts from hypotheses.
        - Never invent fake IP addresses, AWS/GCP account IDs, timestamps, or cloud resources not in the context.
        - If evidence in context is insufficient, explicitly state evidence gaps.

        CLOUD SECURITY CONTEXT:
        {full_context}

        CONVERSATION HISTORY:
        {history_str}

        SECURITY INCIDENT QUESTION:
        "{user_msg}"
        """

    with logfire.span("✍️ LLM Synthesis"):
        try:
            response = None
            for attempt in range(3):
                try:
                    response = portkey_client.chat.completions.create(
                        model=f"@{settings.GROQ_SLUG}/{settings.GROQ_MODEL}",
                        messages=[{"role": "user", "content": prompt}],
                        temperature=0.1
                    )
                    break
                except Exception as e:
                    err_str = str(e).lower()
                    if ("429" in err_str or "rate_limit" in err_str) and attempt < 2:
                        wait_time = 2 * (attempt + 1)
                        logfire.warning(f"Groq 429 Rate limit — retrying in {wait_time}s (attempt {attempt + 1}/3)...")
                        time.sleep(wait_time)
                    else:
                        raise e

            content = response.choices[0].message.content
            cache_status = extract_cache_status(response)
            is_cache_hit = cache_status == "HIT"

            if is_cache_hit:
                logfire.info("⚡ Gateway Cache Hit — response served from Portkey cache.")
                plan_update = state["plan"] + ["Cache: Hit ⚡"]
                status = "Cache hit — instant response."
            else:
                logfire.info("✅ Response synthesised via LLM.")
                plan_update = state["plan"]
                status = "Response generated."

            return {
                "final_answer": content,
                "status": status,
                "plan": plan_update,
                "messages": [{"role": "assistant", "content": content}]
            }

        except Exception as e:
            logfire.error(f"LLM Generation failed: {e}")
            raise e
