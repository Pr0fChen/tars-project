# 1. Image de base légère avec Python 3
FROM python:3.12-slim

# 2. Crée et positionne-toi dans /app
WORKDIR /app

# 3. Copie des dépendances et installation
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# 4. Copie de ton code
COPY tars_brain_server.py ./

# 5. Expose le port Flask
EXPOSE 5000

# 6. Commande de démarrage
CMD ["gunicorn", "-b", "0.0.0.0:5000", "tars_brain_server:app"]
