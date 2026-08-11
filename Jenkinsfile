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
            post {
                failure {
                    script { env.FAILED_STAGE = 'Checkout' }
                }
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
            post {
                failure {
                    script { env.FAILED_STAGE = 'Install' }
                }
            }
        }

        stage('Test') {
            steps {
                sh '''#!/bin/bash
                    set -e
                    set -o pipefail
                    export MONGO_URI="mongodb://localhost:27017/test_student_db"
                    export SECRET_KEY="test-secret-key"
                    venv/bin/pytest test_app.py -v --tb=short 2>&1 | tee test_output.txt
                '''
            }
            post {
                always {
                    archiveArtifacts artifacts: 'test_output.txt', allowEmptyArchive: true
                }
                failure {
                    script { env.FAILED_STAGE = 'Test' }
                }
            }
        }

        stage('Build') {
            steps {
                sh '''
                    docker build -t "${IMAGE_NAME}:${IMAGE_TAG}" .
                    docker tag "${IMAGE_NAME}:${IMAGE_TAG}" "${FULL_IMAGE}"
                    docker tag "${IMAGE_NAME}:${IMAGE_TAG}" "${LATEST_IMAGE}"
                '''
            }
            post {
                failure {
                    script { env.FAILED_STAGE = 'Build' }
                }
            }
        }

        // AWS start
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
            post {
                failure {
                    script { env.FAILED_STAGE = 'Push to ECR' }
                }
            }
        }

        // The deploy stage calling a script to perform the deployment tasks
        // To avoid interpolation confusion between groovy to local shell to EC2 shell
        stage('Deploy to EC2') {
            steps {
                sshagent(credentials: ['ec2-ssh-key']) {
                    sh '''

                        echo "Copying deployment script to EC2..."

                        scp -o StrictHostKeyChecking=no \
                            scripts/deploy_to_ec2.sh \
                            "${EC2_USER}@${EC2_HOST}:/tmp/deploy_to_ec2.sh"

                        echo "Running deployment script on EC2..."


                        ssh -o StrictHostKeyChecking=no \
                            "${EC2_USER}@${EC2_HOST}" \
                            "chmod +x /tmp/deploy_to_ec2.sh && \
                            AWS_REGION='${AWS_REGION}' \
                            ECR_REGISTRY='${ECR_REGISTRY}' \
                            FULL_IMAGE='${FULL_IMAGE}' \
                            MONGO_URI='${MONGO_URI}' \
                            SECRET_KEY='${SECRET_KEY}' \
                            /tmp/deploy_to_ec2.sh"
                    '''
                }
            }
            post {
                failure {
                    script { env.FAILED_STAGE = 'Deploy to EC2' }
                }
            }
        }

        // define scripts/health_check.sh 
        // copy to ec2 are run from there
        stage('Verify') {
            steps {
                sshagent(credentials: ['ec2-ssh-key']) {
                    sh '''
                        scp -o StrictHostKeyChecking=no \
                            scripts/health_check.sh \
                            "$EC2_USER@$EC2_HOST:/tmp/health_check.sh"

                        ssh -o StrictHostKeyChecking=no \
                            "$EC2_USER@$EC2_HOST" \
                            "chmod +x /tmp/health_check.sh && /tmp/health_check.sh" 
                    '''
                }
            }
            post {
                failure {
                    script { env.FAILED_STAGE = 'Verify' }
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
                    export COMMIT_SHA="${COMMIT_SHA}"
                    export IMAGE_TAG="${IMAGE_TAG}"
                    export FAILED_STAGE="${FAILED_STAGE:-}"
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