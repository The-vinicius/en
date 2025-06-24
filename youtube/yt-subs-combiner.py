#!/usr/bin/env python3
import yt_dlp
import argparse
import sys
import os
import re
import tempfile
from itertools import zip_longest
from datetime import datetime, timedelta
import subprocess
from webvtt import WebVTT
from combiner import combine_subtitles_vtt

def parse_vtt_to_segments(vtt_path):
    """
    Lê um arquivo .vtt e retorna uma lista de segmentos com start, end e texto.
    """
    vtt = WebVTT().read(vtt_path)
    segments = []

    for caption in vtt:
        start_sec = time_to_seconds(caption.start)
        end_sec = time_to_seconds(caption.end)
        duration = end_sec - start_sec
        segments.append({
            'start': start_sec,
            'end': end_sec,
            'duration': duration,
            'text': caption.text.strip().replace('\n', ' ')
        })

    return segments


def time_to_seconds(timestamp):
    """Converte tempo VTT (ex: '00:01:02.345') em segundos float"""
    h, m, s = timestamp.split(':')
    s, ms = s.split('.')
    return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000


def cut_audio_grouped(audio_path, segments, out_dir, group_size=10):
    """
    Agrupa segmentos em blocos de 10 e corta o áudio com ffmpeg.
    """
    os.makedirs(out_dir, exist_ok=True)

    for i in range(0, len(segments), group_size):
        group = segments[i:i + group_size]
        start = group[0]['start']
        end = group[-1]['end']
        duration = end - start

        preview_text = ' '.join(seg['text'] for seg in group[:2])
        safe_text = ''.join(c for c in preview_text[:20] if c.isalnum() or c == ' ')\
            .rstrip().replace(' ', '_')

        filename = f"group_{i // group_size + 1:03d}_{safe_text}.mp3"
        output_path = os.path.join(out_dir, filename)

        cmd = [
            'ffmpeg', '-y', '-i', audio_path,
            '-ss', str(start), '-t', str(duration),
            '-c', 'copy', output_path
        ]
        subprocess.run(cmd, check=True)
        print(f"✅ Segmento salvo: {output_path}")


def download_audio(url, out_dir):
    """
    Baixa áudio (mp3) via yt_dlp.
    Retorna o caminho do arquivo de áudio.
    """
    os.makedirs(out_dir, exist_ok=True)
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': os.path.join(out_dir, 'audio.%(ext)s'),
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }]
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.extract_info(url, download=True)
    return os.path.join(out_dir, 'audio.mp3')

def get_video_info(url):
    """Obtém informações básicas do vídeo"""
    with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
        return ydl.extract_info(url, download=False)

def download_subtitle(url, lang, output_dir):
    """Baixa uma única legenda com tratamento robusto de erros"""
    # Criar nome de arquivo seguro
    video_info = get_video_info(url)
    video_id = video_info['id']
    safe_filename = f"{video_id}.{lang}.vtt"
    output_path = os.path.join(output_dir, safe_filename)
    output_path_id = os.path.join(output_dir, video_id)
    
    # Configurações de download
    ydl_opts = {
        'skip_download': True,
        'writesubtitles': True,
        'writeautomaticsub': True,
        'subtitleslangs': [lang],
        'convertsubtitles': 'srt',
        'outtmpl': output_path_id,
        'quiet': True,
        'ignoreerrors': False,
        'no_warnings': True,
    }
    
    print(f"Baixando legenda '{lang}'... {output_path}")
    try:
        # Primeiro verifica se a legenda existe
        available_subs = video_info.get('subtitles', {})
        available_auto_subs = video_info.get('automatic_captions', {})
        
        if lang not in available_subs and lang not in available_auto_subs:
            print(f"Erro: Legenda '{lang}' não disponível para este vídeo")
            print("Legendas disponíveis:")
            for l in list(available_subs.keys()) + list(available_auto_subs.keys()):
                print(f" - {l}")
            sys.exit(1)
        
        # Faz o download
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        
        # Verifica se o arquivo foi criado
        if not os.path.exists(output_path):
            print(f"Erro: Arquivo não foi criado: {output_path}")
            sys.exit(1)
            
        if os.path.getsize(output_path) == 0:
            print(f"Erro: Arquivo de legenda vazio: {output_path}")
            os.remove(output_path)
            sys.exit(1)
            
        print(f"Legenda salva em: {output_path}")
        return output_path
        
    except Exception as e:
        print(f"Erro grave durante download: {str(e)}")
        sys.exit(1)

TIMESTAMP_RE = re.compile(
    r'(?P<start>\d{2}:\d{2}:\d{2}[,\.]\d{3})\s*-->\s*'
    r'(?P<end>\d{2}:\d{2}:\d{2}[,\.]\d{3})'
)

def parse_srt(content: str):
    """
    Parses SRT or VTT content into a list of blocks:
    Each block is a dict with keys: index, start, end, text.
    """
    blocks = []
    parts = re.split(r'\r?\n\r?\n+', content.strip())
    for part in parts:
        lines = part.strip().splitlines()
        # Find the line with timestamps
        time_line = None
        idx = None
        for i, line in enumerate(lines):
            if TIMESTAMP_RE.search(line):
                time_line = line
                # Check if previous line is an index
                if i > 0 and lines[i-1].isdigit():
                    idx = int(lines[i-1])
                text_lines = lines[i+1:]
                break
        if not time_line:
            continue
        m = TIMESTAMP_RE.search(time_line)
        start = m.group('start').replace('.', ',')
        end = m.group('end').replace('.', ',')
        text = "\n".join(text_lines).strip()
        blocks.append({'index': idx, 'start': start, 'end': end, 'text': text})
    return blocks


def main():
    parser = argparse.ArgumentParser(
        description='Ferramenta robusta para download e combinação de legendas do YouTube'
    )
    
    parser.add_argument('url', help='URL do vídeo do YouTube')
    parser.add_argument('-p', '--primary', required=True, 
                       help='Idioma primário (ex: en)')
    parser.add_argument('-s', '--secondary', required=True, 
                       help='Idioma secundário (ex: pt)')
    parser.add_argument('-o', '--output', default='./legendas', 
                       help='diretório de saída (padrão: ./legendas)')

    
    args = parser.parse_args()
    
    # Garante que o diretório de saída existe
    os.makedirs(args.output, exist_ok=True)
    
    print(f"\nProcessando vídeo: {args.url}")
    
    # Baixa as legendas separadamente
    primary_path = download_subtitle(args.url, args.primary, args.output)
    secondary_path = download_subtitle(args.url, args.secondary, args.output)
    
    # Cria nome para o arquivo combinado
    video_info = get_video_info(args.url)
    video_id = video_info['id']
    combined_path = os.path.join(args.output, f"{video_id}.combined.srt")
    
    # Combina as legendas
    combine_subtitles_vtt(primary_path, secondary_path, combined_path)
    
    print("\n✅ Processo concluído com sucesso!")
    print(f"Legenda combinada salva em: {combined_path}")
    name_audio = download_audio(args.url, args.output)
    segments = parse_vtt_to_segments(primary_path)
    cut_audio_grouped(name_audio, segments, args.output, group_size=15)

if __name__ == '__main__':
    main()
