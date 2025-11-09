import ollama

def analyze_sentiment(texts):
    sentiment_results = []
    for text in texts:
        response = ollama.chat(
            model="gpt4all",
            messages=[
                {
                    "role": "user",
                    "content": f"Analizza il sentiment di questo testo e ritorna 'Positivo', 'Neutro' o 'Negativo':\n{text}"
                }
            ]
        )
        sentiment_results.append(response["message"]["content"])
    return sentiment_results