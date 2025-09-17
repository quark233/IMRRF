from openai import OpenAI

class LLMRequester:
    def __init__(self):
        self.client = OpenAI(api_key="OPENAI_API_KEY")
    def generate(self, model, prompt):
        response = self.client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0
        )
        return response.choices[0].message.content
    