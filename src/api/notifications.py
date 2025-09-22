import os
import json
from flask import Flask, request, jsonify
import logging
import requests

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NotificationService:
    def __init__(self):
        # Configurações Twilio
        self.twilio_account_sid = os.environ.get('TWILIO_ACCOUNT_SID')
        self.twilio_auth_token = os.environ.get('TWILIO_AUTH_TOKEN')
        self.twilio_phone_number = os.environ.get('TWILIO_PHONE_NUMBER', '+14155238886')
        self.whatsapp_sandbox_number = os.environ.get('WHATSAPP_SANDBOX_NUMBER', 'whatsapp:+14155238886')
        
        # Configurações SendGrid
        self.sendgrid_api_key = os.environ.get('SENDGRID_API_KEY')
        self.from_email = os.environ.get('FROM_EMAIL', 'wellness@example.com')
        
        # URLs das APIs
        self.twilio_messages_url = f"https://api.twilio.com/2010-04-01/Accounts/{self.twilio_account_sid}/Messages.json"
        self.sendgrid_url = "https://api.sendgrid.com/v3/mail/send"
    
    def send_sms(self, to_phone, message):
        """Enviar SMS usando Twilio API diretamente"""
        if not self.twilio_account_sid or not self.twilio_auth_token:
            return {"success": False, "error": "Twilio not configured"}
        
        try:
            # Garantir formato E.164
            if not to_phone.startswith('+'):
                to_phone = '+' + to_phone
            
            data = {
                'From': self.twilio_phone_number,
                'To': to_phone,
                'Body': message
            }
            
            response = requests.post(
                self.twilio_messages_url,
                data=data,
                auth=(self.twilio_account_sid, self.twilio_auth_token)
            )
            
            if response.status_code == 201:
                result = response.json()
                logger.info(f"SMS sent successfully. SID: {result.get('sid')}")
                return {
                    "success": True, 
                    "message_sid": result.get('sid'),
                    "status": result.get('status')
                }
            else:
                logger.error(f"Error sending SMS: {response.text}")
                return {"success": False, "error": response.text}
            
        except Exception as e:
            logger.error(f"Error sending SMS: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def send_whatsapp(self, to_phone, message):
        """Enviar mensagem WhatsApp usando Twilio API diretamente"""
        if not self.twilio_account_sid or not self.twilio_auth_token:
            return {"success": False, "error": "Twilio not configured"}
        
        try:
            # Garantir formato WhatsApp
            if not to_phone.startswith('whatsapp:'):
                if not to_phone.startswith('+'):
                    to_phone = '+' + to_phone
                to_phone = 'whatsapp:' + to_phone
            
            data = {
                'From': self.whatsapp_sandbox_number,
                'To': to_phone,
                'Body': message
            }
            
            response = requests.post(
                self.twilio_messages_url,
                data=data,
                auth=(self.twilio_account_sid, self.twilio_auth_token)
            )
            
            if response.status_code == 201:
                result = response.json()
                logger.info(f"WhatsApp message sent successfully. SID: {result.get('sid')}")
                return {
                    "success": True, 
                    "message_sid": result.get('sid'),
                    "status": result.get('status')
                }
            else:
                logger.error(f"Error sending WhatsApp: {response.text}")
                return {"success": False, "error": response.text}
            
        except Exception as e:
            logger.error(f"Error sending WhatsApp: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def send_email(self, to_email, subject, html_content, text_content=None):
        """Enviar email usando SendGrid API diretamente"""
        if not self.sendgrid_api_key:
            return {"success": False, "error": "SendGrid not configured"}
        
        try:
            headers = {
                'Authorization': f'Bearer {self.sendgrid_api_key}',
                'Content-Type': 'application/json'
            }
            
            data = {
                "personalizations": [
                    {
                        "to": [{"email": to_email}],
                        "subject": subject
                    }
                ],
                "from": {"email": self.from_email},
                "content": [
                    {
                        "type": "text/html",
                        "value": html_content
                    }
                ]
            }
            
            if text_content:
                data["content"].append({
                    "type": "text/plain",
                    "value": text_content
                })
            
            response = requests.post(
                self.sendgrid_url,
                headers=headers,
                json=data
            )
            
            if response.status_code == 202:
                logger.info(f"Email sent successfully. Status: {response.status_code}")
                return {
                    "success": True,
                    "status_code": response.status_code,
                    "message_id": response.headers.get('X-Message-Id')
                }
            else:
                logger.error(f"Error sending email: {response.text}")
                return {"success": False, "error": response.text}
            
        except Exception as e:
            logger.error(f"Error sending email: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def send_wellness_summary(self, user_data, summary_text, channels=['email']):
        """
        Enviar resumo de wellness para múltiplos canais
        """
        results = {}
        
        # Preparar conteúdo personalizado
        user_name = user_data.get('name', 'Usuário')
        
        # Conteúdo para SMS/WhatsApp (mais curto)
        short_message = f"🌟 Olá {user_name}!\n\n{summary_text[:200]}...\n\nVeja o relatório completo no app!"
        
        # Conteúdo para email (mais detalhado)
        email_subject = f"Seu Relatório Diário de Wellness - {user_name}"
        email_html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #4CAF50;">🌟 Seu Relatório Diário de Wellness</h2>
                
                <p>Olá <strong>{user_name}</strong>,</p>
                
                <div style="background-color: #f9f9f9; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <h3 style="color: #2196F3; margin-top: 0;">📊 Análise dos Seus Dados de Saúde</h3>
                    <p style="white-space: pre-line;">{summary_text}</p>
                </div>
                
                <div style="background-color: #e8f5e8; padding: 15px; border-radius: 8px; margin: 20px 0;">
                    <h4 style="color: #4CAF50; margin-top: 0;">💡 Dica do Dia</h4>
                    <p>Continue monitorando seus dados de saúde regularmente. Pequenas melhorias diárias levam a grandes resultados!</p>
                </div>
                
                <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
                
                <p style="font-size: 12px; color: #666;">
                    Este relatório foi gerado automaticamente com base nos seus dados do Apple Saúde.<br>
                    Para parar de receber esses relatórios, acesse as configurações do app.
                </p>
            </div>
        </body>
        </html>
        """
        
        # Enviar por cada canal solicitado
        if 'sms' in channels and user_data.get('phone'):
            results['sms'] = self.send_sms(user_data['phone'], short_message)
        
        if 'whatsapp' in channels and user_data.get('phone'):
            results['whatsapp'] = self.send_whatsapp(user_data['phone'], short_message)
        
        if 'email' in channels and user_data.get('email'):
            results['email'] = self.send_email(
                user_data['email'], 
                email_subject, 
                email_html,
                summary_text
            )
        
        return results
    
    def send_test_notifications(self, test_data):
        """Enviar notificações de teste para validar configuração"""
        test_message = "🧪 Teste do sistema de notificações do Wellness Coach! Se você recebeu esta mensagem, tudo está funcionando perfeitamente."
        
        results = {}
        
        if test_data.get('phone'):
            results['sms'] = self.send_sms(test_data['phone'], test_message)
            results['whatsapp'] = self.send_whatsapp(test_data['phone'], test_message)
        
        if test_data.get('email'):
            results['email'] = self.send_email(
                test_data['email'],
                "Teste - Wellness Coach Notifications",
                f"<h2>Teste de Notificação</h2><p>{test_message}</p>",
                test_message
            )
        
        return results

# Instância global do serviço
notification_service = NotificationService()

def create_notification_routes(app):
    """Criar rotas para o sistema de notificações"""
    
    @app.route('/api/send-wellness-summary', methods=['POST'])
    def send_wellness_summary():
        try:
            data = request.get_json()
            
            user_data = data.get('user_data', {})
            summary_text = data.get('summary_text', '')
            channels = data.get('channels', ['email'])
            
            if not summary_text:
                return jsonify({"error": "Summary text is required"}), 400
            
            if not user_data.get('email') and not user_data.get('phone'):
                return jsonify({"error": "User email or phone is required"}), 400
            
            results = notification_service.send_wellness_summary(
                user_data, summary_text, channels
            )
            
            return jsonify({
                "success": True,
                "results": results
            })
            
        except Exception as e:
            logger.error(f"Error in send_wellness_summary: {str(e)}")
            return jsonify({"error": str(e)}), 500
    
    @app.route('/api/test-notifications', methods=['POST'])
    def test_notifications():
        try:
            data = request.get_json()
            
            test_data = {
                'phone': data.get('phone'),
                'email': data.get('email')
            }
            
            if not test_data.get('phone') and not test_data.get('email'):
                return jsonify({"error": "Phone or email is required for testing"}), 400
            
            results = notification_service.send_test_notifications(test_data)
            
            return jsonify({
                "success": True,
                "results": results
            })
            
        except Exception as e:
            logger.error(f"Error in test_notifications: {str(e)}")
            return jsonify({"error": str(e)}), 500
    
    @app.route('/api/notification-status', methods=['GET'])
    def notification_status():
        """Verificar status das configurações de notificação"""
        status = {
            "twilio_configured": bool(notification_service.twilio_account_sid and notification_service.twilio_auth_token),
            "sendgrid_configured": bool(notification_service.sendgrid_api_key),
            "available_channels": []
        }
        
        if status["twilio_configured"]:
            status["available_channels"].extend(["sms", "whatsapp"])
        
        if status["sendgrid_configured"]:
            status["available_channels"].append("email")
        
        return jsonify(status)

if __name__ == "__main__":
    # Teste local
    app = Flask(__name__)
    create_notification_routes(app)
    app.run(debug=True, port=5002)
