# -------------------------------------------------------------
# Importation des librairies
# -------------------------------------------------------------

import os
import json
import requests
import re
import textwrap
import base64
from dotenv import load_dotenv
from discord_webhook import DiscordWebhook, DiscordEmbed
from PIL import Image, ImageDraw, ImageFont
from MinecraftIpToGuiImage.src import loader
from time import sleep

# -------------------------------------------------------------
# Importation des paramètres ( fichier .env )
# -------------------------------------------------------------

load_dotenv()

# Paramètres réseau
START_IP = os.getenv('START_IP')
NETMASK = os.getenv('NETMASK')
END_IP = os.getenv('END_IP')
PORT = os.getenv('PORT')

# Paramètres Minecraft
MC_EDITION = os.getenv('EDITION')
MC_VERSION = os.getenv('VERSION')
MC_ONLINE_PLAYERS = int(os.getenv('ONLINE_PLAYERS'))

# Paramètres Discord
DS_WEBHOOK = os.getenv('WEBHOOK')
DS_BOT_NAME = os.getenv('BOT_NAME')
DS_WEBHOOK_COLOR = os.getenv('WEBHOOK_COLOR')

# -------------------------------------------------------------
# Lancement du scan avec l'outil MasScan
# -------------------------------------------------------------

MASSCAN_FILE = 'masscan.txt'
MASSCAN_COMMAND = f'masscan -p{PORT} {START_IP}/{str(NETMASK)} --exclude 255.255.255.255 -oL {MASSCAN_FILE}'

if not os.path.exists(MASSCAN_FILE):
    try:
        os.system(MASSCAN_COMMAND)
    except:
        print('Merci d\'installer l\'outil MasScan pour scanner les IP')
        exit()

# -------------------------------------------------------------
# Traitement du scan MasScan
# -------------------------------------------------------------

MASSCAN_SORTED_FILE = 'sorted_masscan.txt'

if not os.path.exists(MASSCAN_SORTED_FILE):
    with open(MASSCAN_FILE, 'r') as mf:
        lines = mf.readlines()

    pattern = re.compile(r'\b(?:\d{1,3}\.){3}\d{1,3}\b')
    ips = [pattern.search(line).group() for line in lines if pattern.search(line)]

    for ip in ips:
        with open(MASSCAN_SORTED_FILE, 'a') as msf:
            msf.write(ip+'\n')

# -------------------------------------------------------------
# Définition des fonctions
# -------------------------------------------------------------

def get_mc_stats(ip, port):
    if MC_EDITION == 'bedrock':
        url = f'https://api.mcstatus.io/v2/status/bedrock/{ip}:{port}'
    else:
        url = f'https://api.mcstatus.io/v2/status/java/{ip}:{port}'
    
    req = requests.get(url)
    res = json.loads(req.text)

    online = res['online']

    if online:
        if MC_VERSION:
            if MC_VERSION in res['version']['name_raw']:
                if MC_ONLINE_PLAYERS:
                    if res['players']['online'] >= MC_ONLINE_PLAYERS:
                        return res
                else:
                    return res
        else:
            if MC_ONLINE_PLAYERS:
                if res['players']['online'] >= MC_ONLINE_PLAYERS:
                    return res
            else:
                return res

    return False

def get_country(ip):
    url = f'http://ip-api.com/json/{ip}'
    req = requests.get(url)
    res = json.loads(req.text)

    if res['status'] == 'success':
        return res['countryCode'].lower()
    else:
        return None

