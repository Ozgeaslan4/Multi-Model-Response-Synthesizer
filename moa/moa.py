import asyncio
import aiohttp

API_KEY = "sk-FiRShAQH8Wxx4BxeWGF4L7v7MGYSXjkkg"  # Replace with your actual API key
API_URL = "https://litellm.unknownland.org"  # Base URL for the OpenAI API

user_prompt = "how can i make cake?"
aggregator_model = "mistralai/Mixtral-8x22B-Instruct-v0.1"
aggregator_system_prompt = """You have been provided with a set of responses from various open-source models to the latest user query. Your task is to synthesize these responses into a single, high-quality response. It is crucial to critically evaluate the information provided in these responses, recognizing that some of it may be biased or incorrect. Your response should not simply replicate the given answers but should offer a refined, accurate, and comprehensive reply to the instruction. Ensure your response is well-structured, coherent, and adheres to the highest standards of accuracy and reliability.

Responses from models:"""

async def fetch_models(session):
    """Fetch the list of available models from the API."""
    async with session.get(f"{API_URL}/models", headers={"Authorization": f"Bearer {API_KEY}"}) as response:
        response_data = await response.json()
        if 'data' in response_data:
            return [model['id'] for model in response_data['data']]
        else:
            print("Error fetching models:", response_data)
            return []

async def run_llm(session, model):
    """Run a single LLM call with a reference model."""
    try:
        async with session.post(
            f"{API_URL}/chat/completions",
            json={
                "model": model,
                "messages": [{"role": "user", "content": user_prompt}],
                "temperature": 0.7,
                "max_tokens": 512,
            },
            headers={"Authorization": f"Bearer {API_KEY}"}
        ) as response:
            response_data = await response.json()
            if "choices" in response_data:
                return response_data["choices"][0]["message"]["content"]
            else:
                print(f"Unexpected response structure: {response_data}")
                return None
    except aiohttp.ClientResponseError as e:
        if e.status == 429:
            print(f"Rate limit exceeded for model {model}. Retrying after a delay.")
            await asyncio.sleep(1)
            return await run_llm(session, model)
        else:
            print(f"Error with model {model}: {e}")
            return None

async def main():
    async with aiohttp.ClientSession() as session:
        # Fetch the list of available models
        models = await fetch_models(session)
        if not models:
            print("No models available. Exiting.")
            return

        print(f"Available models: {models}")

        # Filter models if necessary
        reference_models = [model for model in models if model.startswith("gpt-") or model.startswith("TheBloke")]

        if not reference_models:
            print("No suitable models found. Exiting.")
            return

        results = await asyncio.gather(*[run_llm(session, model) for model in reference_models])
        results = [result for result in results if result]  # Filter out None results

        if not results:
            print("No successful results. Exiting.")
            return

        async with session.post(
            f"{API_URL}/chat/completions",
            json={
                "model": aggregator_model,
                "messages": [
                    {"role": "system", "content": aggregator_system_prompt},
                    {"role": "user", "content": "\n\n".join(results)},
                ],
                "temperature": 0.7,
                "max_tokens": 512,
            },
            headers={"Authorization": f"Bearer {API_KEY}"}
        ) as response:
            response_data = await response.json()
            if "choices" in response_data:
                print(response_data["choices"][0]["message"]["content"])
            else:
                print(f"Unexpected response structure: {response_data}")

asyncio.run(main())








