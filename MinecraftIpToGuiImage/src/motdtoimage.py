from bs4 import BeautifulSoup
import bs4
import re
from MinecraftIpToGuiImage.src import styleandtextretriver
from MinecraftIpToGuiImage.src import toimage

def getmotdtoimg(html, icon, players, servername=None):
    # Si html est une chaîne, on en fait une liste d’une seule ligne pour compatibilité
    if isinstance(html, str):
        html = [html]

    for i in range(0, len(html)):
        html[i] = html[i].replace("\\/", "/")
        html[i] = html[i].replace(";", "")
        html[i] = re.sub(r"( )\1+", lambda m: "⛟" * (m.end() - m.start()), html[i])

    alltextandstyles = []

    for i in range(0, len(html)):
        alltextandstyles.append([])
        soup = BeautifulSoup(html[i], 'html.parser')
        all_elements = list(soup.children)

        for x in all_elements:
            if isinstance(x, bs4.element.NavigableString):
                alltextandstyles[i].append({
                    'text': str(x),
                    'styles': {
                        "color": None,
                        "font-weight": None,
                        "font-style": None,
                        "text-decoration": None
                    }
                })
            else:
                stuff = styleandtextretriver.get_as_list(x)
                alltextandstyles[i].extend(stuff)

    for x in alltextandstyles:
        for y in x:
            y['text'] = y['text'].replace("⛟", " ")

    toimage.toImage(alltextandstyles, icon, players, servername)