pipeline {
    agent any

    environment {
        AWS_REGION      = 'us-east-1'
        ECR_REGISTRY    = '729598252377.dkr.ecr.us-east-1.amazonaws.com'
        IMAGE_NAME      = 'student-registration'
        COMMIT_SHA      = sh(script: 'git rev-parse --short HEAD', returnStdout: true).trim()
        IMAGE_TAG       = "${COMMIT_SHA}"
        FULL_IMAGE      = "${ECR_REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}"
        LATEST_IMAGE    = "${ECR_REGISTRY}/${IMAGE_NAME}:latest"
        EC2_HOST        = credentials('ec2-host')
        EC2_USER        = 'ubuntu'
        MONGO_URI       = credentials('mongo-uri')
        SECRET_KEY      = credentials('flask-secret-key')
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
                sh 'echo "Build ${BUILD_NUMBER} | Commit: ${COMMIT_SHA}"'
            }
        }

        stage('Install') {
            steps {
                sh '''
                    python3 -m venv venv
                    venv/bin/pip install --upgrade pip
                    venv/bin/pip install -r requirements.txt
                '''
            }
        }

        stage('Test') {
            steps {
                sh '''
                    export MONGO_URI="mongodb://localhost:27017/test_student_db"
                    export SECRET_KEY="test-secret-key"
                    venv/bin/pytest test_app.py -v --tb=short 2>&1 | tee test_output.txt
                '''
            }
            post {
                always {
                    archiveArtifacts artifacts: 'test_output.txt', allowEmptyArchive: true
                }
            }
        }

        stage('Build') {
            steps {
                sh """
                    docker build -t ${IMAGE_NAME}:${IMAGE_TAG} .
                    docker tag ${IMAGE_NAME}:${IMAGE_TAG} ${FULL_IMAGE}
                    docker tag ${IMAGE_NAME}:${IMAGE_TAG} ${LATEST_IMAGE}
                """
            }
        }

        stage('Push to ECR') {
            steps {
                withCredentials([
                    string(credentialsId: 'aws-access-key-id', variable: 'AWS_ACCESS_KEY_ID'),
                    string(credentialsId: 'aws-secret-access-key', variable: 'AWS_SECRET_ACCESS_KEY')
                ]) {
                    sh """
                        export AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID}
                        export AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY}
                        export AWS_DEFAULT_REGION=${AWS_REGION}
                        aws ecr get-login-password --region ${AWS_REGION} | docker login --username AWS --password-stdin ${ECR_REGISTRY}
                        docker push ${FULL_IMAGE}
                        docker push ${LATEST_IMAGE}
                    """
                }
            }
        }

        stage('Deploy to EC2') {
            steps {
                sshagent(credentials: ['ec2-ssh-key']) {
                    sh """
                        ssh -o StrictHostKeyChecking=no ${EC2_USER}@${EC2_HOST} "aws ecr get-login-password --region ${AWS_REGION} | docker login --username AWS --password-stdin ${ECR_REGISTRY}"
                            
                        ssh -o StrictHostKeyChecking=no ${EC2_USER}@${EC2_HOST} "docker pull ${FULL_IMAGE}"
                            
                        ssh -o StrictHostKeyChecking=no ${EC2_USER}@${EC2_HOST} "docker stop student-reg || true; docker rm student-reg || true"
                            
                        ssh -o StrictHostKeyChecking=no ${EC2_USER}@${EC2_HOST} "docker run -d -p 5000:5000 -e MONGO_URI='${MONGO_URI}' -e SECRET_KEY='${SECRET_KEY}' --name student-reg ${FULL_IMAGE}"    
                        
                        ssh -o StrictHostKeyChecking=no ${EC2_USER}@${EC2_HOST} "docker system prune -f"
                    """
                }
            }
        }

        stage('Verify') {
            steps {
                sshagent(credentials: ['ec2-ssh-key']) {
                    sh """
                        ssh -o StrictHostKeyChecking=no ${EC2_USER}@${EC2_HOST} 
                        "echo 'Polling /health endpoint...' 
                        for i in 1 2 3 4 5 
                        do 
                            echo Attempt \\$i... 
                            if curl -sf http://localhost:5000/health > /dev/null 
                            then 
                                echo 'HEALTH CHECK PASSED'
                                exit 0
                            fi 
                            sleep 5
                        done 
                        echo 'HEALTH CHECK FAILED' 
                        docker logs student-reg || true 
                        exit 1"
                    """
                }
            }
        }
    }

    post {
        always {
            script {
                env.BUILD_STATUS = currentBuild.result ?: 'SUCCESS'
            }
            withCredentials([
                string(credentialsId: 'sendgrid-api-key', variable: 'SENDGRID_API_KEY'),
                string(credentialsId: 'email-to', variable: 'EMAIL_TO'),
                string(credentialsId: 'email-from', variable: 'EMAIL_FROM')
            ]) {
                sh '''
                    export BUILD_STATUS="${BUILD_STATUS}"
                    export BUILD_NUMBER="${BUILD_NUMBER}"
                    export BUILD_URL="${BUILD_URL}"
                    export JOB_NAME="${JOB_NAME}"
                    export SENDGRID_API_KEY="${SENDGRID_API_KEY}"
                    export EMAIL_TO="${EMAIL_TO}"
                    export EMAIL_FROM="${EMAIL_FROM}"
                    python3 scripts/email_report.py || true
                '''
            }
            cleanWs()
        }
    }
}