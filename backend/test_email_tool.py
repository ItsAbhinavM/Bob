"""
Test email functionality directly
Run this to diagnose email issues
"""
import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.agents.tools.email_service import email_service
from app.agents.tools.contact_service import contact_service

async def test_email_system():
    """Test the entire email system"""
    
    print("\n" + "="*60)
    print("🧪 EMAIL SYSTEM TEST")
    print("="*60 + "\n")
    
    # Step 1: Check environment variables
    print("📋 Step 1: Checking Environment Variables")
    print("-" * 60)
    
    sender_email = os.getenv("SENDER_EMAIL")
    sender_password = os.getenv("SENDER_PASSWORD")
    smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = os.getenv("SMTP_PORT", "587")
    
    print(f"SENDER_EMAIL: {sender_email if sender_email else '❌ NOT SET'}")
    print(f"SENDER_PASSWORD: {'✅ SET' if sender_password else '❌ NOT SET'}")
    print(f"SMTP_SERVER: {smtp_server}")
    print(f"SMTP_PORT: {smtp_port}")
    
    if not sender_email or not sender_password:
        print("\n❌ ERROR: Email credentials not configured!")
        print("Please set SENDER_EMAIL and SENDER_PASSWORD in .env file")
        return
    
    # Step 2: Test adding a contact
    print("\n📋 Step 2: Testing Contact Management")
    print("-" * 60)
    
    test_alias = "testuser"
    test_email = input(f"Enter test email address (or press Enter to use {sender_email}): ").strip()
    if not test_email:
        test_email = sender_email
    
    print(f"\nAdding contact: {test_alias} -> {test_email}")
    
    result = await contact_service.add_contact(
        alias=test_alias,
        email=test_email,
        name="Test User"
    )
    
    if result['success']:
        print(f"✅ Contact added successfully")
    else:
        print(f"ℹ️ Contact might already exist: {result.get('error')}")
    
    # Step 3: Retrieve contact
    print(f"\nRetrieving contact '{test_alias}'...")
    contact = await contact_service.get_contact(test_alias)
    
    if contact:
        print(f"✅ Contact found: {contact}")
    else:
        print(f"❌ Contact not found!")
        return
    
    # Step 4: Send test email
    print("\n📋 Step 3: Testing Email Send")
    print("-" * 60)
    
    subject = "Test Email from Bob Assistant"
    body = """Hello!

This is a test email from Bob, your AI assistant.

If you're reading this, the email system is working correctly!

Best regards,
Bob
"""
    
    print(f"Sending test email to: {contact['email']}")
    print(f"Subject: {subject}")
    
    result = await email_service.send_email(
        to_email=contact['email'],
        subject=subject,
        body=body,
        to_alias=test_alias
    )
    
    print("\n📧 Email Send Result:")
    print("-" * 60)
    
    if result['success']:
        print(f"✅ SUCCESS: {result['message']}")
        print(f"📝 Log ID: {result.get('log_id')}")
        print(f"\n📬 Check your inbox at: {contact['email']}")
        print(f"   (Also check spam folder)")
    else:
        print(f"❌ FAILED: {result.get('error')}")
        print("\nCommon issues:")
        print("1. Wrong app password (must be 16-char Gmail App Password)")
        print("2. 2-Step Verification not enabled on Gmail")
        print("3. Incorrect SMTP settings")
        print("4. Network/firewall blocking SMTP port 587")
    
    # Step 5: Check email logs
    print("\n📋 Step 4: Checking Email Logs")
    print("-" * 60)
    
    logs = email_service.get_email_logs(limit=3)
    
    if logs:
        print(f"Recent email logs:")
        for log in logs:
            status_icon = "✅" if log['status'] == 'sent' else "❌" if log['status'] == 'failed' else "⏳"
            print(f"{status_icon} To: {log['to']}, Subject: {log['subject']}, Status: {log['status']}")
    else:
        print("No email logs found")
    
    print("\n" + "="*60)
    print("🧪 TEST COMPLETE")
    print("="*60 + "\n")

if __name__ == "__main__":
    asyncio.run(test_email_system())