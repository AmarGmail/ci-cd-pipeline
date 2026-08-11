# Student Registration System - CI/CD Pipeline

A fully automated CI/CD pipeline that deploys a Flask + MongoDB Student Registration System from a Git push to a running container on AWS EC2, with automated testing, health checks, and email notifications.

---

## 📋 Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Prerequisites](#prerequisites)
3. [Step 1: Fork & Clone Repository](#step-1-fork--clone-repository)
4. [Step 2: Local Development Setup](#step-2-local-development-setup)
5. [Step 3: Dockerize the Application](#step-3-dockerize-the-application)
6. [Step 4: MongoDB Atlas Configuration](#step-4-mongodb-atlas-configuration)
7. [Step 5: AWS Infrastructure Setup](#step-5-aws-infrastructure-setup)
8. [Step 6: Jenkins Server Setup](#step-6-jenkins-server-setup)
9. [Step 7: Jenkins Credentials](#step-7-jenkins-credentials)
10. [Step 8: GitHub Webhook Configuration](#step-8-github-webhook-configuration)
11. [Step 9: Pipeline Stages Explained](#step-9-pipeline-stages-explained)
12. [Step 10: Trigger & Monitor](#step-10-trigger--monitor)
13. [Step 11: Intentional Pipeline Failed at Test Stage](#step-11-intentional-pipeline-failed-at-test-stage)
14. [Troubleshooting](#troubleshooting)
15. [Project Structure](#project-structure)

---

## Architecture Overview

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Developer     │     │  Local Ubuntu    │     │   Amazon ECR    │
│   (Git Push)    │────▶│  Jenkins + ngrok │────▶│  Docker Images  │
└─────────────────┘     └──────────────────┘     └────────┬────────┘
         │                                                │
         │         GitHub Webhook                         │
         │                                                ▼
         │                                       ┌─────────────────┐
         │                                       │   AWS EC2       │
         │                                       │  (Production)   │
         │                                       │  Flask + Docker │
         │                                       └────────┬────────┘
         │                                                │
         │                                                ▼
         │                                       ┌─────────────────┐
         │                                       │  MongoDB Atlas  │
         └──────────────────────────────────────▶│  (Cloud DB)     │
                                                 └─────────────────┘
```

### Tech Stack

| Component | Technology |
|-----------|------------|
| **Application** | Flask, Python 3.12 |
| **Database** | MongoDB Atlas (M0 Free Tier) |
| **Containerization** | Docker |
| **CI/CD** | Jenkins (local) |
| **Cloud Registry** | Amazon ECR |
| **Cloud Compute** | AWS EC2 (Ubuntu 22.04) |
| **Tunneling** | ngrok |
| **Email Service** | SendGrid |
| **Testing** | pytest, mongomock |

---

## Prerequisites

Before starting, ensure you have accounts and tools ready:

- [ ] **GitHub Account** - to fork and host the repository
- [ ] **AWS Account** - for ECR and EC2
- [ ] **MongoDB Atlas Account** - https://cloud.mongodb.com (free M0 cluster)
- [ ] **SendGrid Account** - https://sendgrid.com (free tier)
- [ ] **Local Ubuntu Machine** - for Jenkins server
- [ ] **ngrok Account** - https://ngrok.com (for exposing local Jenkins)
- [ ] **Docker** - installed on both local Ubuntu and EC2
- [ ] **AWS CLI** - installed on local Ubuntu and EC2

---

## Final outcome

![Desired Result](screenshots/Desired_result.jpg)

---

## Step 1: Fork & Clone Repository

### 1.1 Fork the Original Repository

1. Navigate to: https://github.com/mohanDevOps-arch/flask_Practice
2. Click the **Fork** button (top-right)
3. Select your GitHub account to create the fork

### 1.2 Clone Your Fork Locally

```bash
git clone https://github.com/AmarGmail/ci-cd-pipeline.git
cd ci-cd-pipeline
```

---

## Step 2: Local Development Setup

### 2.1 Install MongoDB (for local testing)

```bash
# Import MongoDB GPG key
curl -fsSL https://pgp.mongodb.com/server-7.0.asc | \
   sudo gpg -o /usr/share/keyrings/mongodb-server-7.0.gpg --dearmor

# Add MongoDB repository
echo "deb [ arch=amd64,arm64 signed-by=/usr/share/keyrings/mongodb-server-7.0.gpg ] \
https://repo.mongodb.org/apt/ubuntu jammy/mongodb-org/7.0 multiverse" | \
   sudo tee /etc/apt/sources.list.d/mongodb-org-7.0.list

# Install and start MongoDB
sudo apt-get update
sudo apt-get install -y mongodb-org
sudo systemctl start mongod
sudo systemctl enable mongod
```

### 2.2 Create Python Virtual Environment

```bash
cd ci-cd-pipeline
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 2.3 Run Tests Locally

```bash
export MONGO_URI="mongodb://localhost:27017/test_student_db"
export SECRET_KEY="test-secret-key"
pytest test_app.py -v
```

Expected output: **4 passed**
![Test Case Results](screenshots/local_test_results.jpg)

---

## Step 3: Dockerize the Application

### 3.1 Dockerfile

Create [Dockerfile](Dockerfile) in the project root:

### 3.2 Use .dockerignore to exclude and keep repo clean
[.dockerignore](.dockerignore)


### 3.3 Build & Test Locally

```bash
# Build image
docker build -t student-reg:latest .

# Run container with Atlas connection
docker run -d \
  -p 5000:5000 \
  -e MONGO_URI="mongodb+srv://USER:PASSWORD@cluster0.xxx.mongodb.net/studentDB?retryWrites=true&w=majority" \
  -e SECRET_KEY="your-secret-key" \
  --name student-reg \
  student-reg:latest

# Verify
curl http://localhost:5000/health or
```

![App health status](screenshots/Manual_run_app_health_local.jpg)

---

## Step 4: MongoDB Atlas Configuration

### 4.1 Create Cluster

1. Sign up at https://cloud.mongodb.com
2. Create a free **M0** cluster (1 per project)
3. Name it `Cluster0`

### 4.2 Create Database User

1. Go to **Security → Database Access**
2. Click **Add New Database User**
3. Authentication Method: **Password**
4. Username: `amarjyotilahkar_db_user`
5. Password: Set a strong password (note it down)
6. Database User Privileges: **Read and write to any database**

### 4.3 Configure Network Access

1. Go to **Security → Network Access**
2. Click **Add IP Address**
3. Add your **local machine IP** (for development)
4. Add your **EC2 public IP** (for production)
5. Optionally add `0.0.0.0/0` for testing (remember to remove later)

### 4.4 Get Connection String

1. Go to **Clusters → Connect → Drivers → Python**
2. Copy the connection string:

```
mongodb+srv://amarjyotilahkar_db_user:<password>@cluster0.xxx.mongodb.net/?retryWrites=true&w=majority
```

3. Replace `<password>` with your actual password
4. Add database name: `studentDB` before `?`

Final format:
```
mongodb+srv://amarjyotilahkar_db_user:YOUR_PASSWORD@cluster0.xxx.mongodb.net/studentDB?retryWrites=true&w=majority
```

---

## Step 5: AWS Infrastructure Setup

### 5.1 Create ECR Repository

**Via AWS Console:**
1. Go to **Amazon ECR → Repositories → Create repository**
2. Visibility: **Private**
3. Repository name: `student-registration`
4. Click **Create repository**

**Save the repository URI:**
```
123456789012.dkr.ecr.us-east-1.amazonaws.com/student-registration
```

### 5.2 Create IAM Role for EC2

1. Go to **IAM → Roles → Create role**
2. Trusted entity: **AWS service**
3. Use case: **EC2**
4. Attach policy: **`AmazonEC2ContainerRegistryReadOnly`**
5. Role name: `student-registration-ec2-role`
6. Click **Create role**

![IAM Role policy](screenshots/IAM_Role_EC2_ECR_Read_Policy.jpg)

### 5.3 Launch EC2 Instance (Production)

1. **EC2 → Instances → Launch instances**
2. **Name:** `student-registration-ec2`
3. **AMI:** Ubuntu Server 22.04 LTS
4. **Instance type:** `t2.micro` (Free tier)
5. **Key pair:** Create or select existing (save `.pem` file)
6. **Security Group:**
   - SSH (22) → Your IP
   - Custom TCP (5000) → Anywhere (or your IP)
7. **IAM instance profile:** `student-registration-ec2-role`
8. **User Data** (auto-install Docker & AWS CLI):

```bash
#!/bin/bash
set -e
apt-get update -y

# Install Docker
apt-get install -y ca-certificates curl gnupg
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
chmod a+r /etc/apt/keyrings/docker.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
apt-get update -y
apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
usermod -aG docker ubuntu

# Install AWS CLI
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
apt-get install -y unzip
unzip awscliv2.zip
./aws/install

systemctl enable docker
systemctl start docker
```

9. Click **Launch instance**

### 5.4 Verify EC2 Setup

```bash
ssh -i your-key.pem ubuntu@<EC2_PUBLIC_IP>
docker --version
docker compose version
aws --version
```

---

## Step 6: Jenkins Server Setup

### 6.1 Install Jenkins on Local Ubuntu

```bash
# Install Java
sudo apt-get update
sudo apt-get install -y openjdk-17-jdk

# Install Jenkins
sudo wget -O /usr/share/keyrings/jenkins-keyring.asc https://pkg.jenkins.io/debian-stable/jenkins.io-2023.key
echo "deb [signed-by=/usr/share/keyrings/jenkins-keyring.asc] https://pkg.jenkins.io/debian-stable binary/" | \
  sudo tee /etc/apt/sources.list.d/jenkins.list > /dev/null
sudo apt-get update
sudo apt-get install -y jenkins

# Install Docker
sudo apt-get install -y docker.io
sudo usermod -aG docker jenkins
sudo usermod -aG docker $USER

# Install AWS CLI
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
sudo apt-get install -y unzip
unzip awscliv2.zip
sudo ./aws/install

# Restart Jenkins
sudo systemctl enable jenkins
sudo systemctl restart jenkins

# Get initial password
sudo cat /var/lib/jenkins/secrets/initialAdminPassword
```

### 6.2 Complete Jenkins Setup

1. Open `http://localhost:8080`
2. Enter the initial admin password
3. Install **suggested plugins**
4. Create admin user

### 6.3 Install Required Plugins

Go to **Manage Jenkins → Plugins → Available Plugins**:

- **Pipeline**
- **GitHub Integration**
- **SSH Agent**
- **Credentials Binding**
- **Workspace Cleanup Plugin**

Restart Jenkins after installation.

### 6.4 Expose Jenkins via ngrok for github web hook trigger to work (CI)

```bash
# Install ngrok (if not already)
# Start tunnel
ngrok http 8080
```

Copy the HTTPS URL (e.g., `https://xxxx.ngrok-free.app`)

---

## Step 7: Jenkins Credentials

Go to **Manage Jenkins → Credentials → System → Global credentials → Add Credentials**

Add all 9 credentials:

| ID | Kind | Value / Description |
|---|---|---|
| `aws-access-key-id` | Secret text | Your AWS Access Key ID |
| `aws-secret-access-key` | Secret text | Your AWS Secret Access Key |
| `ec2-host` | Secret text | Your EC2 public IP (e.g., `3.82.145.67`) |
| `ec2-ssh-key` | SSH Username with private key | Username: `ubuntu`, Private Key: contents of `.pem` file |
| `mongo-uri` | Secret text | Full Atlas connection string with real password |
| `flask-secret-key` | Secret text | Random secret string for Flask |
| `sendgrid-api-key` | Secret text | SendGrid API key (starts with `SG.`) |
| `email-to` | Secret text | Recipient email (e.g., `amarjyoti.lahkar@gmail.com`) |
| `email-from` | Secret text | Verified SendGrid sender email |

> **Note:** For `ec2-ssh-key`, paste the entire contents of your `.pem` file including `-----BEGIN OPENSSH PRIVATE KEY-----` and `-----END OPENSSH PRIVATE KEY-----`.

---

## Step 8: GitHub Webhook Configuration

### 8.1 Configure Webhook in GitHub

1. Go to your forked repo: `https://github.com/AmarGmail/ci-cd-pipeline`
2. **Settings → Webhooks → Add webhook**
3. **Payload URL:** `https://YOUR_NGROK_URL.ngrok-free.app/github-webhook/`
4. **Content type:** `application/json`
5. **Which events?** Just the **push** event
6. **Active:** ✅ checked
7. Click **Add webhook**

### 8.2 Create Jenkins Pipeline Job

1. **New Item** → Name: `student-registration` → **Pipeline**
2. **Build Triggers:** Check **"GitHub hook trigger for GITScm polling"**
3. **Pipeline → Definition:** Pipeline script from SCM
4. **SCM:** Git
5. **Repository URL:** `https://github.com/YOUR_USERNAME/ci-cd-pipeline.git`
6. **Branch:** `*/main`
7. **Script Path:** `Jenkinsfile`
8. Click **Save**

---

## Step 9: Pipeline Stages

![Jenkins Pipeline Overview](screenshots/Build_Pipeline_Stages.jpg)


The pipeline (`Jenkinsfile`) consists of 8 automated stages:

### Stage 1: Checkout
- Pulls the latest source code from the `main` branch
- Captures the Git commit SHA for image tagging

### Stage 2: Install
- Creates a Python virtual environment (`venv`)
- Installs all dependencies from `requirements.txt`

### Stage 3: Test
- Sets `MONGO_URI` to local test database
- Runs `pytest test_app.py`
- **Stops the pipeline if any test fails**
- Archives test output as a build artifact

### Stage 4: Build
- Builds a Docker image tagged with the commit SHA
- Also tags as `latest`

### Stage 5: Push to ECR
- Authenticates with AWS ECR using credentials
- Pushes both the SHA-tagged image and `latest` tag

### Stage 6: Deploy to EC2
- SSH into the production EC2 instance
- Logs into ECR from EC2
- Pulls the latest Docker image
- Stops and removes the old container
- Starts a new container with Atlas connection

### Stage 7: Verify (Success Gate)
- Polls the `/health` endpoint up to 5 times
- Checks MongoDB Atlas connectivity
- **If health check passes:** pipeline continues
- **If health check fails:** pipeline stops, container logs are captured

### Stage 8: Notify
- Sends an HTML email via SendGrid
- Includes build status, number, timestamp, and Jenkins URL
- **Success:** Green email with ✅
- **Failure:** Red email with ❌

---

## Step 10: Trigger & Monitor

### Trigger a Build

```bash
# Make any change and push
echo "# CI/CD Pipeline Ready" >> README.md
git add README.md
git commit -m "Trigger Jenkins build"
git push origin main
```

The GitHub webhook will automatically trigger the Jenkins pipeline.

### Monitor Build Progress

1. Open Jenkins: `http://localhost:8080/job/student-registration/`
2. Click the build number
3. Click **Console Output** to watch live logs

### Verify Deployment

```bash
# Test health endpoint
curl http://<EC2_PUBLIC_IP>:5000/health

# Expected response:
# {"status":"healthy","database":"connected","timestamp":"..."}

# Test the application
curl http://<EC2_PUBLIC_IP>:5000/
```

### Email Verification

![Email Verification](screenshots/Build-Success-Report-Email.jpg)

---

## Step 11: Intentional Pipeline Failed at Test Stage

To verify that the pipeline correctly stops and sends a failure email when tests fail:

### 11.1 Add an Intentional Failure Test

Add this to `test_app.py`:

```python
def test_intentional_failure(client):
    """Intentional failure to test email notification"""
    assert False, "This test is designed to fail for pipeline testing"

![Forced build failure email](screenshots/Intentional-build-failed-at-test-stage.jpg)

---
## Troubleshooting

| Issue | Cause | Solution |
|---|---|---|
| `docker: permission denied` | Jenkins user not in docker group | `sudo usermod -aG docker jenkins && sudo systemctl restart jenkins` |
| `aws: command not found` | AWS CLI not installed | Install AWS CLI on Jenkins host and EC2 |
| `pytest: command not found` | pytest not in venv | `pip install pytest` in venv |
| `ssh: Connection timed out` | EC2 security group blocks port 22 | Add your IP to EC2 security group |
| `bad auth : authentication failed` | Wrong MongoDB password in credential | Update `mongo-uri` credential with real password |
| `No such container: student-reg` | Container crashed immediately | Check `docker logs` on EC2 for MongoDB connection errors |
| `HEALTH CHECK FAILED` | Atlas IP not whitelisted | Add EC2 public IP to MongoDB Atlas Network Access |
| `Email not received` | SendGrid sender not verified | Verify sender email in SendGrid dashboard |
| `ngrok URL changed` | ngrok tunnel expired | Restart ngrok and update GitHub webhook URL |
| `sshagent not found` | Plugin not installed | Install **SSH Agent** plugin in Jenkins |

---

## Project Structure

```
ci-cd-pipeline/
├── .github/
│   └── workflows/           # (Optional) GitHub Actions backup
├── scripts/
│   ├── deploy_to_ec2.sh     # EC2 deployment script
│   ├── health_check.sh      # Health verification script
│   └── email_report.py      # SendGrid email notification
├── templates/
│   ├── base.html            # Base HTML template
│   └── index.html           # Student list page
├── screenshots/             # Add the screenshots here
├── app.py                   # Flask application
├── Dockerfile               # Docker image definition
├── docker-compose.yml       # (Optional) Local compose setup
├── Jenkinsfile              # CI/CD pipeline definition
├── requirements.txt         # Python dependencies
├── test_app.py              # pytest test suite
├── pytest.ini               # pytest configuration
├── .dockerignore            # Docker build exclusions
├── .gitignore               # Git exclusions
└── README.md                # This file
```

---

## Key Files Reference

### app.py - Flask Application
- Flask app with MongoDB integration
- Routes: `/`, `/add`, `/update/<id>`, `/delete/<id>`, `/health`
- `/health` endpoint verifies MongoDB Atlas connectivity

### test_app.py - Test Suite
- 4 tests: home page, add student, update student, delete student
- Uses local MongoDB (`mongodb://localhost:27017/test_student_db`)
- Clears and seeds test data before each test

### Dockerfile
- Based on `python:3.12-slim`
- Installs `gcc` for native dependencies
- Uses `gunicorn` production WSGI server
- Exposes port 5000

### Jenkinsfile
- Declarative pipeline with 8 stages
- Uses `sshagent` for EC2 SSH authentication
- Uses `withCredentials` for secure secret injection
- Archives test artifacts and cleans workspace

---

## Security Best Practices

1. **Never commit secrets** - `.env`, passwords, or API keys
2. **Use Jenkins Credentials** - All secrets stored in Jenkins, not in code
3. **IP Whitelisting** - Restrict MongoDB Atlas and EC2 SSH to known IPs
4. **URL-encode passwords** - If MongoDB password contains special characters
5. **Rotate credentials** - Periodically update AWS keys and SendGrid tokens
6. **ECR lifecycle policy** - Auto-delete old images to reduce storage costs

---

## License

This project is for educational purposes as part of a CI/CD DevOps assignment.

---

## Author

- **GitHub:** [AmarGmail](https://github.com/AmarGmail)
- **Original Repository:** [mohanDevOps-arch/flask_Practice](https://github.com/mohanDevOps-arch/flask_Practice)

---

**End-to-End CI/CD Pipeline: Git Push → Jenkins → Docker → ECR → EC2 → Health Check → Email Report**
