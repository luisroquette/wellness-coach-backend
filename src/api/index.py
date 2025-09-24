from flask import Flask, request, jsonify
from flask_cors import CORS
import openai
import os
import json
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Configurar OpenAI
openai.api_key = os.getenv('OPENAI_API_KEY')

# Simulação de banco de dados em memória (para desenvolvimento)
users_db = {}
analyses_db = {}

@app.route('/api/health', methods=['GET'])
def health_check():
    """Endpoint de health check"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.1.0",
        "firebase_enabled": False
    })

@app.route('/api/generate-summary', methods=['POST'])
def generate_summary():
    """Endpoint original que funciona - mantido para compatibilidade"""
    try:
        data = request.json
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        steps = data.get('steps', 0)
        calories = data.get('calories', 0)
        sleep_hours = data.get('sleep_hours', 0)
        
        # Criar prompt personalizado
        prompt = f"""
        Você é um coach de saúde e bem-estar especializado em análise de dados de atividade física.
        
        Analise os seguintes dados de saúde de hoje:
        - Passos: {steps}
        - Calorias queimadas: {calories}
        - Horas de sono: {sleep_hours}
        
        Forneça uma análise motivacional e personalizada em português brasileiro, incluindo:
        1. Avaliação geral do dia
        2. Pontos positivos
        3. Áreas para melhoria
        4. Dica específica para amanhã
        
        Mantenha o tom encorajador e positivo, com no máximo 150 palavras.
        """
        
        client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Você é um coach de saúde motivacional que fala português brasileiro."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=200,
            temperature=0.7
        )
        
        summary = response.choices[0].message.content.strip()
        
        return jsonify({
            "summary": summary,
            "data": {
                "steps": steps,
                "calories": calories,
                "sleep_hours": sleep_hours
            },
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/register', methods=['POST'])
def register_user():
    """Registro de usuário (simulado sem Firebase)"""
    try:
        data = request.json
        
        required_fields = ['email', 'password', 'name', 'phone', 'city', 'state', 'country']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing field: {field}"}), 400
        
        email = data['email']
        
        # Verificar se usuário já existe
        if email in users_db:
            return jsonify({"error": "User already exists"}), 409
        
        # Simular criação de usuário
        user_id = f"user_{len(users_db) + 1}"
        users_db[email] = {
            "id": user_id,
            "email": email,
            "name": data['name'],
            "phone": data['phone'],
            "city": data['city'],
            "state": data['state'],
            "country": data['country'],
            "created_at": datetime.now().isoformat(),
            "profile_completed": False
        }
        
        return jsonify({
            "message": "User registered successfully",
            "user_id": user_id,
            "email": email
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/login', methods=['POST'])
def login_user():
    """Login de usuário (simulado sem Firebase)"""
    try:
        data = request.json
        
        if 'email' not in data or 'password' not in data:
            return jsonify({"error": "Email and password required"}), 400
        
        email = data['email']
        
        # Verificar se usuário existe
        if email not in users_db:
            return jsonify({"error": "User not found"}), 404
        
        user = users_db[email]
        
        # Simular token (em produção seria JWT)
        token = f"token_{user['id']}_{datetime.now().timestamp()}"
        
        return jsonify({
            "message": "Login successful",
            "token": token,
            "user": {
                "id": user['id'],
                "email": user['email'],
                "name": user['name'],
                "profile_completed": user['profile_completed']
            }
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/onboarding/start', methods=['POST'])
def start_onboarding():
    """Iniciar chat de onboarding"""
    try:
        data = request.json
        user_id = data.get('user_id')
        
        if not user_id:
            return jsonify({"error": "User ID required"}), 400
        
        # Primeira pergunta do onboarding
        welcome_message = """
        Olá! 👋 Bem-vindo ao My Chat Fit! 
        
        Sou sua assistente de saúde e bem-estar. Para personalizar sua experiência, preciso conhecer você melhor.
        
        Vamos começar: Qual é sua idade?
        """
        
        return jsonify({
            "message": welcome_message,
            "step": 1,
            "total_steps": 5,
            "question_type": "age"
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/onboarding/answer', methods=['POST'])
def process_onboarding_answer():
    """Processar resposta do onboarding"""
    try:
        data = request.json
        user_id = data.get('user_id')
        answer = data.get('answer')
        step = data.get('step', 1)
        
        if not user_id or not answer:
            return jsonify({"error": "User ID and answer required"}), 400
        
        # Definir próximas perguntas baseadas no step
        questions = {
            1: {
                "message": "Perfeito! Agora me conte, qual é sua profissão?",
                "question_type": "profession",
                "step": 2
            },
            2: {
                "message": "Interessante! Que tipos de exercícios você pratica ou gostaria de praticar?",
                "question_type": "exercises",
                "step": 3
            },
            3: {
                "message": "Ótimo! Como é sua rotina de trabalho? Você trabalha sentado, em pé, ou se movimenta bastante?",
                "question_type": "work_routine",
                "step": 4
            },
            4: {
                "message": "Entendi! Por último, a que horas você costuma se deitar para dormir?",
                "question_type": "sleep_time",
                "step": 5
            },
            5: {
                "message": """
                Perfeito! 🎉 
                
                Agora tenho todas as informações que preciso para personalizar sua experiência no My Chat Fit!
                
                Com base no seu perfil, vou gerar análises personalizadas dos seus dados de saúde e sugerir melhorias específicas para seu estilo de vida.
                
                Bem-vindo à sua jornada de saúde e bem-estar! 💪
                """,
                "question_type": "completed",
                "step": "completed"
            }
        }
        
        if step < 5:
            next_question = questions.get(step, questions[5])
            return jsonify({
                "message": next_question["message"],
                "step": next_question["step"],
                "total_steps": 5,
                "question_type": next_question["question_type"]
            })
        else:
            # Onboarding completo
            return jsonify({
                "message": questions[5]["message"],
                "step": "completed",
                "total_steps": 5,
                "question_type": "completed",
                "onboarding_completed": True
            })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/analysis/personalized', methods=['POST'])
def generate_personalized_analysis():
    """Gerar análise personalizada baseada no perfil do usuário"""
    try:
        data = request.json
        
        # Dados de saúde
        steps = data.get('steps', 0)
        calories = data.get('calories', 0)
        sleep_hours = data.get('sleep_hours', 0)
        
        # Dados do perfil (simulados ou vindos do onboarding)
        age = data.get('age', 30)
        profession = data.get('profession', 'profissional')
        exercises = data.get('exercises', 'exercícios regulares')
        work_routine = data.get('work_routine', 'trabalho misto')
        sleep_time = data.get('sleep_time', '22:00')
        
        # Criar prompt personalizado
        prompt = f"""
        Você é um coach de saúde personalizado. Analise os dados considerando o perfil específico:
        
        PERFIL DO USUÁRIO:
        - Idade: {age} anos
        - Profissão: {profession}
        - Exercícios preferidos: {exercises}
        - Rotina de trabalho: {work_routine}
        - Horário de dormir: {sleep_time}
        
        DADOS DE HOJE:
        - Passos: {steps}
        - Calorias: {calories}
        - Sono: {sleep_hours}h
        
        Forneça uma análise PERSONALIZADA considerando:
        1. Como os dados se relacionam com a profissão e rotina
        2. Sugestões específicas para os exercícios preferidos
        3. Ajustes baseados no horário de sono
        4. Motivação personalizada para o perfil
        
        Resposta em português brasileiro, máximo 180 palavras, tom motivacional.
        """
        
        client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Você é um coach de saúde que cria análises altamente personalizadas."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=250,
            temperature=0.7
        )
        
        analysis = response.choices[0].message.content.strip()
        
        return jsonify({
            "analysis": analysis,
            "personalized": True,
            "profile_used": {
                "age": age,
                "profession": profession,
                "exercises": exercises,
                "work_routine": work_routine,
                "sleep_time": sleep_time
            },
            "health_data": {
                "steps": steps,
                "calories": calories,
                "sleep_hours": sleep_hours
            },
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/user/profile', methods=['GET'])
def get_user_profile():
    """Obter perfil do usuário"""
    try:
        # Simular busca de perfil
        return jsonify({
            "message": "Profile endpoint ready",
            "note": "Firebase integration pending"
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Endpoint raiz para teste
@app.route('/', methods=['GET'])
def root():
    return jsonify({
        "message": "My Chat Fit API v1.1",
        "status": "running",
        "endpoints": [
            "/api/health",
            "/api/generate-summary",
            "/api/register",
            "/api/login", 
            "/api/onboarding/start",
            "/api/onboarding/answer",
            "/api/analysis/personalized",
            "/api/user/profile"
        ]
    })

if __name__ == '__main__':
    app.run(debug=True)
