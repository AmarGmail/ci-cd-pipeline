import os
import sys
import requests
from datetime import datetime, timezone

SENDGRID_API_KEY = os.environ.get('SENDGRID_API_KEY')
EMAIL_TO = os.environ.get('EMAIL_TO')
EMAIL_FROM = os.environ.get('EMAIL_FROM')

BUILD_NUMBER = os.environ.get('BUILD_NUMBER', 'N/A')
BUILD_URL = os.environ.get('BUILD_URL', '')
JOB_NAME = os.environ.get('JOB_NAME', 'student-registration')
BUILD_STATUS = os.environ.get('BUILD_STATUS', 'SUCCESS')
COMMIT_SHA = os.environ.get('COMMIT_SHA', 'N/A')
IMAGE_TAG = os.environ.get('IMAGE_TAG', 'N/A')
FAILED_STAGE = os.environ.get('FAILED_STAGE', '')

status = 'SUCCESS'
if BUILD_STATUS == 'FAILURE':
    status = 'FAILURE'

if status == 'SUCCESS':
    emoji = '✅'
    color = '#22c55e'
    subject = f'{emoji} Build #{BUILD_NUMBER} SUCCESS — {JOB_NAME}'
else:
    emoji = '❌'
    color = '#ef4444'
    subject = f'{emoji} Build #{BUILD_NUMBER} FAILED — {JOB_NAME}'

# Build failed stage HTML only if failure occurred
failed_stage_html = ''
if status == 'FAILURE' and FAILED_STAGE:
    failed_stage_html = f'''
    <div class="detail" style="background: #fef2f2; border-left-color: #ef4444;">
        <strong>Failed Stage:</strong> <span style="color: #ef4444; font-weight: bold;">{FAILED_STAGE}</span>
    </div>
    '''

html = f"""<!DOCTYPE html>
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
    <div class="detail"><strong>Status:</strong> <span style="color:{color};font-weight:bold;">{status}</span></div>
    <div class="detail"><strong>Build #:</strong> {BUILD_NUMBER}</div>
    <div class="detail"><strong>Commit SHA:</strong> <code>{COMMIT_SHA}</code></div>
    <div class="detail"><strong>Image Tag:</strong> <code>{IMAGE_TAG}</code></div>
    {failed_stage_html}
    <div class="detail"><strong>Timestamp:</strong> {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}</div>
    <div class="detail"><strong>Build URL:</strong> <a href="{BUILD_URL}">{BUILD_URL}</a></div>
  </div>
  <div class="footer">
    <p>Automated report from Jenkins CI/CD Pipeline</p>
  </div>
</div>
</body>
</html>"""

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