def send_discord(mc_stats):
    webhook = DiscordWebhook(url=DS_WEBHOOK, username=DS_BOT_NAME)

    mc_srv_software = mc_stats['version']['name_clean']
    mc_srv_ip = mc_stats['host']
    mc_srv_port = mc_stats['port']
    mv_srv_players_list = mc_stats['players']['list']

    try:
        loader.loadandrun(serverip=f'{mc_srv_ip}:{mc_srv_port}', edition=MC_EDITION)

        with open("motd.png", "rb") as motd_file:
            webhook.add_file(file=motd_file.read(), filename='motd.png')
    except:
        if os.path.exists('motd.png'):
            os.remove('motd.png')

        with open("empty_motd.png", "rb") as empty_motd_file:
            webhook.add_file(file=empty_motd_file.read(), filename='empty_motd.png')

        print('Cannot get MOTD image !')

    country = get_country(mc_srv_ip)

    if country:
        embed = DiscordEmbed(title=f":flag_{country}: Serveur trouvé !", description="Un serveur a été trouvé", color=DS_WEBHOOK_COLOR)
    else:
        embed = DiscordEmbed(title="Serveur trouvé !", description="Un serveur a été trouvé", color=DS_WEBHOOK_COLOR)

    if MC_VERSION:
        embed.add_embed_field(name='Édition de Minecraft', value=f'```{MC_EDITION}```', inline=True)
        embed.add_embed_field(name='Version', value=f'```{MC_VERSION}```', inline=True)
    else:
        embed.add_embed_field(name='Édition de Minecraft', value=f'```{MC_EDITION}```', inline=False)

    embed.add_embed_field(name='IP', value=f'```{mc_srv_ip}```', inline=True)
    embed.add_embed_field(name='PORT', value=f'```{mc_srv_port}```', inline=True)
    embed.add_embed_field(name='Logiciel détécté', value=f'```{mc_srv_software}```', inline=False)

    if mv_srv_players_list:
        clean_players_list = []

        for player in mv_srv_players_list:
            clean_players_list.append(player['name_clean'])

        embed.add_embed_field(name='Liste des joueurs', value=f'```{clean_players_list}```', inline=False)
        webhook.content = '@everyone'

    if os.path.exists('motd.png'):
        embed.set_image(url='attachment://motd.png')
    else:
        embed.set_image(url='attachment://empty_motd.png')

    webhook.add_embed(embed)
    webhook.execute()

# -------------------------------------------------------------
# Boucler sur les IP triés
# -------------------------------------------------------------

with open(MASSCAN_SORTED_FILE, 'r') as msf:
    ips = msf.readlines()

if not os.path.exists('valid_servers.json'):
    with open('valid_servers.json', 'w') as f:
        json.dump({}, f)
elif not os.path.exists('invalid_servers.json'):
    with open('invalid_servers.json', 'w') as f:
        json.dump({}, f)

with open('valid_servers.json', 'r') as vsf:
    valid_servers_data = json.load(vsf)

with open('invalid_servers.json', 'r') as vsf:
    invalid_servers_data = json.load(vsf)

for t_ip in ips:
    t_ip = t_ip.strip()
    port_key = str(PORT)

    if port_key not in valid_servers_data:
        valid_servers_data[port_key] = []
    elif port_key not in invalid_servers_data:
        invalid_servers_data[port_key] = []

    if t_ip not in valid_servers_data[port_key] and t_ip not in invalid_servers_data[port_key]:
        try:
            stats = get_mc_stats(ip=t_ip, port=PORT)
        except:
            print('Erreur à la récupération des statistiques ! Reprise dans 10 secondes...')
            sleep(10)
            continue

        if stats:
            print(f'SERVEUR TROUVÉ : {t_ip}:{PORT}')

            send_discord(mc_stats=stats)
            valid_servers_data[port_key].append(t_ip)

            with open('valid_servers.json', 'w', encoding='utf-8') as vsf:
                json.dump(valid_servers_data, vsf, ensure_ascii=False, indent=4)
        else:
            print(f'SERVEUR NON VALIDE : {t_ip}:{PORT}')

            invalid_servers_data[port_key].append(t_ip)

            with open('invalid_servers.json', 'w', encoding='utf-8') as vsf:
                json.dump(invalid_servers_data, vsf, ensure_ascii=False, indent=4)
    else:
        print(f'IP DÉJÀ ANALYSÉE : {t_ip}:{PORT}')

print('SCAN TERMINÉ !')

# -------------------------------------------------------------
# Néttoyage des fichiers
# -------------------------------------------------------------

if os.path.exists('motd.png'):
    os.remove('motd.png')
if os.path.exists(MASSCAN_SORTED_FILE):
    os.remove(MASSCAN_SORTED_FILE)
