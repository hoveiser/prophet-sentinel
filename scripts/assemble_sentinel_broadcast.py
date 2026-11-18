"""Render a truthful 50-second local preview with original ambient audio."""
from pathlib import Path
import json
import math
import shutil
import subprocess
import wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageOps

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT/".cache"
FPS, SECONDS = 24, 50
W, H = 1280, 720
BG, AMBER, VIOLET = "#08070c", "#f59e0b", "#8b5cf6"
CAPTIONS = [
    "ProphetSentinel connects source verification, forecasting, and realized calibration.",
    "The observatory distinguishes actual contract state from an unverified deployment.",
    "Source authenticity routes signals. True Brier accuracy waits for the resolved outcome.",
    "Sentinel native rewards and ProphetGrid PGT returns are separate asset ledgers.",
    "This is a local development preview. Live transactions and release verification remain open.",
]


def text(draw, position, value, size=24, color="#ede7f5"):
    draw.text(position, value, font=ImageFont.load_default(size=size), fill=color)


def audio():
    rate = 44100
    t = np.arange(rate*SECONDS)/rate
    fade = np.minimum(np.minimum(t/3,(SECONDS-t)/3),1)
    pad = .035*np.sin(2*np.pi*82.41*t)+.018*np.sin(2*np.pi*123.47*t)+.012*np.sin(2*np.pi*164.81*t)
    phase = t % 4
    ping = .035*np.sin(2*np.pi*659.25*t)*np.exp(-phase*7)
    left = np.clip((pad*(.8+.2*np.sin(2*np.pi*.13*t))+ping)*fade,-.2,.2)
    right = np.clip((pad*(.8+.2*np.cos(2*np.pi*.13*t))+ping*.9)*fade,-.2,.2)
    stereo = np.column_stack((left, right)).flatten()
    samples = (stereo*32767).astype('<i2')
    out = CACHE/"sentinel-ambient.wav"
    with wave.open(str(out),'wb') as f:
        f.setnchannels(2); f.setsampwidth(2); f.setframerate(rate); f.writeframes(samples.tobytes())
    return out


def scene(index):
    im = Image.new("RGB",(W,H),BG)
    d = ImageDraw.Draw(im)
    text(d,(48,30),"PROPHETSENTINEL",26,AMBER)
    text(d,(790,37),"LOCAL PREVIEW / NO LIVE TX EVIDENCE",16,"#c2abc9")
    d.line((48,80,1232,80),fill="#392740",width=1)
    if index == 0:
        crest = Image.open(ROOT/"docs/logo.png").resize((390,390))
        im.paste(crest,(805,145))
        text(d,(65,180),"Many forecasts.",54)
        text(d,(65,252),"One accountable signal.",45,"#bfa9d9")
        text(d,(68,350),"Primary-source verification",23)
        text(d,(68,397),"Quantized Brier calibration",23)
        text(d,(68,444),"Real cross-contract position accounting",23)
    elif index in (1,2):
        name = "observatory-desktop.png" if index == 1 else "observatory-calibration.png"
        screenshot = Image.open(CACHE/name).convert("RGB")
        shot = ImageOps.contain(screenshot,(1160,490),Image.Resampling.LANCZOS)
        im.paste(shot,((W-shot.width)//2,100))
    elif index == 3:
        for x,color,title,lines in [(65,AMBER,"SENTINEL NATIVE VAULT",["GEN-backed PFT accounting","Bounty + forecaster bonds","Soft-fail refundable credits"]),(675,VIOLET,"PROPHETGRID POSITION",["Outcome shares on the linked contract","Returns recorded as PGT","No native-GEN redemption claim"])]:
            d.rounded_rectangle((x,150,x+535,480),radius=15,outline=color,width=2,fill="#13111c")
            text(d,(x+26,185),title,25,color)
            for n,line in enumerate(lines): text(d,(x+26,260+n*65),line,22)
        text(d,(400,525),"SEPARATE CUSTODY. SEPARATE LIABILITIES.",22,"#cbb8db")
    else:
        text(d,(65,150),"Evidence before settlement.",46)
        for i,label in enumerate(["AUDIT","EMIT","CONFIRM","RECONCILE","SETTLE"]):
            x=65+i*238
            d.rounded_rectangle((x,260,x+215,370),radius=8,outline=VIOLET if i%2 else AMBER,width=2,fill="#13111c")
            text(d,(x+25,302),label,24)
        text(d,(65,430),"Pinned runner / Exact integer scoring / Explicit recovery paths",24)
        text(d,(65,480),"Release requires verified live execution and closed safety findings.",22,"#c5a9ce")
    d = ImageDraw.Draw(im)
    d.rectangle((35,615,1245,690),fill="#16101f")
    caption = CAPTIONS[index]
    font = ImageFont.load_default(size=22)
    if d.textlength(caption,font=font)>1160:
        font = ImageFont.load_default(size=20)
    d.text(((W-d.textlength(caption,font=font))/2,638),caption,font=font,fill="#eee7f5")
    return im


def main():
    CACHE.mkdir(exist_ok=True)
    for name in ("observatory-desktop.png","observatory-calibration.png"):
        if not (CACHE/name).is_file():
            raise RuntimeError("Run the browser checks to capture the local UI first")
    soundtrack = audio()
    output = ROOT/"docs/demo-video-subtitled.mp4"
    command = ["ffmpeg","-y","-loglevel","error","-f","rawvideo","-pix_fmt","rgb24","-s",f"{W}x{H}","-r",str(FPS),"-i","-","-i",str(soundtrack),"-c:v","libx264","-preset","fast","-crf","25","-pix_fmt","yuv420p","-c:a","aac","-b:a","96k","-ac","2","-movflags","+faststart","-t",str(SECONDS),str(output)]
    proc = subprocess.Popen(command,stdin=subprocess.PIPE)
    bases = [scene(i) for i in range(5)]
    for frame in range(FPS*SECONDS):
        im = bases[min(4,frame//(FPS*10))].copy()
        d = ImageDraw.Draw(im)
        d.rectangle((35,698,35+int(1210*(frame+1)/(FPS*SECONDS)),701),fill=AMBER)
        proc.stdin.write(im.tobytes())
    proc.stdin.close()
    if proc.wait() != 0:
        raise RuntimeError("Video encoding failed")
    report = json.loads(subprocess.check_output(["ffprobe","-v","error","-show_streams","-show_format","-of","json",str(output)]))
    video = next(s for s in report["streams"] if s["codec_type"]=="video")
    assert (video["width"],video["height"]) == (1280,720)
    assert 48 <= float(report["format"]["duration"]) <= 52
    assert output.stat().st_size < 15000000
    audio_stream = next(s for s in report["streams"] if s["codec_type"]=="audio")
    assert audio_stream["channels"] == 2
    shutil.copyfile(output,ROOT/"frontend/public/demo-video-subtitled.mp4")
    result = {"duration_seconds":float(report["format"]["duration"]),"width":1280,"height":720,"bytes":output.stat().st_size,"subtitles":"burned in","audio":"original synthesized ambient stereo","scope":"local preview, not live transaction evidence"}
    (ROOT/"evidence").mkdir(exist_ok=True)
    (ROOT/"evidence/media.json").write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result,indent=2))


if __name__ == "__main__":
    main()
