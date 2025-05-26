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

echo "Installation terminée"
