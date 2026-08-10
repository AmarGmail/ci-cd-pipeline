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
                sh 'echo "Commit SHA: ${COMMIT_SHA}"'
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

        stage ('Tests') {
            steps {
                sh '''
                    export MONGO_URI="mongodb://localhost:27017/test_student_db"
                    export SECRET_KEY="test-secret-key"
                    venv/bin/pytest test_app.py -v --tb=short 2>&1 | tee test_output.txt
                '''
            }
            post {
                always {
                    archiveArtifacts artifacts: 'test_output.txt', allowEmptyArchieve: true
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
                sshagent(['ec2-ssh-key']) {
                    sh """
                        ssh -o StrictHostKeyChecking=no ${EC2_USER}@${EC2_HOST} << REMOTE
                        set -e
                        # Login to ECR
                        aws ecr get-login-password --region ${AWS_REGION} | docker login --username AWS --password-stdin ${ECR_REGISTRY}
                        
                        # Pull the commit-SHA tagged image
                        docker pull ${FULL_IMAGE}
                        
                        # Stop and remove old container
                        docker stop student-reg || true
                        docker rm student-reg || true
                        
                        # Run new container with Atlas connection
                        docker run -d -p 5000:5000 -e MONGO_URI="${MONGO_URI}" \\
                            -e SECRET_KEY="${SECRET_KEY}" \\
                            --name student-reg \\
                            ${FULL_IMAGE}
                        
                        # Cleanup dangling images
                            docker system prune -f
                        REMOTE
                    """
                }
            }
        }

        stage('verify') {
            steps {
                sshagent(['ec2-ssh-key']) {
                    sh """
                        ssh -o StrictHostKeyChecking=no ${EC2_USER}@${EC2_HOST} << REMOTE
                            echo "Polling /health endpoint..."
                            for i in 1 2 3 4 5; do
                                echo "Attempt \$i..."
                                if curl -sf http://localhost:5000/health > /dev/null; then
                                    echo "✅ HEALTH CHECK PASSED"
                                    exit 0
                                fi
                                sleep 5
                            done
                            echo "❌ HEALTH CHECK FAILED after 5 attempts"
                            docker logs student-reg || true
                            exit 1
                        REMOTE
                    """
                }
            }
        }    
    }
    post {
        always {
            env.BUILD_STATUS = currentBuild.result ?: 'SUCCESS'
        }
        sh '''
            export BUILD_STATUS="${BUILD_STATUS}"
            export BUILD_NUMBER="${BUILD_NUMBER}"
            export BUILD_URL="${BUILD_URL}"
            export JOB_NAME="${JOB_NAME}"
            python3 scripts/email_report.py || true
        '''
        cleanWS()
    }
}