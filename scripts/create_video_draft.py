"""Create a narrated evidence walkthrough; not a continuous live screen capture.

Windows requires System.Speech; Python requires Pillow, pypdfium2 and
imageio-ffmpeg. The video uses the real saved dashboard and PDF, with explicit
synthetic narration/screenshot labels. No team member is impersonated.
"""
from pathlib import Path
import json
import os
import subprocess
import textwrap
import wave
import argparse
from PIL import Image, ImageDraw, ImageFont
import pypdfium2
import imageio_ffmpeg

ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser();parser.add_argument('--extended',action='store_true');args=parser.parse_args()
TMP=ROOT/('tmp/video-extended' if args.extended else 'tmp/video')
TMP.mkdir(parents=True,exist_ok=True)
FFMPEG=imageio_ffmpeg.get_ffmpeg_exe()
scenes=json.loads((ROOT/('submission/implementation-scenes.json' if args.extended else 'submission/video-scenes.json')).read_text())
font_path=Path('C:/Windows/Fonts/segoeui.ttf')
bold_path=Path('C:/Windows/Fonts/segoeuib.ttf')
SCALE=1.5
def font(size,bold=False):return ImageFont.truetype(str(bold_path if bold else font_path),round(size*SCALE))
pdf=pypdfium2.PdfDocument(str(ROOT/'submission/RASCALS-ContinuityGuard-Pitch.pdf'))
dashboard=Image.open(ROOT/'evidence/dashboard.png').convert('RGB')
records=[]
for index,(title,narration,source) in enumerate(scenes):
    text_file=TMP/f'{index}.txt';text_file.write_text(narration,encoding='utf-8')
    wav=TMP/f'{index}.wav'
    # Paths are passed through environment variables, never interpolated as code.
    env=dict(os.environ,CG_NARRATION=str(text_file),CG_WAV=str(wav))
    ps="$ErrorActionPreference='Stop'; Add-Type -AssemblyName System.Speech; $s=New-Object System.Speech.Synthesis.SpeechSynthesizer; $s.Rate=1; $s.SetOutputToWaveFile($env:CG_WAV); $s.Speak([IO.File]::ReadAllText($env:CG_NARRATION)); $s.Dispose()"
    subprocess.run(['pwsh','-NoProfile','-Command',ps],env=env,check=True)
    with wave.open(str(wav)) as audio: duration=audio.getnframes()/audio.getframerate()+1.5
    frame=Image.new('RGB',(1920,1080),'#f6f8f2');draw=ImageDraw.Draw(frame)
    draw.text((54,25),'RASCALS / CONTINUITYGUARD',font=font(17,True),fill='#187563')
    draw.text((54,73),title,font=font(29,True),fill='#183f34')
    if source[0]=='pdf': asset=pdf[source[1]].render(scale=2.2).to_pil().convert('RGB')
    elif source[0]=='image':asset=Image.open(ROOT/source[1]).convert('RGB')
    elif source[0]=='code':
        asset=Image.new('RGB',(1785,637),'#173e34');d=ImageDraw.Draw(asset)
        for y,line in enumerate(source[1].splitlines()):d.text((30,25+y*45),line,font=font(23),fill='#f5f8ee')
    else:asset=dashboard.crop(source[1])
    # thumbnail never enlarges low-resolution screenshots.
    asset.thumbnail((1785,637),Image.Resampling.LANCZOS)
    frame.paste(asset,((1920-asset.width)//2,144+(637-asset.height)//2))
    draw.line((54,810,1866,810),fill='#d7e1d4',width=2)
    lines=textwrap.wrap(narration,width=112)
    assert len(lines)<=6,'Narration caption exceeds frame capacity'
    step,size=(32,18) if len(lines)>5 else (37,21)
    for y,line in enumerate(lines):draw.text((54,826+y*step),line,font=font(size),fill='#183f34')
    draw.text((54,1036),'Chaptered evidence walkthrough | Synthetic narration | Data provenance labeled | AI assistance disclosed',font=font(14),fill='#657c70')
    png=TMP/f'{index}.png'; frame.save(png)
    clip=TMP/f'{index}.mp4'
    subprocess.run([FFMPEG,'-y','-loglevel','error','-loop','1','-i',str(png),'-i',str(wav),'-t',str(duration),'-vf','fps=15,format=yuv420p','-c:v','libx264','-preset','fast','-crf','18','-c:a','aac','-b:a','128k','-af','apad',str(clip)],check=True)
    records.append({'scene':index+1,'title':title,'seconds':round(duration,2),'narration':narration})
    print('Created scene',index+1,round(duration,2),flush=True)
concat=TMP/'clips.txt'
concat.write_text(''.join("file '"+str(TMP/f'{i}.mp4').replace('\\','/')+"'\n" for i in range(len(scenes))))
out=ROOT/('submission/RASCALS-Implementation-Guide.mp4' if args.extended else 'submission/RASCALS-ContinuityGuard-Walkthrough.mp4')
subprocess.run([FFMPEG,'-y','-loglevel','error','-f','concat','-safe','0','-i',str(concat),'-c','copy','-movflags','+faststart',str(out)],check=True)
total=sum(r['seconds'] for r in records)
assert total<(900 if args.extended else 180),f'Video exceeds its limit: {total}'
(ROOT/('submission/implementation-video-manifest.json' if args.extended else 'submission/video-manifest.json')).write_text(json.dumps({'duration_seconds':round(total,2),'model_version':json.loads((ROOT/'artifacts/manifest.json').read_text())['version'],'resolution':'1920x1080','format':'H.264/AAC MP4','presentation':'Chaptered implementation/evidence guide, not continuous live screen recording','voice':'Windows System.Speech synthetic narration; no person impersonated','scenes':records},indent=2))
print(out,total,out.stat().st_size)
