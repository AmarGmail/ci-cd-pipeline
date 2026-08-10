import os
import sys
import requests
from datetime import datetime

SENDGRID_API_KEY = os.environ.get('SENDGRID_API_KEY')
EMAIL_TO = os.environ.get('EMAIL_TO')
EMAIL_FROM = os.environ.get('EMAIL_FROM')

BUILD_NUMBER = os.environ.get('BUILD_NUMBER', 'N/A')
BUILD_URL = os.environ.get('BUILD_URL', '')
JOB_NAME = os.environ.get('JOB_NAME', 'student-registration')
BUILD_STATUS = os.environ.get('BUILD_STATUS', 'SUCCESS')

# Determine styling
if BUILD_STATUS == 'SUCCESS':
    emoji = '✅'
    color = '#22c55e'
    subject = f'{emoji} Build #{BUILD_NUMBER} SUCCESS — {JOB_NAME}'
elif BUILD_STATUS == 'FAILURE':
    emoji = '❌'
    color = '#ef4444'
    subject = f'{emoji} Build #{BUILD_NUMBER} FAILED — {JOB_NAME}'
else:
    emoji = '⚠️'
    color = '#f59e0b'
    subject = f'{emoji} Build #{BUILD_NUMBER} {BUILD_STATUS} — {JOB_NAME}'

html = f"""
<!DOCTYPE html>
<html>
<head>
<style>
body {{ font-family: Arial, sans-serif; background: #f3f4f6; padding: 20px; }}
.container {{ max-width: 600px; margin: 0 auto; background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
.header {{ background: {color}; color: white; padding: 24px; text-align: center; }}
.content {{ padding: 24px; }}
.detail {{ background: #f9fafb; padding: 12px 16px; margin: 8px 0; border-radius: 8px; border-left: 4px solid {color}; }}
.footer {{ text-align: center; padding: 16px; font-size: 12px; color: #6b7280; }}
a {{ color: #3b82f6; text-decoration: none; }}
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <h1>{emoji} Jenkins Build Report</h1>
    <p>{JOB_NAME}</p>
  </div>
  <div class="content">
    <div class="detail"><strong>Status:</strong> <span style="color:{color};font-weight:bold;">{BUILD_STATUS}</span></div>
    <div class="detail"><strong>Build #:</strong> {BUILD_NUMBER}</div>
    <div class="detail"><strong>Commit SHA:</strong> {os.environ.get('COMMIT_SHA', 'N/A')}</div>
    <div class="detail"><strong>Timestamp:</strong> {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}</div>
    <div class="detail"><strong>Build URL:</strong> <a href="{BUILD_URL}">{BUILD_URL}</a></div>
  </div>
  <div class="footer">
    <p>Automated report from Jenkins CI/CD Pipeline</p>
  </div>
</div>
</body>
</html>
"""

url = "https://api.sendgrid.com/v3/mail/send"
headers = {
    "Authorization": f"Bearer {SENDGRID_API_KEY}",
    "Content-Type": "application/json"
}
payload = {
    "personalizations": [{"to": [{"email": EMAIL_TO}]}],
    "from": {"email": EMAIL_FROM},
    "subject": subject,
    "content": [{"type": "text/html", "value": html}]
}

resp = requests.post(url, json=payload, headers=headers)
if resp.status_code == 202:
    print("✅ Email sent successfully")
else:
    print(f"⚠️ Email send failed: {resp.status_code} — {resp.text}")
sys.exit(0)