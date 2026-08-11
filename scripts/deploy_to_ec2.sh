#!/bin/bash
set -e

echo "----------------------"
echo "Staring deployment"
echo "----------------------"

echo "Logging into ECR..."
aws ecr get-login-password --region "${AWS_REGION}" |
    docker login \
        --username AWS \
        --password-stdin "${ECR_REGISTRY}"

echo "Pulling image: ${FULL_IMAGE}"
docker pull "${FULL_IMAGE}"

echo "Stopping existing container..."
docker stop student-reg || true

echo "Removing existing container..."
docker rm student-reg || true

echo "Starting new container..."
docker run -d \
    -p 5000:5000 \
    -e MONGO_URI="${MONGO_URI}" \
    -e SECRET_KEY="${SECRET_KEY}" \
    --name student-reg \
    "${FULL_IMAGE}"

echo "Checking container status..."
docker ps -a --filter name=student-reg

echo "Container logs..."
docker logs student-reg || true

echo "----------------------"
echo "Deployment completed"
echo "----------------------"