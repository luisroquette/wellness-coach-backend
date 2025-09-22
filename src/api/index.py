# -*- coding: utf-8 -*-
from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import openai
import logging

# Importar sistema de notificações
from notifications import create_notification_routes, notification_service

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Inicializa o Flask App
app = Flask(__name__)
CORS(app)  # Permite requisições de qualquer origem

# Configura a chave da API da OpenAI a partir de variáveis de ambiente
openai.api_key = os.environ.get("OPENAI_API_KEY")

# Adicionar rotas de notificação
create_notification_routes(app)

# Rota principal para verificar se o servidor está no ar
@app.route("/")
def home():
    return jsonify({
        "status": "healthy",
        "message": "Wellness Coach API está funcionando!",
        "openai_configured": bool(openai.api_key),
        "notifications_available": bool(notification_service.twilio_account_sid or notification_service.sendgrid_api_key)
    })

# Define o endpoint da API em /api/generate-summary
@app.route("/api/generate-summary", methods=['POST'])
def generate_summary_handler():
    """
    Recebe os dados de saúde do app, gera um resumo com a IA e retorna.
    """
    try:
        # 1. Extrai os dados JSON da requisição
        health_data = request.get_json()

        if not health_data:
            return jsonify({"error": "Nenhum dado recebido"}), 400

        # 2. Valida se a chave da API da OpenAI está configurada
        if not openai.api_key:
            return jsonify({"error": "A chave da API da OpenAI não foi configurada no servidor."}), 500

        # Extrair dados de saúde
        steps = health_data.get('steps', 0)
        distance = health_data.get('distance', 0)
        calories = health_data.get('calories', 0)
        sleep_hours = health_data.get('sleep_hours', 0)
        heart_rate = health_data.get('heart_rate', 0)
        exercise_time = health_data.get('exercise_time', 0)

        # 3. Monta a instrução (prompt) para a IA - Estilo "Treinador Motivacional"
        prompt_text = f"""
        Como um coach de wellness motivacional e especialista em saúde, analise os seguintes dados de atividade física e saúde de hoje e crie um resumo personalizado e motivacional em português brasileiro:

        📊 Dados de Hoje:
        - Passos: {steps}
        - Distância percorrida: {distance:.1f} km
        - Calorias queimadas: {calories}
        - Horas de sono: {sleep_hours:.1f}h
        - Frequência cardíaca média: {heart_rate} BPM
        - Tempo de exercício: {exercise_time} minutos

        Crie um resumo motivacional de 2-3 parágrafos que:
        1. Parabenize pelos pontos positivos
        2. Dê dicas específicas para melhorar
        3. Seja encorajador e personalizado
        4. Use emojis apropriados
        5. Mantenha um tom amigável e profissional

        Foque em motivar a pessoa a continuar cuidando da saúde.
        """

        # 4. Chama a API da OpenAI (GPT) - versão 0.28.1
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Você é um coach de wellness experiente e motivacional que ajuda pessoas a melhorar sua saúde e bem-estar."},
                {"role": "user", "content": prompt_text}
            ],
            max_tokens=500,
            temperature=0.7
        )

        # 5. Extrai o texto gerado pela IA
        summary = response.choices[0].message.content.strip()

        # 6. Retorna o resumo gerado em uma resposta JSON
        return jsonify({
            "success": True,
            "summary": summary,
            "data_analyzed": {
                "steps": steps,
                "distance": distance,
                "calories": calories,
                "sleep_hours": sleep_hours,
                "heart_rate": heart_rate,
                "exercise_time": exercise_time
            }
        })

    except Exception as e:
        logger.error(f"Erro ao gerar resumo: {str(e)}")
        return jsonify({"error": f"Ocorreu um erro ao gerar o resumo: {str(e)}"}), 500

@app.route('/api/generate-and-send-summary', methods=['POST'])
def generate_and_send_summary():
    """Gerar resumo com IA e enviar por notificações"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "Dados não fornecidos"}), 400
        
        # Extrair dados de saúde
        health_data = {
            'steps': data.get('steps', 0),
            'distance': data.get('distance', 0),
            'calories': data.get('calories', 0),
            'sleep_hours': data.get('sleep_hours', 0),
            'heart_rate': data.get('heart_rate', 0),
            'exercise_time': data.get('exercise_time', 0)
        }
        
        # Extrair dados do usuário
        user_data = data.get('user_data', {})
        channels = data.get('channels', ['email'])
        
        # Validar se a chave da API da OpenAI está configurada
        if not openai.api_key:
            return jsonify({"error": "A chave da API da OpenAI não foi configurada no servidor."}), 500
        
        # Gerar resumo com IA
        steps = health_data['steps']
        distance = health_data['distance']
        calories = health_data['calories']
        sleep_hours = health_data['sleep_hours']
        heart_rate = health_data['heart_rate']
        exercise_time = health_data['exercise_time']
        
        prompt = f"""
        Como um coach de wellness motivacional e especialista em saúde, analise os seguintes dados de atividade física e saúde de hoje e crie um resumo personalizado e motivacional em português brasileiro:

        📊 Dados de Hoje:
        - Passos: {steps}
        - Distância percorrida: {distance:.1f} km
        - Calorias queimadas: {calories}
        - Horas de sono: {sleep_hours:.1f}h
        - Frequência cardíaca média: {heart_rate} BPM
        - Tempo de exercício: {exercise_time} minutos

        Crie um resumo motivacional de 2-3 parágrafos que:
        1. Parabenize pelos pontos positivos
        2. Dê dicas específicas para melhorar
        3. Seja encorajador e personalizado
        4. Use emojis apropriados
        5. Mantenha um tom amigável e profissional

        Foque em motivar a pessoa a continuar cuidando da saúde.
        """
        
        # Chamar OpenAI API - versão 0.28.1
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Você é um coach de wellness experiente e motivacional que ajuda pessoas a melhorar sua saúde e bem-estar."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500,
            temperature=0.7
        )
        
        summary = response.choices[0].message.content.strip()
        
        # Enviar notificações
        notification_results = notification_service.send_wellness_summary(
            user_data, summary, channels
        )
        
        return jsonify({
            "success": True,
            "summary": summary,
            "data_analyzed": health_data,
            "notification_results": notification_results
        })
        
    except Exception as e:
        logger.error(f"Erro ao gerar e enviar resumo: {str(e)}")
        return jsonify({"error": f"Erro interno: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5001)
