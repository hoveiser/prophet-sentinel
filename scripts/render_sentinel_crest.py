"""Render the original geometric Sentinel crest at 512 by 512 pixels."""
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]


def render():
    scale = 3
    im = Image.new("RGB", (512*scale, 512*scale), "#08070c")
    d = ImageDraw.Draw(im)
    def ring(box, color, width):
        d.ellipse(tuple(x*scale for x in box), outline=color, width=width*scale)
    ring((48,48,464,464), "#392941", 2)
    ring((86,86,426,426), "#69512e", 2)
    ring((118,118,394,394), "#58398b", 2)
    d.line([(256*scale,24*scale),(256*scale,488*scale)], fill="#23192f",width=scale)
    d.line([(24*scale,256*scale),(488*scale,256*scale)], fill="#23192f",width=scale)
    shield = [(256,110),(359,169),(345,315),(256,405),(167,315),(153,169),(256,110)]
    d.polygon([(x*scale,y*scale) for x,y in shield], fill="#15101e")
    d.line([(x*scale,y*scale) for x,y in shield], fill="#f59e0b", width=7*scale, joint="curve")
    d.line([(190*scale,290*scale),(224*scale,220*scale),(258*scale,268*scale),(310*scale,192*scale)],fill="#b899ee",width=13*scale,joint="curve")
    for x,y in [(190,290),(224,220),(258,268),(310,192)]:
        d.ellipse(((x-7)*scale,(y-7)*scale,(x+7)*scale,(y+7)*scale),fill="#fbc463")
    for x,y,c in [(108,128,"#10b981"),(431,244,"#f59e0b"),(135,416,"#8b5cf6")]:
        d.ellipse(((x-6)*scale,(y-6)*scale,(x+6)*scale,(y+6)*scale),fill=c)
    im = im.resize((512,512), Image.Resampling.LANCZOS)
    for folder in (ROOT/"docs", ROOT/"frontend/public"):
        folder.mkdir(parents=True,exist_ok=True)
        target = folder/"logo.png"
        im.save(target,optimize=True)
        assert target.stat().st_size < 500000
        print(target.relative_to(ROOT), target.stat().st_size, "bytes")


if __name__ == "__main__":
    render()
