"""Create a captioned 40-second edited UI walkthrough from real app captures.

Optional dependencies: Pillow and imageio-ffmpeg. No browser automation here.
The output is an edited still-capture walkthrough, not a continuous recording.
"""
import argparse
from pathlib import Path
import shutil
import subprocess
import sys
import textwrap

ROOT=Path(__file__).resolve().parents[1]
ART=ROOT/'artifacts'
REPO='https://github.com/preethamvooturi003/signal-and-starts'


def main(repo=REPO):
    from PIL import Image,ImageDraw,ImageFont
    try:
        import imageio_ffmpeg
    except ImportError:
        # Checkout-local helper used in the initial build; not committed.
        sys.path.insert(0,str(ROOT/'.local'/'media'))
        import imageio_ffmpeg
    ffmpeg=shutil.which('ffmpeg') or imageio_ffmpeg.get_ffmpeg_exe()
    frames=ART/'frames';frames.mkdir(parents=True,exist_ok=True)
    fonts=[Path('C:/Windows/Fonts/segoeui.ttf'),Path('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf')]
    font_path=next((p for p in fonts if p.exists()),None)
    if font_path is None:raise RuntimeError('Install a TrueType font and update fonts in scripts/make_video.py')
    font=lambda size:ImageFont.truetype(str(font_path),size)
    w,h=1920,1080
    def base():
        image=Image.new('RGB',(w,h),'#102f37');draw=ImageDraw.Draw(image)
        draw.rounded_rectangle((56,31,351,76),radius=10,fill='#244a4d')
        draw.text((74,40),'Demo · Synthetic data',font=font(22),fill='#d5e9df')
        draw.text((1188,42),'Offline evidence assistant · actual app captures',font=font(20),fill='#9bbab5')
        return image,draw
    def screen(name,caption):
        image,draw=base();source=Image.open(ART/name).convert('RGB')
        source.thumbnail((1808,810),Image.Resampling.LANCZOS)
        image.paste(source,((w-source.width)//2,100+(810-source.height)//2))
        draw.rectangle((0,935,w,h),fill='#0b242b')
        lines=caption.split('\n')
        for i,line in enumerate(lines):
            box=draw.textbbox((0,0),line,font=font(31));draw.text(((w-box[2])/2,963+i*44),line,font=font(31),fill='#eff7f1')
        return image
    intro,draw=base()
    draw.text((150,223),'SIGNAL & STARTS',font=font(28),fill='#8ec6b1')
    draw.text((145,310),'More engagement.',font=font(91),fill='#f1f6ef')
    draw.text((145,420),'Starts still below plan.',font=font(91),fill='#f1f6ef')
    draw.text((150,596),'What changed underneath?',font=font(47),fill='#a5cdbb')
    draw.text((150,829),'A fictional pharmaceutical commercial investigation',font=font(26),fill='#9bbab5')
    outro,draw=base()
    draw.text((150,235),'From a performance gap',font=font(77),fill='#f1f6ef')
    draw.text((150,340),'to a testable next question.',font=font(77),fill='#f1f6ef')
    draw.text((153,515),'Preetham Vooturi',font=font(43),fill='#b1d5bd')
    draw.text((153,580),'Business analysis · Data modeling · Evidence-led AI workflows',font=font(29),fill='#9bbab5')
    for i,line in enumerate(textwrap.wrap(repo,76)):
        draw.text((153,737+i*39),line,font=font(29),fill='#e0eee4')
    draw.text((153,906),'Independent portfolio · No patient or employer data · No causal claim',font=font(24),fill='#8aa9a3')
    scenes=[(intro,5),(screen('nordhaven.jpg','Nordhaven: 217 starts vs 340 targeted.\nEngagement is up 38.1% year on year.'),5),
      (screen('investigation.jpg','Investigate the gap.\nEvery finding links back to its evidence.'),5),
      (screen('investigation.jpg','Incoming switches account for 71.5%\nof the arithmetic shortfall.'),6),
      (screen('evidence.jpg','89.8% of contacts reach the top quarter of HCPs.\nReported process delays remain a hypothesis.'),6),
      (screen('followup.jpg','What should we investigate next?\nAudit reach. Validate delays. Test before scaling activity.'),8),(outro,5)]
    concat=[]
    for i,(frame,duration) in enumerate(scenes):
        png=frames/f'{i:02d}.png';frame.save(png)
        concat.append(f"file '{png.as_posix()}'\nduration {duration}\n")
    concat.append(f"file '{(frames/'06.png').as_posix()}'\n")
    manifest=frames/'concat.txt';manifest.write_text(''.join(concat),encoding='utf-8')
    output=ART/'signal-and-starts-demo.mp4'
    subprocess.run([ffmpeg,'-y','-v','warning','-f','concat','-safe','0','-i',str(manifest),'-t','40','-r','30','-c:v','libx264','-preset','medium','-crf','19','-pix_fmt','yuv420p','-movflags','+faststart',str(output)],check=True)
    check=subprocess.run([ffmpeg,'-hide_banner','-i',str(output)],capture_output=True,text=True)
    print(check.stderr)
    print(f'Created {output} ({output.stat().st_size/1e6:.1f} MB). Silent, burned-in captions, 40 seconds.')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--repo-url',default=REPO);args=parser.parse_args();main(args.repo_url)
