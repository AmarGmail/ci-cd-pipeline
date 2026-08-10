#!/bin/bash
cd ~/flask_Practice

# Create venv if not exists
if [ ! -d venv ]; then
    python3 -m venv venv
fi

# Activate venv
source venv/bin/activate

# Upgrade pip and install dependencies
sudo apt update
sudo apt install python3-pip -y
sudo pip install --upgrade pip
sudo pip install -r requirements.txt black pylint bandit pytest pytest-html

# Ensure .env exists
#echo -e "MONGO_URI=mongodb+srv://mohan:Herovired123@herovired.f3do4.mongodb.net/studentDB\nSECRET_KEY=your-secret-key" > .env
#echo -e "MONGO_URI="mongodb+srv://amarjyotilahkar_db_user:xxxxxxx@cluster0.omg67uu.mongodb.net/studentDB\nSECRET_KEY=your-secret-key > .env
cat > .env << 'EOF'
MONGO_URI="mongodb+srv://amarjyotilahkar_db_user:<MY_PASSWORD>@cluster0.omg67uu.mongodb.net/studentDB?retryWrites=true&w=majority"
SECRET_KEY="<MY_SECRET>"
EOF

# Run app
sudo nohup python3 app.py --host=0.0.0.0 --port=5000 > flask.log 2>&1 &
