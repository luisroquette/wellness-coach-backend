# -*- coding: utf-8 -*-
from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import openai

# Inicializa o Flask App
app = Flask(__name__)
CORS(app)  # Permite requisições de qualquer origem

# Configura a chave da API da OpenAI a partir de variáveis de ambiente
openai.api_key = os.environ.get("OPENAI_API_KEY")

# Define o endpoint da API em /api/generate-summary
@app.route("/api/generate-summary", methods=['POST'])
def generate_summary_handler():
    """
    Recebe os dados de saúde do app, gera um resumo com a IA e retorna.
    """
    # 1. Extrai os dados JSON da requisição
    health_data = request.get_json()

    if not health_data:
        return jsonify({"error": "Nenhum dado recebido"}), 400

    # 2. Valida se a chave da API da OpenAI está configurada
    if not openai.api_key:
        return jsonify({"error": "A chave da API da OpenAI não foi configurada no servidor."}), 500

    # 3. Monta a instrução (prompt) para a IA - Estilo "Treinador Motivacional"
    try:
        prompt_text = f"""
        Analise os seguintes dados de saúde de um usuário em formato JSON e gere um resumo curto, motivacional e amigável em português do Brasil.

        **Regras do Resumo:**
        - Comece com uma saudação positiva e energética.
        - Celebre as metas atingidas (calorias, tempo de exercício).
        - Analise a qualidade do sono, destacando pontos positivos como a duração e o tempo em sono profundo.
        - Se houver uma tendência de queda (como em passos ou distância), aborde de forma gentil, como um desafio ou sugestão para o dia seguinte, sem tom de crítica.
        - Termine com uma frase de encorajamento.
        - O tom deve ser de um "Treinador Motivacional", não de um relatório médico.

        **Dados do Usuário:**
        {health_data}
        """

        # 4. Chama a API da OpenAI (GPT)
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Você é um coach de bem-estar e saúde, especialista em interpretar dados e motivar pessoas."},
                {"role": "user", "content": prompt_text}
            ],
            temperature=0.7,  # Um pouco de criatividade
            max_tokens=250    # Limita o tamanho da resposta
        )

        # 5. Extrai o texto gerado pela IA
        summary = response.choices[0].message.content.strip()

        # 6. Retorna o resumo gerado em uma resposta JSON
        return jsonify({"summary": summary})

    except Exception as e:
        # Retorna uma mensagem de erro genérica se algo falhar
        return jsonify({"error": f"Ocorreu um erro ao gerar o resumo: {str(e)}"}), 500

# Rota principal para verificar se o servidor está no ar
@app.route("/")
def home():
    return "Servidor do Wellness Coach AI está no ar."

if __name__ == "__main__":
    app.run(debug=True)
