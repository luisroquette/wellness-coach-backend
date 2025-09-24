# -*- coding: utf-8 -*-
from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import json
from datetime import datetime, timezone
import firebase_admin
from firebase_admin import credentials, firestore, auth
from openai import OpenAI

# Inicializa o Flask App
app = Flask(__name__)
CORS(app)  # Permite requisições de qualquer origem

# Configura o cliente da OpenAI
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# Inicializa Firebase Admin SDK
def initialize_firebase():
    """Inicializa o Firebase Admin SDK"""
    try:
        # Verifica se já foi inicializado
        firebase_admin.get_app()
    except ValueError:
        # Inicializa com credenciais do ambiente
        firebase_config = os.environ.get("FIREBASE_CONFIG")
        if firebase_config:
            # Parse das credenciais do ambiente
            cred_dict = json.loads(firebase_config)
            cred = credentials.Certificate(cred_dict)
        else:
            # Fallback para arquivo de credenciais (desenvolvimento)
            cred = credentials.ApplicationDefault()
        
        firebase_admin.initialize_app(cred)

# Inicializa Firebase
initialize_firebase()
db = firestore.client()

# ============================================================================
# ENDPOINTS DE AUTENTICAÇÃO
# ============================================================================

@app.route("/api/auth/register", methods=['POST'])
def register_user():
    """
    Registra um novo usuário no Firebase Auth e salva dados no Firestore
    """
    try:
        data = request.get_json()
        
        # Validação dos dados obrigatórios
        required_fields = ['email', 'password', 'name', 'phone', 'city', 'state', 'country']
        for field in required_fields:
            if not data.get(field):
                return jsonify({"error": f"Campo obrigatório: {field}"}), 400
        
        # Cria usuário no Firebase Auth
        user = auth.create_user(
            email=data['email'],
            password=data['password'],
            display_name=data['name']
        )
        
        # Dados do usuário para o Firestore
        user_data = {
            'personal_info': {
                'name': data['name'],
                'email': data['email'],
                'phone': data['phone'],
                'city': data['city'],
                'state': data['state'],
                'country': data['country']
            },
            'account_info': {
                'user_id': user.uid,
                'created_at': datetime.now(timezone.utc),
                'last_login': datetime.now(timezone.utc),
                'app_version': '1.1',
                'onboarding_completed': False
            },
            'profile': {
                'age': None,
                'profession': None,
                'work_schedule': None,
                'sleep_time': None,
                'exercise_preferences': [],
                'exercise_frequency': None,
                'health_goals': [],
                'lifestyle': None
            },
            'preferences': {
                'notification_times': ['18:00', '21:00'],
                'communication_style': 'motivational',
                'notification_enabled': True
            }
        }
        
        # Salva no Firestore
        db.collection('users').document(user.uid).set(user_data)
        
        return jsonify({
            "success": True,
            "user_id": user.uid,
            "message": "Usuário registrado com sucesso"
        }), 201
        
    except auth.EmailAlreadyExistsError:
        return jsonify({"error": "Email já está em uso"}), 409
    except Exception as e:
        return jsonify({"error": f"Erro ao registrar usuário: {str(e)}"}), 500

@app.route("/api/auth/verify-token", methods=['POST'])
def verify_token():
    """
    Verifica se o token Firebase é válido e retorna dados do usuário
    """
    try:
        data = request.get_json()
        id_token = data.get('id_token')
        
        if not id_token:
            return jsonify({"error": "Token não fornecido"}), 400
        
        # Verifica o token
        decoded_token = auth.verify_id_token(id_token)
        user_id = decoded_token['uid']
        
        # Busca dados do usuário no Firestore
        user_doc = db.collection('users').document(user_id).get()
        
        if not user_doc.exists:
            return jsonify({"error": "Usuário não encontrado"}), 404
        
        user_data = user_doc.to_dict()
        
        # Atualiza último login
        db.collection('users').document(user_id).update({
            'account_info.last_login': datetime.now(timezone.utc)
        })
        
        return jsonify({
            "success": True,
            "user_id": user_id,
            "user_data": user_data
        }), 200
        
    except auth.InvalidIdTokenError:
        return jsonify({"error": "Token inválido"}), 401
    except Exception as e:
        return jsonify({"error": f"Erro ao verificar token: {str(e)}"}), 500

