import requests
from PIL import Image

# функция парсит картинку, сохраняет её, обрезает и сохраняет снова под тем же именем
def getImage():
    url = 'https://www2.irf.se/maggraphs/preliminary_k_index_last_24.png'
    # запись файла на диск
    filename = 'Q-index.png'
    r = requests.get(url, allow_redirects=True)
    open(filename, 'wb').write(r.content)
    im = Image.open('Q-index.png')
    im.LOAD_TRUNCATED_IMAGES = True
    im.crop((608, 8, 1206, 306)).save('Q-index.png')