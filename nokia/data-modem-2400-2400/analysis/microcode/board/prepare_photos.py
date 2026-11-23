"""Reproducible documentary views; Pillow required only for this utility.

Manually chosen PCB corners align board orientation/extent approximately.
These are visual tracing aids, not a metrology-grade registered overlay.
"""
import hashlib
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageOps

HERE=Path(__file__).resolve().parent
PHOTOS=HERE.parents[2]/'photos'
OUT=HERE/'evidence'
SIZE=(2000,1000)
CORNERS={
 'front':[(.062,.158),(.074,.77),(.957,.765),(.959,.146)],
 'back':[(.045,.19),(.023,.792),(.93,.804),(.925,.204)],
}
FILES={'front':'PXL_20261123_114926601.jpg','back':'PXL_20261123_114932814.jpg'}


def main():
    OUT.mkdir(exist_ok=True)
    inventory=json.loads((HERE/'inventory.json').read_text())
    try:font=ImageFont.truetype('/System/Library/Fonts/Monaco.ttf',16)
    except OSError:font=ImageFont.load_default()
    manifest={'purpose':'approximate orientation/extent alignment; never proof of electrical continuity','views':{}}
    for side,name in FILES.items():
        source=PHOTOS/name
        im=Image.open(source)
        im=im.transpose(Image.Transpose.ROTATE_270) if side=='front' else ImageOps.flip(im)
        quad=tuple(v for x,y in CORNERS[side] for v in (x*im.width,y*im.height))
        rect=im.transform(SIZE,Image.Transform.QUAD,quad,resample=Image.Resampling.BICUBIC)
        rect.save(OUT/f'{side}-rectified.jpg',quality=94)
        draw=ImageDraw.Draw(rect)
        for part in inventory['parts']:
            x,y=part['center']; x*=SIZE[0]; y*=SIZE[1]
            color='#ffb000' if part['status']=='unresolved' else '#fff000'
            draw.ellipse((x-5,y-5,x+5,y+5),outline=color,width=2)
            label=part['ref']+' '+part['marking'] if side=='front' else part['ref']+' approx.'
            if len(label)>20:label=label[:19]+'…'
            box=draw.textbbox((x-40,y-38),label,font=font)
            draw.rectangle(box,fill='black');draw.text((x-40,y-38),label,font=font,fill=color)
        if side=='front':
            nets=json.loads((HERE/'nets.json').read_text())
            for fragment in nets.get('trace_fragments',[]):
                points=[tuple(x) for x in fragment['polyline_pixels']]
                draw.line(points,fill='#00ffff',width=3)
                x,y=points[-1];draw.ellipse((x-6,y-6,x+6,y+6),outline='#00ffff',width=2)
                draw.text((x+10,y-18),fragment['id']+' endpoint unresolved',font=font,fill='#00ffff',stroke_width=1,stroke_fill='black')
        draw.text((8,965),'Approximate locations. Yellow: identified; amber: unresolved. No pin numbers inferred.',font=font,fill='white',stroke_width=2,stroke_fill='black')
        rect.save(OUT/f'{side}-annotated.jpg',quality=94)
        manifest['views'][side]={'source':str(source.relative_to(HERE.parents[2])),
            'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
            'orientation':'rotate clockwise 90 degrees' if side=='front' else 'flip vertically',
            'quadrilateral_normalized_UL_LL_LR_UR':CORNERS[side],'output_size':SIZE}
    (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')


if __name__=='__main__':main()
