import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Dict, Optional

from app.services.database import SessionLocal, EmailLog

class EmailService:
    """SMTP-based email service"""
    
    def __init__(self):
        # Email configuration from environment - NO FALLBACK for security
        self.sender_email = os.getenv("SENDER_EMAIL")
        self.sender_password = os.getenv("SENDER_PASSWORD")
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        
        # Validate required environment variables
        if not self.sender_email:
            print("⚠️ ERROR: SENDER_EMAIL not set in .env file!")
        if not self.sender_password:
            print("⚠️ ERROR: SENDER_PASSWORD not set in .env file!")
    
    async def send_email(
        self, 
        to_email: str, 
        subject: str, 
        body: str,
        to_alias: Optional[str] = None
    ) -> Dict[str, any]:
        """
        Send email using SMTP
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            body: Email body (plain text)
            to_alias: Optional alias name (for logging)
        
        Returns:
            Dict with status and message
        """
        db = SessionLocal()
        
        try:
            # Create email log entry
            email_log = EmailLog(
                to_email=to_email,
                to_alias=to_alias,
                subject=subject,
                body=body,
                status="pending"
            )
            db.add(email_log)
            db.commit()
            log_id = email_log.id
            
            # Create message
            message = MIMEMultipart()
            message["From"] = self.sender_email
            message["To"] = to_email
            message["Subject"] = subject
            
            # Add body
            message.attach(MIMEText(body, "plain"))
            
            # Connect to SMTP server and send
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()  # Secure connection
                server.login(self.sender_email, self.sender_password)
                server.send_message(message)
            
            # Update log as sent
            email_log.status = "sent"
            email_log.sent_at = datetime.utcnow()
            db.commit()
            
            return {
                "success": True,
                "message": f"Email sent successfully to {to_email}",
                "log_id": log_id
            }
            
        except smtplib.SMTPAuthenticationError:
            error = "Authentication failed. Check SENDER_PASSWORD in .env (use Gmail App Password)"
            email_log.status = "failed"
            email_log.error_message = error
            db.commit()
            return {
                "success": False,
                "error": error
            }
            
        except smtplib.SMTPException as e:
            error = f"SMTP error: {str(e)}"
            email_log.status = "failed"
            email_log.error_message = error
            db.commit()
            return {
                "success": False,
                "error": error
            }
            
        except Exception as e:
            error = f"Failed to send email: {str(e)}"
            if 'email_log' in locals():
                email_log.status = "failed"
                email_log.error_message = error
                db.commit()
            return {
                "success": False,
                "error": error
            }
        
        finally:
            db.close()
    
    def get_email_logs(self, limit: int = 10) -> list:
        """Get recent email logs"""
        db = SessionLocal()
        try:
            logs = db.query(EmailLog)\
                .order_by(EmailLog.created_at.desc())\
                .limit(limit)\
                .all()
            
            return [{
                "id": log.id,
                "to": log.to_email,
                "alias": log.to_alias,
                "subject": log.subject,
                "status": log.status,
                "sent_at": log.sent_at.isoformat() if log.sent_at else None
            } for log in logs]
        finally:
            db.close()


# Create global instance
email_service = EmailService()