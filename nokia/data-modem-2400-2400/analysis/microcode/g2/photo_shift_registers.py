"""Extract the four visible CD4094BE markings from the DSU3556 front photo."""

import hashlib
from pathlib import Path

from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
PHOTO = HERE.parents[2] / 'photos/PXL_20261123_114723348.jpg'
EXPECTED_SHA256 = '27f26c102d280c86e2745a687a3b934dedcbbdf13cdc5ede565172f05da5a28d'
BOXES = (
    (1300, 700, 1500, 1100),
    (1050, 2000, 1250, 2400),
    (1700, 2600, 1900, 3000),
    (1700, 3050, 1900, 3450),
)
OUT = HERE / 'results/dsu3556-cd4094.jpg'


def run(out=OUT):
    if hashlib.sha256(PHOTO.read_bytes()).hexdigest() != EXPECTED_SHA256:
        raise ValueError('DSU3556 photo hash changed')
    source = Image.open(PHOTO)
    if source.size != (3072, 4080):
        raise ValueError('DSU3556 photo dimensions changed')
    sheet = Image.new('RGB', (1600, 260), 'white')
    labels = ImageDraw.Draw(sheet)
    for index, box in enumerate(BOXES):
        labels.text((index * 400 + 8, 8),
                    f'{index + 1}: x={box[0]}..{box[2]}, y={box[1]}..{box[3]}',
                    fill='black')
        sheet.paste(source.crop(box).rotate(90, expand=True),
                    (index * 400, 36))
    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out, quality=95)
    return out


if __name__ == '__main__':
    print(run())
