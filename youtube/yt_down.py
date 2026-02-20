#!/usr/bin/env python3
"""
Script para baixar áudio (MP3) e legenda (SRT) de vídeos do YouTube usando yt-dlp
com argumentos via linha de comando.
"""

import os
import sys
import argparse
import yt_dlp


def download_audio(url: str, out_dir: str) -> str:
    """Baixa o áudio no formato MP3"""
    os.makedirs(out_dir, exist_ok=True)
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': os.path.join(out_dir, '%(id)s - %(title)s.%(ext)s'),
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'quiet': False,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            audio_path = filename.rsplit('.', 1)[0] + '.mp3'
        
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Arquivo de áudio não encontrado: {audio_path}")
            
        print(f"Áudio salvo em: {audio_path}")
        return audio_path
        
    except Exception as e:
        print(f"Erro ao baixar áudio: {str(e)}", file=sys.stderr)
        sys.exit(1)


def get_video_info(url: str) -> dict:
    """Obtém metadados do vídeo sem baixar"""
    with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
        return ydl.extract_info(url, download=False)


def download_subtitle(url: str, lang: str, output_dir: str) -> str | None:
    """Baixa legenda convertida para SRT"""
    os.makedirs(output_dir, exist_ok=True)

    try:
        video_info = get_video_info(url)
        video_id = video_info.get('id', 'video')
        video_title = video_info.get('title', 'sem_titulo')
        
        # Nome seguro e descritivo
        base_name = f"{video_id} - {video_title[:80]}"
        base_name = "".join(c for c in base_name if c.isalnum() or c in " -_").strip()
        output_template = os.path.join(output_dir, base_name)
        
        ydl_opts = {
            'skip_download': True,
            'writesubtitles': True,
            'writeautomaticsub': True,
            'subtitleslangs': [lang],
            'subtitlesformat': 'srt/best',
            'convertsubtitles': 'srt',
            'outtmpl': output_template,
            'quiet': False,
        }

        print(f"Tentando baixar legenda em '{lang}'...")

        available_manual = set(video_info.get('subtitles', {}).keys())
        available_auto = set(video_info.get('automatic_captions', {}).keys())
        available = available_manual | available_auto

        if lang not in available:
            print(f"Legenda '{lang}' não disponível.")
            if available:
                print("Legendas disponíveis:", ", ".join(sorted(available)))
            else:
                print("Nenhuma legenda (manual ou automática) disponível.")
            return None

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        # Procura o arquivo gerado
        possible = [
            f"{output_template}.{lang}.srt",
            f"{output_template}.{lang}.vtt",
        ]

        for path in possible:
            if os.path.exists(path) and os.path.getsize(path) > 200:
                print(f"Legenda salva em: {path}")
                return path
        
        print("Não foi possível localizar o arquivo de legenda válido.")
        return None

    except Exception as e:
        print(f"Erro ao baixar legenda: {str(e)}", file=sys.stderr)
        return None


def main():
    parser = argparse.ArgumentParser(
        description="Baixa áudio (MP3) e legenda (SRT) de vídeos do YouTube usando yt-dlp",
        formatter_class=argparse.RawTextHelpFormatter
    )
    
    parser.add_argument(
        "url",
        help="URL do vídeo do YouTube (ex: https://youtu.be/abc123)"
    )
    
    parser.add_argument(
        "-l", "--lang", "--legendas",
        default="en",
        help="Código da língua da legenda (padrão: pt)\nExemplos: pt, en, es, fr"
    )
    
    parser.add_argument(
        "-o", "--output", "--saida",
        default="downloads",
        help="Pasta onde salvar os arquivos (padrão: ./downloads)"
    )
    
    parser.add_argument(
        "--only-audio",
        action="store_true",
        help="Baixar apenas o áudio (ignora legenda)"
    )
    
    parser.add_argument(
        "--only-subtitle",
        action="store_true",
        help="Baixar apenas a legenda (ignora áudio)"
    )

    args = parser.parse_args()

    print("═" * 60)
    print(f"URL:          {args.url}")
    print(f"Língua:       {args.lang}")
    print(f"Pasta saída:  {args.output}")
    print("═" * 60)

    audio_file = None
    subtitle_file = None

    if not args.only_subtitle:
        print("\n→ Baixando áudio...")
        audio_file = download_audio(args.url, args.output)

    if not args.only_audio:
        print("\n→ Baixando legenda...")
        subtitle_file = download_subtitle(args.url, args.lang, args.output)

    print("\n" + "═" * 60)
    if audio_file or subtitle_file:
        print("Resumo do download:")
        if audio_file:
            print(f"Áudio   → {audio_file}")
        if subtitle_file:
            print(f"Legenda → {subtitle_file}")
    else:
        print("Nenhum arquivo foi baixado com sucesso.")


if __name__ == "__main__":
    main()
