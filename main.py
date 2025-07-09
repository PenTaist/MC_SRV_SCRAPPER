# -------------------------------------------------------------
# Importation des librairies
# -------------------------------------------------------------

import os
import json
import requests
import re
import textwrap
import base64
import logging
import shutil
from dotenv import load_dotenv
from discord_webhook import DiscordWebhook, DiscordEmbed
from PIL import Image, ImageDraw, ImageFont
from MinecraftIpToGuiImage.src import loader
from time import sleep
from mcstatus import JavaServer

# -------------------------------------------------------------
# Sauvegardes des listes de serveurs si existantes
# -------------------------------------------------------------

if os.path.exists('valid_servers.json'):
    os.remove('valid_servers.json.bak')
    shutil.copyfile('valid_servers.json', 'valid_servers.json.bak')

if os.path.exists('invalid_servers.json'):
    os.remove('invalid_servers.json.bak')
    shutil.copyfile('invalid_servers.json', 'invalid_servers.json.bak')

# -------------------------------------------------------------
# Configuration des logs
# -------------------------------------------------------------

logger = logging.getLogger(__name__)
logging.basicConfig(filename='program.log', encoding='utf-8', level=logging.INFO, datefmt='%Y-%m-%d %H:%M:%S')

# -------------------------------------------------------------
# Move auto du env en .env
# -------------------------------------------------------------

if os.path.exists('env') and not os.path.exists('.env'):
    os.rename('env', '.env')

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
MC_COUNTRY = os.getenv('COUNTRY')

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
        logger.info('Lancement de la commande MasScan')
    except:
        print('Merci d\'installer l\'outil MasScan pour scanner les IP')
        logger.warning('Outil MasScan non installé')
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

    logger.info('Fichier sorted_masscan.txt créé')

# -------------------------------------------------------------
# Définition des fonctions
# -------------------------------------------------------------

def get_mc_stats(ip, port):
    global detected_mc_edition

    if MC_EDITION == 'java':
        url = f'https://api.mcstatus.io/v2/status/java/{ip}:{port}'

        req = requests.get(url)
        res = json.loads(req.text)

        if not res['online']:
            return False
    elif MC_EDITION == 'bedrock':
        url = f'https://api.mcstatus.io/v2/status/bedrock/{ip}:{port}'

        req = requests.get(url)
        res = json.loads(req.text)

        if not res['online']:
            return False
    else:
        req = requests.get(f'https://api.mcstatus.io/v2/status/java/{ip}:{port}')
        res = json.loads(req.text)

        if res['online']:
            detected_mc_edition = 'java'
        else:
            req = requests.get(f'https://api.mcstatus.io/v2/status/bedrock/{ip}:{port}')
            res = json.loads(req.text)

            if res['online']:
                detected_mc_edition = 'bedrock'
            else:
                return False

    server_country = get_country(ip)

    if MC_COUNTRY:
        if MC_COUNTRY == server_country:
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
    else:
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

def get_ping(ip, port):
    try:
        server = JavaServer.lookup(f'{ip}:{port}')
        latency = int(server.ping())
        return latency
    except:
        logger.warning('get_ping() --> Erreur')
        return False

def get_country(ip):
    url = f'http://ip-api.com/json/{ip}'
    req = requests.get(url)
    res = json.loads(req.text)

    if res['status'] == 'success':
        return res['countryCode'].lower()
    else:
        logger.warning('get_country() --> Pays non récupéré')
        return None

