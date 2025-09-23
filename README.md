# Wellness Coach AI - Backend

Este é o backend do aplicativo Wellness Coach AI, desenvolvido para processar dados de saúde e gerar resumos motivacionais usando inteligência artificial.

## Estrutura do Projeto

```
wellness_coach_backend/
├── api/
│   └── index.py          # Função principal da API
├── requirements.txt      # Dependências Python
├── vercel.json          # Configuração para implantação na Vercel
└── README.md            # Este arquivo
```

## Como Implantar na Vercel

### Pré-requisitos
1. Conta no GitHub
2. Conta na Vercel (conectada ao GitHub)
3. Chave de API da OpenAI

### Passos para Implantação

1. **Criar um repositório no GitHub:**
   - Acesse [GitHub](https://github.com) e crie um novo repositório
   - Nome sugerido: `wellness-coach-backend`
   - Faça o upload de todos os arquivos desta pasta

2. **Conectar à Vercel:**
   - Acesse [Vercel](https://vercel.com)
   - Clique em "New Project"
   - Selecione o repositório `wellness-coach-backend`
   - Clique em "Deploy"

3. **Configurar Variáveis de Ambiente:**
   - No painel da Vercel, vá em "Settings" > "Environment Variables"
   - Adicione a variável:
     - Nome: `OPENAI_API_KEY`
     - Valor: Sua chave de API da OpenAI

4. **Testar a API:**
   - Após a implantação, você receberá uma URL como: `https://wellness-coach-backend.vercel.app`
   - Teste o endpoint: `POST https://wellness-coach-backend.vercel.app/api/generate-summary`

## Formato dos Dados de Entrada

A API espera receber dados no seguinte formato JSON:

```json
{
  "userID": "user_12345",
  "reportDate": "2025-09-22",
  "activity": {
    "activeEnergyBurned": 502,
    "appleExerciseTime": 49,
    "appleStandHours": 4,
    "stepCount": 2242,
    "distanceWalkingRunning": 3.0
  },
  "sleep": {
    "totalDuration": 427,
    "score": 84,
    "deepSleepDuration": 68,
    "remSleepDuration": 94,
    "heartRateMax": 73
  },
  "trends": {
    "stepTrend": "decreasing",
    "distanceTrend": "decreasing"
  },
  "vitals": {
    "headphoneAudioExposure": 96
  }
}
```

## Resposta da API

A API retorna um resumo motivacional no formato:

```json
{
  "summary": "Olá! Tenho ótimas notícias sobre sua saúde..."
}
```

## Tecnologias Utilizadas

- **Python 3.9**: Linguagem de programação
- **Flask**: Framework web para criar a API
- **OpenAI GPT-4**: Modelo de IA para gerar os resumos
- **Vercel**: Plataforma de hospedagem serverless

## Suporte

Para dúvidas ou problemas, consulte a documentação da Vercel ou entre em contato com o desenvolvedor.
