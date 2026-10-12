#!/usr/bin/env python3
"""Add a randomly selected background track to videos using FFmpeg."""
from pathlib import Path
import json, random, shutil, subprocess, sys

ROOT = Path(__file__).resolve().parent
INPUTS, BGM, OUTPUTS = ROOT / 'inputs', ROOT / 'bgm', ROOT / 'outputs'
VIDEO_EXTS = {'.mp4', '.mov', '.mkv', '.m4v', '.avi', '.webm'}
AUDIO_EXTS = {'.mp3', '.wav', '.m4a', '.aac', '.flac', '.ogg', '.opus'}
FADE_SECONDS = 1.8

def probe(path):
    p = subprocess.run(['ffprobe','-v','error','-show_entries','format=duration:stream=codec_type,duration','-of','json',str(path)], capture_output=True, text=True)
    if p.returncode: raise RuntimeError(p.stderr.strip() or f'ffprobe failed on {path.name}')
    data=json.loads(p.stdout); duration=float(data.get('format',{}).get('duration') or 0)
    if duration <= 0: duration=max((float(s.get('duration') or 0) for s in data.get('streams',[])),default=0)
    return duration, any(s.get('codec_type')=='audio' for s in data.get('streams',[]))

def main():
    for exe in ('ffmpeg','ffprobe'):
        if not shutil.which(exe): raise RuntimeError(f'{exe} not found on PATH. Install FFmpeg and reopen the terminal.')
    videos=sorted(p for p in INPUTS.glob('*') if p.is_file() and p.suffix.lower() in VIDEO_EXTS) if INPUTS.is_dir() else []
    if not videos: videos=sorted(p for p in ROOT.glob('*') if p.is_file() and p.suffix.lower() in VIDEO_EXTS)
    if not videos: print('No videos found. Put files in inputs/ or beside this script.'); return 0
    tracks=sorted(p for p in BGM.glob('*') if p.is_file() and p.suffix.lower() in AUDIO_EXTS) if BGM.is_dir() else []
    if not tracks: print('No audio tracks found in bgm/.'); return 1
    OUTPUTS.mkdir(exist_ok=True)
    failures=0
    for video in videos:
        try:
            duration, has_audio=probe(video); track=random.choice(tracks)
            if duration <= 0: raise RuntimeError('Could not determine a positive video duration')
            fade=max(0.0,duration-FADE_SECONDS)
            # Loop short music; trim every BGM track to match video and fade smoothly.
            af=f"aloop=loop=-1:size=2e+09,atrim=duration={duration:.6f},asetpts=PTS-STARTPTS,afade=t=out:st={fade:.6f}:d={min(FADE_SECONDS,duration):.6f},volume=0.22"
            out=OUTPUTS / f'{video.stem}_audio.mp4'
            cmd=['ffmpeg','-hide_banner','-loglevel','error','-y','-i',str(video),'-stream_loop','-1','-i',str(track)]
            if has_audio:
                cmd += ['-filter_complex',f'[1:a]{af}[bg];[0:a][bg]amix=inputs=2:duration=first:dropout_transition=0[aout]','-map','0:v:0','-map','[aout]']
            else:
                cmd += ['-filter_complex',f'[1:a]{af}[aout]','-map','0:v:0','-map','[aout]']
            cmd += ['-c:v','copy','-c:a','aac','-b:a','192k','-movflags','+faststart','-shortest',str(out)]
            run=subprocess.run(cmd,capture_output=True,text=True)
            if run.returncode: raise RuntimeError(run.stderr.strip()[-1600:])
            print(f'Created: {out.relative_to(ROOT)} (music: {track.name})')
        except Exception as e:
            failures+=1; print(f'ERROR {video.name}: {e}',file=sys.stderr)
    print(f'Finished. {len(videos)-failures}/{len(videos)} succeeded. Outputs: {OUTPUTS}')
    return 1 if failures else 0
if __name__=='__main__':
    try: sys.exit(main())
    except Exception as exc: print(f'ERROR: {exc}',file=sys.stderr); sys.exit(1)