@app.route("/api/user/profile", methods=['GET', 'PUT'])
def user_profile():
    """
    GET: Retorna perfil do usuário
    PUT: Atualiza perfil do usuário
    """
    try:
        # Verifica autenticação
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({"error": "Token de autorização necessário"}), 401
        
        id_token = auth_header.split('Bearer ')[1]
        decoded_token = auth.verify_id_token(id_token)
        user_id = decoded_token['uid']
        
        if request.method == 'GET':
            # Retorna perfil do usuário
            user_doc = db.collection('users').document(user_id).get()
            if not user_doc.exists:
                return jsonify({"error": "Usuário não encontrado"}), 404
            
            return jsonify({
                "success": True,
                "user_data": user_doc.to_dict()
            }), 200
        
        elif request.method == 'PUT':
            # Atualiza perfil do usuário
            data = request.get_json()
            
            # Campos que podem ser atualizados
            update_data = {}
            
            if 'profile' in data:
                for key, value in data['profile'].items():
                    update_data[f'profile.{key}'] = value
            
            if 'preferences' in data:
                for key, value in data['preferences'].items():
                    update_data[f'preferences.{key}'] = value
            
            if update_data:
                db.collection('users').document(user_id).update(update_data)
            
            return jsonify({
                "success": True,
                "message": "Perfil atualizado com sucesso"
            }), 200
            
    except auth.InvalidIdTokenError:
        return jsonify({"error": "Token inválido"}), 401
    except Exception as e:
        return jsonify({"error": f"Erro ao processar perfil: {str(e)}"}), 500

# ============================================================================
# ENDPOINTS DE CHAT E ONBOARDING
# ============================================================================

@app.route("/api/chat/onboarding", methods=['POST'])
def chat_onboarding():
    """
    Processa conversa de onboarding com IA para coletar perfil do usuário
    """
    try:
        # Verifica autenticação
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({"error": "Token de autorização necessário"}), 401
        
        id_token = auth_header.split('Bearer ')[1]
        decoded_token = auth.verify_id_token(id_token)
        user_id = decoded_token['uid']
        
        data = request.get_json()
        user_message = data.get('message', '')
        conversation_step = data.get('step', 1)
        
        # Busca dados do usuário
        user_doc = db.collection('users').document(user_id).get()
        user_data = user_doc.to_dict()
        user_name = user_data['personal_info']['name']
        
        # Prompts para diferentes etapas do onboarding
        onboarding_prompts = {
            1: f"""Você é uma coach de wellness chamada Ana. Inicie uma conversa calorosa com {user_name} para conhecê-lo melhor. 
            Pergunte sobre idade e profissão de forma natural e amigável. Seja empática e motivacional.
            Mantenha a resposta curta (máximo 2 frases).""",
            
            2: f"""Continue a conversa com {user_name}. Agora pergunte sobre a rotina de trabalho e horários. 
            Seja curiosa sobre como o trabalho afeta o bem-estar dele. 
            Mantenha a resposta curta e conversacional.""",
            
            3: f"""Agora pergunte ao {user_name} sobre exercícios: que tipos gosta, com que frequência pratica, 
            e quais são seus horários preferidos. Seja encorajadora independente da resposta.
            Mantenha a resposta curta.""",
            
            4: f"""Pergunte ao {user_name} sobre hábitos de sono: que horas costuma dormir, como é a qualidade do sono, 
            e se tem alguma rotina antes de dormir. Seja compreensiva.
            Mantenha a resposta curta.""",
            
            5: f"""Finalize perguntando ao {user_name} sobre objetivos de saúde e bem-estar. O que ele gostaria de melhorar? 
            Termine com uma mensagem motivacional sobre a jornada que começarão juntos.
            Mantenha a resposta curta."""
        }
        
        prompt = onboarding_prompts.get(conversation_step, onboarding_prompts[1])
        
        # Chama OpenAI
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": user_message}
            ],
            temperature=0.8,
            max_tokens=150
        )
        
        ai_response = response.choices[0].message.content.strip()
        
        # Salva conversa no Firestore
        conversation_data = {
            'user_id': user_id,
            'step': conversation_step,
            'user_message': user_message,
            'ai_response': ai_response,
            'timestamp': datetime.now(timezone.utc)
        }
        
        db.collection('onboarding_conversations').add(conversation_data)
        
        return jsonify({
            "success": True,
            "ai_response": ai_response,
            "next_step": conversation_step + 1,
            "completed": conversation_step >= 5
        }), 200
        
    except Exception as e:
        return jsonify({"error": f"Erro no chat de onboarding: {str(e)}"}), 500

