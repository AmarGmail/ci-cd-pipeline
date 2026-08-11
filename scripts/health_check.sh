#!/bin/bash
set -u 
echo "Polling /health endpoint..."

for i in 1 2 3 4 5; do
    echo "Health Check - Attempt $i..."

    if curl -sf http://localhost:5000/health > /dev/null; then
        echo "HEALTH CHECK PASSED"
        exit 0
    fi

    sleep 5
done

echo "HEALTH CHECK FAILED after 5 attempts"

docker logs student-reg || true

exit 1


