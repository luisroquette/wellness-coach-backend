# Firebase Setup - My Chat Fit v1.1

## Configuração do Firebase

### 1. Criar Projeto Firebase

1. Acesse [Firebase Console](https://console.firebase.google.com)
2. Clique em "Adicionar projeto"
3. Nome do projeto: `mychatfit-project`
4. Habilite Google Analytics (opcional)
5. Clique em "Criar projeto"

### 2. Configurar Authentication

1. No console Firebase, vá para **Authentication**
2. Clique em **Começar**
3. Na aba **Sign-in method**, habilite:
   - **Email/Password** (obrigatório)
   - **Google** (opcional, para futuro)

### 3. Configurar Firestore Database

1. No console Firebase, vá para **Firestore Database**
2. Clique em **Criar banco de dados**
3. Escolha **Iniciar no modo de teste** (por enquanto)
4. Selecione localização: **southamerica-east1 (São Paulo)**

### 4. Configurar Service Account

1. Vá para **Configurações do projeto** (ícone de engrenagem)
2. Aba **Contas de serviço**
3. Clique em **Gerar nova chave privada**
4. Baixe o arquivo JSON
5. Renomeie para `firebase-config.json`

### 5. Configurar Variáveis de Ambiente

#### Para Desenvolvimento Local:
```bash
export FIREBASE_CONFIG='{"type":"service_account",...}'
export OPENAI_API_KEY="sua-chave-openai"
```

#### Para Vercel (Produção):
1. Acesse Vercel Dashboard
2. Vá para o projeto `wellness-coach-backend`
3. Settings → Environment Variables
4. Adicione:
   - `FIREBASE_CONFIG`: Cole o conteúdo completo do JSON
   - `OPENAI_API_KEY`: Sua chave da OpenAI

### 6. Estrutura do Banco de Dados

```
users/
├── {user_id}/
│   ├── personal_info/
│   │   ├── name: string
│   │   ├── email: string
│   │   ├── phone: string
│   │   ├── city: string
│   │   ├── state: string
│   │   └── country: string
│   ├── account_info/
│   │   ├── user_id: string
│   │   ├── created_at: timestamp
│   │   ├── last_login: timestamp
│   │   ├── app_version: string
│   │   └── onboarding_completed: boolean
│   ├── profile/
│   │   ├── age: number
│   │   ├── profession: string
│   │   ├── work_schedule: string
│   │   ├── sleep_time: string
│   │   ├── exercise_preferences: array
│   │   ├── exercise_frequency: string
│   │   ├── health_goals: array
│   │   └── lifestyle: string
│   └── preferences/
│       ├── notification_times: array
│       ├── communication_style: string
│       └── notification_enabled: boolean

onboarding_conversations/
├── {conversation_id}/
│   ├── user_id: string
│   ├── step: number
│   ├── user_message: string
│   ├── ai_response: string
│   └── timestamp: timestamp

health_analyses/
├── {analysis_id}/
│   ├── user_id: string
│   ├── health_data: object
│   ├── ai_analysis: string
│   ├── timestamp: timestamp
│   └── app_version: string
```

### 7. Regras de Segurança Firestore

```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // Usuários podem ler/escrever apenas seus próprios dados
    match /users/{userId} {
      allow read, write: if request.auth != null && request.auth.uid == userId;
    }
    
    // Conversas de onboarding
    match /onboarding_conversations/{conversationId} {
      allow read, write: if request.auth != null && 
        request.auth.uid == resource.data.user_id;
    }
    
    // Análises de saúde
    match /health_analyses/{analysisId} {
      allow read, write: if request.auth != null && 
        request.auth.uid == resource.data.user_id;
    }
  }
}
```

### 8. Testar Configuração

```bash
# Instalar dependências
pip install -r requirements.txt

# Executar localmente
python src/api/index.py

# Testar endpoints
curl -X POST http://localhost:5000/api/health
```

### 9. Deploy no Vercel

```bash
# Fazer deploy
vercel --prod

# Verificar logs
vercel logs
```

## Endpoints Disponíveis

### Autenticação
- `POST /api/auth/register` - Registrar usuário
- `POST /api/auth/verify-token` - Verificar token

### Perfil
- `GET /api/user/profile` - Buscar perfil
- `PUT /api/user/profile` - Atualizar perfil

### Chat
- `POST /api/chat/onboarding` - Chat de onboarding
- `POST /api/chat/complete-onboarding` - Finalizar onboarding

### Análises
- `POST /api/generate-summary` - Gerar resumo (compatível v1.0)
- `GET /api/user/history` - Histórico de análises

### Utilitários
- `GET /api/health` - Health check