def send_discord(mc_stats):
    webhook = DiscordWebhook(url=DS_WEBHOOK, username=DS_BOT_NAME)

    mc_srv_software = mc_stats['version']['name_clean']
    mc_srv_ip = mc_stats['host']
    mc_srv_port = mc_stats['port']
    mc_srv_players_list = mc_stats['players']['list']
    mc_srv_plugins = mc_stats['plugins']
    mc_srv_mods = mc_stats['mods']

    blacklisted = False

    if os.path.exists('blacklist.json'):
        with open('blacklist.json', 'r') as bf:
            blacklist = json.load(bf)
        
        if any(mod in blacklist for mod in mc_srv_mods):
            blacklisted = True

    if not blacklisted:
        try:
            if MC_EDITION:
                loader.loadandrun(serverip=f'{mc_srv_ip}:{mc_srv_port}', edition=MC_EDITION)
            else:
                loader.loadandrun(serverip=f'{mc_srv_ip}:{mc_srv_port}', edition=detected_mc_edition)

            with open("motd.png", "rb") as motd_file:
                webhook.add_file(file=motd_file.read(), filename='motd.png')
        except:
            if os.path.exists('motd.png'):
                os.remove('motd.png')

            with open("empty_motd.png", "rb") as empty_motd_file:
                webhook.add_file(file=empty_motd_file.read(), filename='empty_motd.png')

            logger.warning('send_discord() --> MOTD non récupéré')

        country = get_country(mc_srv_ip)

        if country:
            embed = DiscordEmbed(title=f":flag_{country}: Serveur trouvé !", description="Un serveur a été trouvé", color=DS_WEBHOOK_COLOR)
        else:
            embed = DiscordEmbed(title="Serveur trouvé !", description="Un serveur a été trouvé", color=DS_WEBHOOK_COLOR)

        if MC_VERSION:
            if MC_EDITION:
                embed.add_embed_field(name='Édition de Minecraft', value=f'```{MC_EDITION}```', inline=True)
            else:
                embed.add_embed_field(name='Édition de Minecraft', value=f'```{detected_mc_edition}```', inline=True)

            embed.add_embed_field(name='Version', value=f'```{MC_VERSION}```', inline=True)
        else:
            if MC_EDITION:
                embed.add_embed_field(name='Édition de Minecraft', value=f'```{MC_EDITION}```', inline=True)
            else:
                embed.add_embed_field(name='Édition de Minecraft', value=f'```{detected_mc_edition}```', inline=True)

        embed.add_embed_field(name='IP', value=f'```{mc_srv_ip}```', inline=True)
        embed.add_embed_field(name='PORT', value=f'```{mc_srv_port}```', inline=True)

        mc_srv_ping = get_ping(mc_srv_ip, mc_srv_port)

        if mc_srv_ping:
            embed.add_embed_field(name='Ping', value=f'```{mc_srv_ping} ms```', inline=False)

        embed.add_embed_field(name='Logiciel détécté', value=f'```{mc_srv_software}```', inline=False)

        if mc_srv_plugins:
            embed.add_embed_field(name='Plugin(s) détécté(s)', value=f'```{mc_srv_plugins}```', inline=False)
        elif mc_srv_mods:
            embed.add_embed_field(name='Mod(s) détécté(s)', value=f'```{mc_srv_mods}```', inline=False)

        if mc_srv_players_list:
            clean_players_list = []

            for player in mc_srv_players_list:
                clean_players_list.append(player['name_clean'])

            embed.add_embed_field(name='Liste des joueurs', value=f'```{clean_players_list}```', inline=False)
            webhook.content = '@everyone'

        if os.path.exists('motd.png'):
            embed.set_image(url='attachment://motd.png')
        else:
            embed.set_image(url='attachment://empty_motd.png')

        webhook.add_embed(embed)
        webhook.execute()
    else:
        logging.info('Serveur blacklisté')

# -------------------------------------------------------------
# Boucler sur les IP triés
# -------------------------------------------------------------

try:
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

    if not isinstance(valid_servers_data, dict):
        valid_servers_data = {}

    with open('invalid_servers.json', 'r') as vsf:
        invalid_servers_data = json.load(vsf)

    if not isinstance(invalid_servers_data, dict):
        invalid_servers_data = {}

    for t_ip in ips:
        t_ip = t_ip.strip()
        port_key = str(PORT)

        if port_key not in valid_servers_data:
            valid_servers_data[port_key] = []
        if port_key not in invalid_servers_data:
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

    logger.info('SCAN TERMINÉ !')
    print('SCAN TERMINÉ !')
except Exception as e:
    logger.error(f'Erreur lors du bouclage sur les IP : {e}')
    print('Un problème est survenu. Regarder les logs pour plus de détails.')

# -------------------------------------------------------------
# Néttoyage des fichiers
# -------------------------------------------------------------

try:
    if os.path.exists('motd.png'):
        os.remove('motd.png')
    if os.path.exists(MASSCAN_SORTED_FILE):
        os.remove(MASSCAN_SORTED_FILE)

    logger.info('Fichiers néttoyés')
    print('Fichiers néttoyés')
except Exception as e:
    logger.error(f'Erreur lors du néttoyage des fichiers : {e}')
    print('Un problème est survenu. Regarder les logs pour plus de détails.')