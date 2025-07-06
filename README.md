# 🧭 Minecraft Server Scanner

Un outil de scan de serveurs Minecraft (Java/Bedrock), utilisant `masscan`, filtrant selon des critères personnalisables, et envoyant les résultats sur Discord via un webhook.

## 🚀 Fonctionnalités

- Scan rapide des plages d'IP grâce à `masscan`.
- Vérification des serveurs Minecraft actifs selon :
  - Édition (`java` / `bedrock`)
  - Version spécifique (optionnelle)
  - Nombre minimal de joueurs connectés
- Génération automatique d'une image MOTD
- Envoi des résultats via Webhook Discord
- Géolocalisation du serveur (pays)

---

## 📦 Installation

### 1. Prérequis

- Python 3.13+
- `masscan` installé sur la machine (obligatoire)
- Accès administrateur (pour exécuter `masscan`)
- `pip` pour installer les dépendances Python

### 2. Clone du dépôt

```bash
git clone https://github.com/votre-utilisateur/minecraft-server-scanner.git
cd minecraft-server-scanner
```

### 3. Installation des dépendances Python

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 4. Configuration

Renommez le fichier `env` en `.env` :

```bash
mv env .env
```

Modifiez les variables à l’intérieur selon vos besoins :

```env
# Réseau
START_IP='0.0.0.0'          # IP de début
NETMASK=0                   # Masque de sous-réseau CIDR
END_IP='255.255.255.255'    # IP de fin
PORT=25565                  # Port Minecraft

# Minecraft
EDITION='java'              # java / bedrock
VERSION=''                  # (optionnel) Ex: 1.21.4
ONLINE_PLAYERS=0            # Nombre de joueurs minimum requis

# Discord
WEBHOOK='WEBHOOK_URL'
BOT_NAME='MinecraftScrapperBot'
WEBHOOK_COLOR='3390ff'
```

### 5. Lancement

```bash
python3 main.py
```

---

## 💻 Pour Windows

1. **Installer Masscan**  
   - Téléchargez la version Windows de [masscan ici](https://github.com/robertdavidgraham/masscan/releases).  
   - Décompressez l’archive et placez `masscan.exe` dans un dossier accessible (ex : `C:\masscan\`).  
   - Ajoutez ce dossier au PATH système (Paramètres > Variables d’environnement).

2. **Installer Python**  
   - Installez Python 3.8+ depuis [python.org](https://www.python.org/downloads/windows/).  
   - Pendant l’installation, cochez "Add Python to PATH".

3. **Installer les dépendances Python**

```powershell
python -m venv venv
.\venv\Scripts\Activate.bat
pip install -r requirements.txt
```

4. **Configuration**

Renommez `env` en `.env` (vous pouvez faire ça dans l’explorateur ou via PowerShell) et modifiez-le selon vos besoins.

5. **Exécuter le script**

Ouvrez PowerShell ou CMD, placez-vous dans le dossier du projet et lancez :

```powershell
python main.py
```

---

## 🔧 Fonctionnement

1. Lance un scan massif sur le port Minecraft avec `masscan`.
2. Trie les IPs détectées.
3. Interroge chaque IP pour récupérer les infos du serveur via l’API [mcstatus.io](https://mcstatus.io/).
4. Filtre les serveurs selon vos critères.
5. Envoie une notification sur Discord pour chaque serveur valide :
   - IP, Port, Version
   - Liste des joueurs connectés
   - Image MOTD (si disponible)
   - Drapeau du pays (via [ip-api.com](http://ip-api.com))
   - Liste des joueurs (si au moins 1 joueur est connecté au serveur) + mention @everyone sur Discord

---

## 🗂 Fichiers générés

- `masscan.txt` : Résultat brut du scan `masscan`
- `sorted_masscan.txt` : Liste triée des IPs détectées
- `valid_servers.json` : Liste des serveurs déjà trouvés
- `motd.png` : Image du MOTD du serveur

---

## ⚠️ Avertissements

- **N’utilisez cet outil que sur des plages IP que vous êtes autorisé à scanner.**
- Le scan massif peut être détecté comme une attaque réseau. Utilisez avec précaution.
- L'outil `masscan` nécessite souvent des privilèges d'administrateur ( root sous Linux ).

---

## 🙏 Remerciements

- [masscan](https://github.com/robertdavidgraham/masscan)
- [mcstatus.io](https://mcstatus.io)
- [discord-webhook](https://github.com/lovvskillz/python-discord-webhook)
- [MinecraftIpToGuiImage](https://github.com/TejasIsCool/MinecraftIpToGuiImage)