@app.route("/api/chat/complete-onboarding", methods=['POST'])
def complete_onboarding():
    """
    Marca onboarding como completo e extrai dados estruturados das conversas
    """
    try:
        # Verifica autenticação
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({"error": "Token de autorização necessário"}), 401
        
        id_token = auth_header.split('Bearer ')[1]
        decoded_token = auth.verify_id_token(id_token)
        user_id = decoded_token['uid']
        
        # Busca todas as conversas de onboarding do usuário
        conversations = db.collection('onboarding_conversations')\
                        .where('user_id', '==', user_id)\
                        .order_by('timestamp')\
                        .stream()
        
        conversation_text = ""
        for conv in conversations:
            conv_data = conv.to_dict()
            conversation_text += f"Usuário: {conv_data['user_message']}\n"
            conversation_text += f"IA: {conv_data['ai_response']}\n\n"
        
        # Extrai dados estruturados da conversa
        extraction_prompt = f"""
        Analise a seguinte conversa de onboarding e extraia as informações em formato JSON:
        
        {conversation_text}
        
        Retorne APENAS um JSON válido com esta estrutura:
        {{
            "age": "número ou null",
            "profession": "profissão ou null",
            "work_schedule": "horário de trabalho ou null",
            "sleep_time": "horário de dormir ou null",
            "exercise_preferences": ["lista de exercícios preferidos"],
            "exercise_frequency": "frequência de exercício ou null",
            "health_goals": ["lista de objetivos de saúde"],
            "lifestyle": "descrição do estilo de vida ou null"
        }}
        """
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Você é um extrator de dados. Retorne apenas JSON válido."},
                {"role": "user", "content": extraction_prompt}
            ],
            temperature=0.1,
            max_tokens=300
        )
        
        try:
            extracted_data = json.loads(response.choices[0].message.content.strip())
        except json.JSONDecodeError:
            extracted_data = {}
        
        # Atualiza perfil do usuário
        update_data = {
            'account_info.onboarding_completed': True,
            'account_info.onboarding_completed_at': datetime.now(timezone.utc)
        }
        
        for key, value in extracted_data.items():
            if value is not None:
                update_data[f'profile.{key}'] = value
        
        db.collection('users').document(user_id).update(update_data)
        
        return jsonify({
            "success": True,
            "message": "Onboarding completo!",
            "extracted_profile": extracted_data
        }), 200
        
    except Exception as e:
        return jsonify({"error": f"Erro ao completar onboarding: {str(e)}"}), 500

# ============================================================================
# ENDPOINTS DE ANÁLISE (EXPANDIDOS)
# ============================================================================

