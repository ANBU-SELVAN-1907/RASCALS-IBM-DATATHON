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
from PIL import Image, ImageDraw, ImageFont
import pypdfium2
import imageio_ffmpeg

ROOT=Path(__file__).resolve().parents[1]
TMP=ROOT/'tmp/video'
TMP.mkdir(parents=True,exist_ok=True)
FFMPEG=imageio_ffmpeg.get_ffmpeg_exe()
scenes=[
('Protect time-critical digital services', 'We are RASCALS. ContinuityGuard detects developing failures in hospital digital-service infrastructure. A shared database bottleneck can disrupt several dependent services. We give operators earlier warning, measured evidence and an inspectable next step. This walkthrough uses actual saved application screenshots and synthetic narration. All telemetry is simulated.', ('pdf',0)),
('Prediction stays on LinuxONE', 'Training and testing executed through Jupyter on IBM LinuxONE, using native s390x Python. A calibrated boosted-tree model forecasts a service-objective breach within sixty seconds. Isolation Forest separately reports novelty. A bounded queue, causal rolling features and persistent incident policy connect incoming telemetry to operator decisions.', ('pdf',2)),
('Watch a developing dependency fault', 'This screenshot comes from the deployed application after a controlled database-pressure replay. Four software services share a database dependency. Forecast scores, latency and service state update as events arrive. The dashboard distinguishes simulated service measurements from observed host resources. A persistent warning creates an evidence-linked incident.', ('shot',(220,90,1250,825))),
('Review evidence before choosing a response', 'The selected incident retains the measurements at warning time. It links connection-pool occupancy, memory and latency to a declared runbook and affected software services. The suspected database source is a heuristic hypothesis, not proof of causality. Operators can inspect the evidence before deciding what to investigate.', ('shot',(870,475,1235,1030))),
('Explain and preview, with explicit tradeoffs', 'Local IBM Granite generated the displayed constrained explanation on LinuxONE. It took twenty-two seconds and cited verified evidence and a runbook. A paired sandbox preview compared deferring optional batch work with taking no action under the same workload. These benefits follow simulator assumptions; no real system was modified.', ('shot',(870,1025,1235,1390))),
('Measure the gain and the cost', 'On sixty final synthetic runs, ContinuityGuard warned before forty-three of forty-seven service incidents. Median early lead was thirty-seven seconds, versus nine for static thresholds. Precision was lower: sixty-one point four percent versus sixty-eight point three. Both missed four incidents. These results are not hospital production validation.', ('pdf',4)),
('Reproducible, inspectable, ready for review', 'Twenty correctness tests passed in Jupyter. Deployment evidence records a non-root container, resource limits and a read-only filesystem. The repository includes code, executed notebooks, model hashes, both runtime measurements and documented limits. Our next step is authorized real telemetry and operator feedback. RASCALS presents ContinuityGuard: useful warning time with accountable decisions.', ('pdf',6)),
]
font_path=Path('C:/Windows/Fonts/segoeui.ttf')
bold_path=Path('C:/Windows/Fonts/segoeuib.ttf')
def font(size,bold=False):return ImageFont.truetype(str(bold_path if bold else font_path),size)
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
    frame=Image.new('RGB',(1280,720),'#f6f8f2');draw=ImageDraw.Draw(frame)
    draw.text((36,17),'RASCALS / CONTINUITYGUARD',font=font(17,True),fill='#187563')
    draw.text((36,49),title,font=font(29,True),fill='#183f34')
    if source[0]=='pdf': asset=pdf[source[1]].render(scale=1.5).to_pil().convert('RGB')
    else:asset=dashboard.crop(source[1])
    asset.thumbnail((1190,425),Image.Resampling.LANCZOS)
    frame.paste(asset,((1280-asset.width)//2,96+(425-asset.height)//2))
    draw.line((36,540,1244,540),fill='#d7e1d4',width=2)
    lines=textwrap.wrap(narration,width=112)
    for y,line in enumerate(lines):draw.text((36,551+y*25),line,font=font(21),fill='#183f34')
    draw.text((36,691),'Recorded evidence walkthrough | Synthetic narration and telemetry | AI assistance disclosed',font=font(14),fill='#657c70')
    png=TMP/f'{index}.png'; frame.save(png)
    clip=TMP/f'{index}.mp4'
    subprocess.run([FFMPEG,'-y','-loglevel','error','-loop','1','-i',str(png),'-i',str(wav),'-t',str(duration),'-vf','fps=15,format=yuv420p','-c:v','libx264','-preset','fast','-crf','24','-c:a','aac','-b:a','96k','-af','apad',str(clip)],check=True)
    records.append({'scene':index+1,'title':title,'seconds':round(duration,2),'narration':narration})
    print('Created scene',index+1,round(duration,2),flush=True)
concat=TMP/'clips.txt'
concat.write_text(''.join("file '"+str(TMP/f'{i}.mp4').replace('\\','/')+"'\n" for i in range(len(scenes))))
out=ROOT/'submission/RASCALS-ContinuityGuard-Walkthrough.mp4'
subprocess.run([FFMPEG,'-y','-loglevel','error','-f','concat','-safe','0','-i',str(concat),'-c','copy','-movflags','+faststart',str(out)],check=True)
total=sum(r['seconds'] for r in records)
assert total<180, f'Video exceeds three minutes: {total}'
(ROOT/'submission/video-manifest.json').write_text(json.dumps({'duration_seconds':round(total,2),'resolution':'1280x720','format':'H.264/AAC MP4','presentation':'Saved-evidence walkthrough, not continuous live capture','voice':'Microsoft Zira synthetic narration; no person impersonated','scenes':records},indent=2))
print(out,total,out.stat().st_size)
