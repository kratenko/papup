# from https://note.nkmk.me/en/python-pyzbar-barcode-qrcode/

from PIL import Image, ImageDraw, ImageFont
from pyzbar.pyzbar import decode

img = Image.open('qrdings.jpg')

draw = ImageDraw.Draw(img)
font = ImageFont.truetype('Arial.ttf', size=20)  # Set 'arial.ttf' for Windows

for d in decode(img):
    draw.rectangle(((d.rect.left, d.rect.top), (d.rect.left + d.rect.width, d.rect.top + d.rect.height)),
                   outline=(0, 0, 255), width=3)
    draw.polygon(d.polygon, outline=(0, 255, 0), width=3)
    draw.text((d.rect.left, d.rect.top + d.rect.height), d.data.decode(),
              (255, 0, 0), font=font)

img.save('qrdingsdings.jpg')