@app.route("/api/generate-summary", methods=['POST'])
def generate_summary_handler():
    """
    Gera resumo personalizado baseado no perfil do usuário (versão expandida)
    """
    try:
        # Verifica autenticação (opcional para compatibilidade com v1.0)
        user_id = None
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            try:
                id_token = auth_header.split('Bearer ')[1]
                decoded_token = auth.verify_id_token(id_token)
                user_id = decoded_token['uid']
            except:
                pass  # Continua sem autenticação para compatibilidade
        
        health_data = request.get_json()
        if not health_data:
            return jsonify({"error": "Nenhum dado recebido"}), 400
        
        # Busca perfil do usuário se autenticado
        user_profile = {}
        if user_id:
            user_doc = db.collection('users').document(user_id).get()
            if user_doc.exists:
                user_data = user_doc.to_dict()
                user_profile = {
                    'name': user_data['personal_info']['name'],
                    'age': user_data['profile'].get('age'),
                    'profession': user_data['profile'].get('profession'),
                    'exercise_preferences': user_data['profile'].get('exercise_preferences', []),
                    'health_goals': user_data['profile'].get('health_goals', []),
                    'communication_style': user_data['preferences'].get('communication_style', 'motivational')
                }
        
        # Prompt personalizado baseado no perfil
        if user_profile:
            prompt_text = f"""
            Analise os dados de saúde do usuário {user_profile['name']} e gere um resumo personalizado em português do Brasil.
            
            **Perfil do Usuário:**
            - Nome: {user_profile['name']}
            - Idade: {user_profile.get('age', 'não informada')}
            - Profissão: {user_profile.get('profession', 'não informada')}
            - Exercícios preferidos: {', '.join(user_profile.get('exercise_preferences', [])) or 'não informado'}
            - Objetivos: {', '.join(user_profile.get('health_goals', [])) or 'não informado'}
            
            **Dados de Saúde:**
            {health_data}
            
            **Instruções:**
            - Use o nome do usuário na saudação
            - Referencie exercícios preferidos quando relevante
            - Conecte com objetivos pessoais quando possível
            - Mantenha tom {user_profile.get('communication_style', 'motivacional')}
            - Seja específico e personalizado
            - Máximo 200 palavras
            """
        else:
            # Fallback para usuários não autenticados (compatibilidade v1.0)
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
        
        # Chama OpenAI
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Você é um coach de bem-estar e saúde, especialista em interpretar dados e motivar pessoas."},
                {"role": "user", "content": prompt_text}
            ],
            temperature=0.7,
            max_tokens=250
        )
        
        summary = response.choices[0].message.content.strip()
        
        # Salva análise no histórico se usuário autenticado
        if user_id:
            analysis_data = {
                'user_id': user_id,
                'health_data': health_data,
                'ai_analysis': summary,
                'timestamp': datetime.now(timezone.utc),
                'app_version': '1.1'
            }
            db.collection('health_analyses').add(analysis_data)
        
        return jsonify({"summary": summary}), 200
        
    except Exception as e:
        return jsonify({"error": f"Ocorreu um erro ao gerar o resumo: {str(e)}"}), 500

@app.route("/api/user/history", methods=['GET'])
def get_user_history():
    """
    Retorna histórico de análises do usuário
    """
    try:
        # Verifica autenticação
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({"error": "Token de autorização necessário"}), 401
        
        id_token = auth_header.split('Bearer ')[1]
        decoded_token = auth.verify_id_token(id_token)
        user_id = decoded_token['uid']
        
        # Parâmetros de paginação
        limit = int(request.args.get('limit', 20))
        offset = int(request.args.get('offset', 0))
        
        # Busca análises do usuário
        analyses = db.collection('health_analyses')\
                    .where('user_id', '==', user_id)\
                    .order_by('timestamp', direction=firestore.Query.DESCENDING)\
                    .limit(limit)\
                    .offset(offset)\
                    .stream()
        
        history = []
        for analysis in analyses:
            analysis_data = analysis.to_dict()
            history.append({
                'id': analysis.id,
                'timestamp': analysis_data['timestamp'],
                'summary': analysis_data['ai_analysis'],
                'health_data': analysis_data.get('health_data', {})
            })
        
        return jsonify({
            "success": True,
            "history": history,
            "count": len(history)
        }), 200
        
    except Exception as e:
        return jsonify({"error": f"Erro ao buscar histórico: {str(e)}"}), 500

# ============================================================================
# ROTA PRINCIPAL
# ============================================================================

@app.route("/")
def home():
    return "My Chat Fit API v1.1 - Sistema de Wellness Coaching com IA"

@app.route("/api/health")
def health_check():
    """Endpoint para verificar saúde da API"""
    return jsonify({
        "status": "healthy",
        "version": "1.1",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }), 200
