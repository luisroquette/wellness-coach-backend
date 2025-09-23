# -*- coding: utf-8 -*-
from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from openai import OpenAI

# Inicializa o Flask App
app = Flask(__name__)
CORS(app)  # Permite requisições de qualquer origem

# Configura o cliente da OpenAI a partir de variáveis de ambiente
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# Define o endpoint da API em /api/generate-summary
@app.route("/api/generate-summary", methods=['POST'])
def generate_summary_handler():
    health_data = request.get_json()

    if not health_data:
        return jsonify({"error": "Nenhum dado recebido"}), 400

    if not client.api_key:
        return jsonify({"error": "A chave da API da OpenAI não foi configurada no servidor."}), 500

    try:
        prompt_text = f"""
        Analise os seguintes dados de saúde de um usuário em formato JSON e gere um resumo curto, motivacional e amigável em português do Brasil.

        **Regras do Resumo:**
        - Comece com uma saudação positiva e energética.
        - Celebre as metas atingidas (calorias, tempo de exercício).
        - Analise a qualidade do sono, destacando pontos positivos como a duração e o tempo em sono profundo.
        - Se houver uma tendência de queda (como em passos ou distância), aborde de forma gentil, como um desafio ou sugestão para o dia seguinte, sem tom de crítica.
        - Termine com uma frase de encorajamento.
        - O tone deve ser de um "Treinador Motivacional", não de um relatório médico.

        **Dados do Usuário:**
        {health_data}
        """

        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {"role": "system", "content": "Você é um coach de bem-estar e saúde, especialista em interpretar dados e motivar pessoas."},
                {"role": "user", "content": prompt_text}
            ],
            temperature=0.7,
            max_tokens=250
        )

        summary = response.choices[0].message.content.strip()
        return jsonify({"summary": summary})

    except Exception as e:
        return jsonify({"error": f"Ocorreu um erro ao gerar o resumo: {str(e)}"}), 500

# Rota principal para verificar se o servidor está no ar
@app.route("/")
def home():
    return "Servidor do Wellness Coach AI está no ar."

