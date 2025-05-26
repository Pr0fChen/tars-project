#!/bin/bash
sudo -i

# 1) Mise à jour du système
apt-get update && apt-get upgrade -y

# 2) Installation des dépendances système
apt-get install -y python3 python3-pip python3-flask

# 3) Installation du client OpenAI en user-local
#    (le module sera dans /root/.local)
pip3 install --user openai --break-package-system

# 4) Création des scripts Python vides
touch /root/tars_personality.py /root/tars_brain_server.py
chmod 600 /root/tars_personality.py /root/tars_brain_server.py

# 5) Déploiement du service systemd
cat << 'EOF' > /etc/systemd/system/tars.service
[Unit]
Description=TARS Brain Server

[Service]
WorkingDirectory=/root
Environment="OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxx"
ExecStart=/usr/bin/python3 /root/tars_brain_server.py
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# 6) Activation et démarrage
systemctl daemon-reload
systemctl enable tars
systemctl start tars

cat << 'EOF' > /root/install_docker.sh
#!/bin/bash

apt-get install apt-transport-https ca-certificates curl gnupg2 software-properties-common sudo
curl -fsSL https://download.docker.com/linux/$(. /etc/os-release; echo "$ID")/gpg | sudo apt-key add -
add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/$(. /etc/os-release; echo "$ID") $(lsb_release -cs) stable"
apt-get update
apt-get install docker-ce
curl -L https://github.com/docker/compose/releases/download/1.19.0/docker-compose-`uname -s`-`uname -m` -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose
docker-compose --version

curl -fsSL https://get.docker.com/ -o get-docker.sh
sh get-docker.sh
EOF

chmod u+x install_docker.sh
./install_docker.sh

echo "Installation terminée"
