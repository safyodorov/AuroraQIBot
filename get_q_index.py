from PIL import Image
from get_image import getImage

# функция возвращает значение Q-индекса
def getQ():
    getImage()

    im = Image.open('Q-index.png')
    im.LOAD_TRUNCATED_IMAGES = True
    # шаг на графике 14 пикселей
    # определяем значение Q-индекса
    # координаты пикселя, если Q = 1
    x = 577.5
    y = 142
    # шаг на графике
    delta = 14

    Q = 0
    while Q <= 9:
        r, g, b = im.getpixel((x, y))
        sum = r+g+b
        if sum > 649:
            break
        else:
            y -= delta
            Q += 1
    return Q
