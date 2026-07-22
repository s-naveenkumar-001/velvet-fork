from openai import OpenAI

import config


def get_client() -> OpenAI:
    return OpenAI(base_url=config.OPENROUTER_BASE_URL, api_key=config.OPENROUTER_API_KEY)
