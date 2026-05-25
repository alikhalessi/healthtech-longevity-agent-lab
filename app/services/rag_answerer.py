import os
from dotenv import load_dotenv
from openai import OpenAI

from app.schemas.rag_schema import RAGAnswer, RetrievedContext
from app.services.vector_store import semantic_search


load_dotenv(override=True)


RAG_SYSTEM_PROMPT = """
You are a cautious health-tech and longevity RAG assistant.

You must answer using only the retrieved context provided by the system.
Do not use outside knowledge.
Do not invent citations, sources, mechanisms, or claims.
If the retrieved context is insufficient, say so clearly.

Safety boundary:
- No medical diagnosis.
- No treatment advice.
- No medication adjustment.
- No personalized clinical decision-making.

Your job:
- Answer the user's question from the retrieved chunks.
- Summarize what the retrieved evidence says.
- Explain limitations.
- Stay conservative.
- Mention when evidence is theoretical, animal-based, preliminary, or not directly human clinical evidence.
"""


def get_openai_client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        raise RuntimeError("OPENAI_API_KEY was not found. Check your local .env file.")

    return OpenAI(api_key=api_key)


def build_context_block(results: list[dict]) -> str:
    context_parts = []

    for index, result in enumerate(results, start=1):
        context_parts.append(
            f"""
[CONTEXT {index}]
chunk_id: {result['chunk_id']}
source_title: {result['source_title']}
source_type: {result['source_type']}
chunk_index: {result['chunk_index']}
similarity_score: {result['similarity_score']}
text:
{result['text']}
"""
        )

    return "\n".join(context_parts)


def answer_question_with_rag(
    question: str,
    limit: int = 5,
) -> RAGAnswer:
    results = semantic_search(query=question, limit=limit)

    if not results:
        raise RuntimeError(
            "No embedding records found or no semantic matches. Build chunks and embeddings first."
        )

    context_block = build_context_block(results)

    retrieved_context = [
        RetrievedContext(
            chunk_id=result["chunk_id"],
            source_title=result["source_title"],
            chunk_index=result["chunk_index"],
            similarity_score=result["similarity_score"],
            text_preview=result["text"][:300],
        )
        for result in results
    ]

    client = get_openai_client()
    model = os.getenv("OPENAI_MODEL", "gpt-5.5")

    user_prompt = f"""
Question:
{question}

Retrieved context:
{context_block}

Answer using only the retrieved context.
If the retrieved context does not fully answer the question, say what is missing.
"""

    response = client.responses.parse(
        model=model,
        input=[
            {
                "role": "system",
                "content": RAG_SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": user_prompt,
            },
        ],
        text_format=RAGAnswer,
    )

    parsed = response.output_parsed

    return parsed.model_copy(
        update={
            "question": question,
            "retrieved_context": retrieved_context,
        }
    )
