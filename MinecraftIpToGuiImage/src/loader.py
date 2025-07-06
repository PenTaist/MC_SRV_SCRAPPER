from PIL import Image
from MinecraftIpToGuiImage.src import motdtoimage
import requests
import json
import base64
import io

def loadandrun(servername='Serveur', serverip="", edition='java'):
    if serverip == "":
        raise Exception("No IP address detected")

    url = f"https://api.mcstatus.io/v2/status/{edition}/{serverip}"
    r = requests.get(url)
    r = r.json()

    icon_base64 = r.get('icon')
    if icon_base64:
        base64_data = icon_base64.split(',')[1]
        icon_bytes = base64.b64decode(base64_data)
        logo = Image.open(io.BytesIO(icon_bytes))
    else:
        logo = Image.new('RGBA', (64, 64), (0, 0, 0, 0))

    html = r['motd']['html']
    onlineplayers = str(r['players']['online'])
    playerstotal = str(r['players']['max'])

    motdtoimage.getmotdtoimg(html, logo, (onlineplayers, playerstotal), servername)
