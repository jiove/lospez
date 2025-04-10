import os
import uuid
import cv2
import numpy as np
import time
import json
import subprocess
import requests
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, render_template, send_from_directory, redirect, url_for, abort
from werkzeug.utils import secure_filename
from scenedetect import VideoManager, SceneManager, StatsManager
from scenedetect.detectors import ContentDetector
from scenedetect.scene_manager import save_images
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from pytube import YouTube
import re

app = Flask(__name__, 
            static_folder='static',
            template_folder='templates')
            
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['RESULTS_FOLDER'] = 'results'
app.config['ALLOWED_EXTENSIONS'] = {'mp4', 'avi', 'mov'}
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500 MB max
app.config['LANDING_PAGE_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'Landing page', 'dist')

# Rate limiter configuration
limiter = Limiter(
    key_func=get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

# IP tracking for upload limits
ip_upload_tracker = {}

# Assicurati che le cartelle necessarie esistano
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['RESULTS_FOLDER'], exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def check_upload_limit(ip_address):
    """Check if IP has exceeded upload limit (5 uploads per hour)"""
    current_time = datetime.now()
    if ip_address in ip_upload_tracker:
        uploads = ip_upload_tracker[ip_address]
        # Remove uploads older than 1 hour
        uploads = [t for t in uploads if current_time - t < timedelta(hours=1)]
        if len(uploads) >= 5:
            return False
        ip_upload_tracker[ip_address] = uploads + [current_time]
    else:
        ip_upload_tracker[ip_address] = [current_time]
    return True

@app.route('/')
def landing_page():
    # Serve our custom landing page
    return render_template('landing.html')

# Serve static files from landing page
@app.route('/<path:path>')
def serve_landing_page_static(path):
    if os.path.exists(os.path.join(app.config['LANDING_PAGE_FOLDER'], path)):
        return send_from_directory(app.config['LANDING_PAGE_FOLDER'], path)
    return app.send_static_file(path)

@app.route('/spezzettatore')
def spezzettatore():
    video_id = request.args.get('video_id')
    mode = request.args.get('mode')
    
    # Se non c'è un video_id, renderizza la pagina senza parametri
    if not video_id:
        return render_template('index.html', video_id='', mode='')
        
    return render_template('index.html', video_id=video_id, mode=mode)

@app.route('/upload', methods=['POST'])
@limiter.limit("5 per hour")  # Limit to 5 uploads per hour
def upload_file():
    # Check if IP has exceeded upload limit
    if not check_upload_limit(request.remote_addr):
        return jsonify({'error': 'You have exceeded the upload limit (5 uploads per hour)'}), 429
    
    # Check if the post request has the file part
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    
    # If user does not select file, browser also
    # submit an empty part without filename
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file and allowed_file(file.filename):
        # Generate a unique ID for this upload
        upload_id = str(uuid.uuid4())
        
        # Create directory for this upload
        upload_dir = os.path.join(app.config['UPLOAD_FOLDER'], upload_id)
        os.makedirs(upload_dir, exist_ok=True)
        
        # Save the file
        filename = secure_filename(file.filename)
        file_path = os.path.join(upload_dir, filename)
        file.save(file_path)
        
        # Create a cartella for the results
        result_folder = os.path.join(app.config['RESULTS_FOLDER'], upload_id)
        os.makedirs(result_folder, exist_ok=True)
        
        # Esegui il rilevamento delle scene
        try:
            scenes, video_info = detect_scenes(file_path, result_folder)
            
            return jsonify({
                'success': True,
                'message': 'Rilevamento scene completato con successo',
                'id': upload_id,
                'scenes': scenes,
                'video_info': video_info
            })
        except Exception as e:
            return jsonify({'error': f'Errore durante il rilevamento delle scene: {str(e)}'}), 500
    
    return jsonify({'error': 'File type not allowed'}), 400

def detect_scenes(video_path, output_folder):
    # Inizializza il video manager
    video_manager = VideoManager([video_path])
    stats_manager = StatsManager()
    scene_manager = SceneManager(stats_manager)
    
    # Aggiungi il rilevatore di contenuti (puoi regolare la soglia di sensibilità)
    scene_manager.add_detector(ContentDetector(threshold=30.0))
    
    # Imposta la durata del downscale per migliorare le prestazioni
    video_manager.set_downscale_factor()
    
    # Avvia il video manager
    video_manager.start()
    
    # Rileva tutte le scene
    scene_manager.detect_scenes(frame_source=video_manager)
    
    # Ottieni l'elenco delle scene rilevate
    scene_list = scene_manager.get_scene_list()
    
    # Estrai il primo frame di ogni scena e salva le scene in formato video
    scenes = []
    
    # Utilizziamo OpenCV direttamente per estrarre i frame e le scene video
    cap = cv2.VideoCapture(video_path)
    
    # Ottieni le proprietà del video
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    # Crea una sottocartella per i video delle scene
    video_folder = os.path.join(output_folder, 'videos')
    os.makedirs(video_folder, exist_ok=True)
    
    for i, scene in enumerate(scene_list):
        # Ottieni il numero del primo e dell'ultimo frame della scena
        start_frame = scene[0].frame_num
        end_frame = scene[1].frame_num
        
        # Posiziona il video sul frame desiderato per estrarre il primo frame
        cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
        
        # Leggi il frame
        ret, frame = cap.read()
        
        if ret:
            # Salva il primo frame come immagine
            frame_path = os.path.join(output_folder, f'scene_{i+1:03d}.jpg')
            cv2.imwrite(frame_path, frame)
            
            # Crea un writer video per questa scena
            video_path = os.path.join(video_folder, f'scene_{i+1:03d}.mp4')
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            video_writer = cv2.VideoWriter(video_path, fourcc, fps, (width, height))
            
            # Torna al primo frame della scena
            cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
            
            # Leggi e scrivi tutti i frame di questa scena
            current_frame = start_frame
            while current_frame < end_frame:
                ret, frame = cap.read()
                if not ret:
                    break
                video_writer.write(frame)
                current_frame += 1
            
            # Rilascia il writer video
            video_writer.release()
            
            scenes.append({
                'id': i+1,
                'start_time': scene[0].get_seconds(),
                'end_time': scene[1].get_seconds(),
                'duration': scene[1].get_seconds() - scene[0].get_seconds(),
                'thumbnail': f'/results/{os.path.basename(output_folder)}/scene_{i+1:03d}.jpg',
                'video': f'/results/{os.path.basename(output_folder)}/videos/scene_{i+1:03d}.mp4'
            })
    
    # Rilascia il video capture
    cap.release()
    
    # Ottieni altre informazioni sul video
    video_format = os.path.splitext(os.path.basename(video_path))[1][1:].upper()
    if not video_format:
        video_format = "Unknown"
    
    video_info = {
        'duration': scene_list[-1][1].get_seconds() if scene_list else 0,
        'fps': fps,
        'resolution': f"{width}x{height}",
        'format': video_format
    }
    
    return scenes, video_info

def detect_scenes_10s(video_path, output_folder):
    """
    Taglia il video in segmenti di massimo 10 secondi, indipendentemente dai cambi di scena.
    """
    # Crea una sottocartella per i video delle scene
    video_folder = os.path.join(output_folder, 'videos')
    os.makedirs(video_folder, exist_ok=True)
    
    # Utilizziamo OpenCV per aprire il video
    cap = cv2.VideoCapture(video_path)
    
    # Ottieni le proprietà del video
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    # Ottieni la rotazione del video dai metadati
    rotation = int(cap.get(cv2.CAP_PROP_ORIENTATION_META))
    
    # Calcola il numero di frame per 10 secondi
    frames_per_segment = int(fps * 10)
    
    # Lista per tenere traccia di tutte le scene
    scenes = []
    
    # Per ogni segmento di 10 secondi
    segment_count = 0
    start_frame = 0
    
    while start_frame < total_frames:
        segment_count += 1
        
        # Calcola il frame finale per questo segmento
        end_frame = min(start_frame + frames_per_segment, total_frames)
        
        # Posiziona il video sul frame iniziale e verifica che il seeking sia avvenuto correttamente
        while True:
            cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
            actual_pos = int(cap.get(cv2.CAP_PROP_POS_FRAMES))
            if actual_pos == start_frame:
                break
            # Se il seeking non è preciso, prova a leggere frame per frame
            cap.read()
        
        # Leggi il primo frame
        ret, frame = cap.read()
        
        if ret:
            # Applica la rotazione corretta al frame se necessario
            if rotation == 90:
                frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
            elif rotation == 180:
                frame = cv2.rotate(frame, cv2.ROTATE_180)
            elif rotation == 270:
                frame = cv2.rotate(frame, cv2.ROTATE_90_COUNTERCLOCKWISE)
            
            # Crea una copia del frame per l'anteprima
            thumbnail = frame.copy()
            
            # Salva il primo frame come immagine thumbnail
            frame_path = os.path.join(output_folder, f'scene_{segment_count:03d}.jpg')
            cv2.imwrite(frame_path, thumbnail)
            
            # Crea un writer video per questo segmento
            video_path = os.path.join(video_folder, f'scene_{segment_count:03d}.mp4')
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            
            # Se il video è ruotato, scambia width e height
            if rotation in [90, 270]:
                video_writer = cv2.VideoWriter(video_path, fourcc, fps, (height, width))
            else:
                video_writer = cv2.VideoWriter(video_path, fourcc, fps, (width, height))
            
            # Scrivi il primo frame
            video_writer.write(frame)
            
            # Leggi e scrivi i frame rimanenti
            current_frame = start_frame + 1
            while current_frame < end_frame:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Applica la rotazione corretta al frame se necessario
                if rotation == 90:
                    frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
                elif rotation == 180:
                    frame = cv2.rotate(frame, cv2.ROTATE_180)
                elif rotation == 270:
                    frame = cv2.rotate(frame, cv2.ROTATE_90_COUNTERCLOCKWISE)
                
                video_writer.write(frame)
                current_frame += 1
            
            # Rilascia il writer video
            video_writer.release()
            
            # Calcola i tempi in secondi
            start_time = start_frame / fps
            end_time = end_frame / fps
            
            # Aggiungi informazioni sulla scena
            scenes.append({
                'id': segment_count,
                'start_time': start_time,
                'end_time': end_time,
                'duration': end_time - start_time,
                'thumbnail': f'/results/{os.path.basename(output_folder)}/scene_{segment_count:03d}.jpg',
                'video': f'/results/{os.path.basename(output_folder)}/videos/scene_{segment_count:03d}.mp4'
            })
        
        # Passa al prossimo segmento
        start_frame = end_frame
    
    # Rilascia il video capture
    cap.release()
    
    # Ottieni altre informazioni sul video
    video_format = os.path.splitext(os.path.basename(video_path))[1][1:].upper()
    if not video_format:
        video_format = "Unknown"
    
    # Crea un dizionario con le informazioni sul video
    video_info = {
        'duration': total_frames / fps,
        'fps': fps,
        'resolution': f"{width}x{height}",
        'format': video_format
    }
    
    return scenes, video_info

@app.route('/upload10s', methods=['POST'])
@limiter.limit("5 per hour")  # Limit to 5 uploads per hour
def upload_file_10s():
    # Check if IP has exceeded upload limit
    if not check_upload_limit(request.remote_addr):
        return jsonify({'error': 'You have exceeded the upload limit (5 uploads per hour)'}), 429
    
    # Check if the post request has the file part
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    
    # If user does not select file, browser also
    # submit an empty part without filename
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file and allowed_file(file.filename):
        # Generate a unique ID for this upload
        upload_id = str(uuid.uuid4())
        
        # Create directory for this upload
        upload_dir = os.path.join(app.config['UPLOAD_FOLDER'], upload_id)
        os.makedirs(upload_dir, exist_ok=True)
        
        # Save the file
        filename = secure_filename(file.filename)
        file_path = os.path.join(upload_dir, filename)
        file.save(file_path)
        
        # Create a cartella for the results
        result_folder = os.path.join(app.config['RESULTS_FOLDER'], upload_id)
        os.makedirs(result_folder, exist_ok=True)
        
        # Esegui il rilevamento delle scene con segmenti di 10 secondi
        try:
            scenes, video_info = detect_scenes_10s(file_path, result_folder)
            
            return jsonify({
                'success': True,
                'message': 'Spezzettamento in segmenti di 10s completato con successo',
                'id': upload_id,
                'scenes': scenes,
                'video_info': video_info
            })
        except Exception as e:
            return jsonify({'error': f'Errore durante lo spezzettamento: {str(e)}'}), 500
    
    return jsonify({'error': 'File type not allowed'}), 400

@app.route('/results/<id>')
def get_results(id):
    results_folder = os.path.join(app.config['RESULTS_FOLDER'], id)
    if not os.path.exists(results_folder):
        return jsonify({'error': 'Results not found'}), 404
    
    # Cerca tutte le immagini nella cartella dei risultati
    images = [f for f in os.listdir(results_folder) if f.endswith('.jpg')]
    
    return jsonify({
        'id': id,
        'images': [f'/results/{id}/{img}' for img in images]
    })

@app.route('/results/<id>/<filename>')
@limiter.exempt  # Questa route è esente dal rate limiting
def serve_result(id, filename):
    return send_from_directory(os.path.join(app.config['RESULTS_FOLDER'], id), filename)

@app.route('/download/<id>')
def download_results(id):
    results_folder = os.path.join(app.config['RESULTS_FOLDER'], id)
    if not os.path.exists(results_folder):
        return jsonify({'error': 'Results not found'}), 404
    
    # Crea un archivio ZIP con tutte le immagini usando una compressione migliore
    zip_path = os.path.join(results_folder, 'images.zip')
    
    # Comprimi tutte le immagini nella cartella con compressione ottimizzata
    import zipfile
    with zipfile.ZipFile(zip_path, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zipf:
        for file in os.listdir(results_folder):
            if file.endswith('.jpg'):
                zipf.write(os.path.join(results_folder, file), file)
    
    return send_from_directory(results_folder, 'images.zip', as_attachment=True)

@app.route('/download-videos/<id>')
def download_videos(id):
    videos_folder = os.path.join(app.config['RESULTS_FOLDER'], id, 'videos')
    if not os.path.exists(videos_folder):
        return jsonify({'error': 'Videos not found'}), 404
    
    # Crea un archivio ZIP con tutti i video usando una compressione migliore
    zip_path = os.path.join(app.config['RESULTS_FOLDER'], id, 'videos.zip')
    
    # Comprimi tutti i video nella cartella con compressione ottimizzata
    import zipfile
    with zipfile.ZipFile(zip_path, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zipf:
        for file in os.listdir(videos_folder):
            if file.endswith('.mp4'):
                zipf.write(os.path.join(videos_folder, file), file)
    
    return send_from_directory(os.path.join(app.config['RESULTS_FOLDER'], id), 'videos.zip', as_attachment=True)

def download_youtube_with_pytube(url, output_path, filename):
    """
    Scarica un video da YouTube usando pytube
    """
    yt = YouTube(
        url,
        use_oauth=False,
        allow_oauth_cache=False
    )
    
    # Attendi il caricamento dei dati del video
    max_retries = 3
    for attempt in range(max_retries):
        try:
            # Forza il caricamento dei metadata
            title = yt.title
            author = yt.author
            length = yt.length
            views = yt.views
            break
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            time.sleep(1)  # Attendi un secondo prima di riprovare
    
    # Ottieni le informazioni sugli stream disponibili
    streams = list(yt.streams.filter(file_extension='mp4').order_by('resolution').desc())
    
    if not streams:
        raise Exception('Nessun formato video disponibile per il download')
    
    # Prova a ottenere un video progressivo (audio + video)
    video = next((s for s in streams if s.is_progressive), None)
    
    # Se non c'è un video progressivo, prendi il primo disponibile
    if not video:
        video = streams[0]
    
    # Scarica il video
    video.download(output_path=output_path, filename=filename)
    
    return {
        'title': yt.title,
        'author': yt.author,
        'length': yt.length,
        'views': yt.views
    }

def download_youtube_with_ytdlp(url, output_path, filename):
    """
    Scarica un video da YouTube usando yt-dlp come alternativa
    """
    try:
        # Comando yt-dlp per scaricare il video
        full_output_path = os.path.join(output_path, filename)
        
        # Ottieni prima le informazioni del video
        info_cmd = [
            'yt-dlp', 
            '--dump-json',
            '--no-playlist',
            url
        ]
        
        # Esegui il comando per ottenere le informazioni
        process = subprocess.Popen(info_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        stdout, stderr = process.communicate()
        
        if process.returncode != 0:
            raise Exception(f"yt-dlp info error: {stderr}")
        
        # Analizza le informazioni del video
        video_info = json.loads(stdout)
        
        # Esegui il download
        download_cmd = [
            'yt-dlp',
            '--format', 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            '--merge-output-format', 'mp4',
            '-o', full_output_path,
            '--no-playlist',
            url
        ]
        
        process = subprocess.Popen(download_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        stdout, stderr = process.communicate()
        
        if process.returncode != 0:
            raise Exception(f"yt-dlp download error: {stderr}")
        
        return {
            'title': video_info.get('title', 'Unknown Title'),
            'author': video_info.get('uploader', 'Unknown Author'),
            'length': video_info.get('duration', 0),
            'views': video_info.get('view_count', 0)
        }
    except Exception as e:
        # Se yt-dlp fallisce, prova a utilizzare requests direttamente (funziona solo per alcuni video)
        try:
            # Utilizzo di requests come ultima risorsa
            from pytube import YouTube
            yt = YouTube(url)
            
            # Ottieni solo l'URL dello stream
            streams = list(yt.streams.filter(file_extension='mp4').order_by('resolution').desc())
            if not streams:
                raise Exception("Nessuno stream disponibile")
                
            video = streams[0]
            stream_url = video.url
            
            response = requests.get(stream_url, stream=True)
            if not response.ok:
                raise Exception(f"Errore HTTP: {response.status_code}")
                
            full_output_path = os.path.join(output_path, filename)
            with open(full_output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=1024*1024):
                    if chunk:
                        f.write(chunk)
            
            return {
                'title': yt.title,
                'author': yt.author,
                'length': yt.length,
                'views': yt.views
            }
        except Exception as inner_e:
            raise Exception(f"Tutti i metodi di download hanno fallito. yt-dlp: {str(e)}, requests: {str(inner_e)}")

@app.route('/download-yt', methods=['POST'])
@limiter.limit("20 per hour")  # Limit to 20 downloads per hour
def download_youtube():
    try:
        url = request.form.get('youtube_url')
        if not url:
            return jsonify({'error': 'URL YouTube mancante'}), 400
        
        # Pulisci l'URL (rimuovi parametri non necessari)
        if '&' in url:
            url = url.split('&')[0]
        
        # Estrai l'ID del video
        video_id = None
        if 'youtube.com/watch?v=' in url:
            video_id = url.split('youtube.com/watch?v=')[1]
        elif 'youtu.be/' in url:
            video_id = url.split('youtu.be/')[1]
        
        if not video_id:
            return jsonify({'error': 'URL YouTube non valido'}), 400
        
        # Prova a scaricare con pytube
        try:
            yt = YouTube(url)
            title = yt.title
            
            # Informazioni video
            info = {
                'title': title,
                'id': video_id
            }
            
            return jsonify({
                'success': True,
                'message': 'Video pronto per l\'elaborazione',
                'info': info
            })
            
        except Exception as e:
            # Se pytube fallisce, prova un altro metodo
            try:
                # Usa requests per ottenere almeno il titolo
                response = requests.get(f"https://www.youtube.com/watch?v={video_id}")
                if response.status_code == 200:
                    # Estrai il titolo dall'HTML (metodo semplificato)
                    html = response.text
                    title_start = html.find('<title>') + 7
                    title_end = html.find('</title>', title_start)
                    title = html[title_start:title_end]
                    title = title.replace(' - YouTube', '')
                    
                    info = {
                        'title': title,
                        'id': video_id
                    }
                    
                    return jsonify({
                        'success': True,
                        'message': 'Video pronto per l\'elaborazione',
                        'info': info
                    })
                else:
                    return jsonify({'error': f'Impossibile accedere al video YouTube: HTTP {response.status_code}'}), 500
            except Exception as e2:
                return jsonify({'error': f'Errore durante l\'elaborazione del video: {str(e)}. Tentativo alternativo fallito: {str(e2)}'}), 500
    
    except Exception as e:
        return jsonify({'error': f'Errore durante l\'elaborazione della richiesta: {str(e)}'}), 500

@app.route('/find-video/<id>')
def find_video(id):
    """
    Reindirizza alla pagina dello spezzettatore con i parametri corretti.
    """
    mode = request.args.get('mode')
    if mode == '10s':
        return redirect(url_for('spezzettatore', video_id=id, mode='10s'))
    else:
        return redirect(url_for('spezzettatore', video_id=id))

@app.route('/process-youtube/<id>')
def process_youtube(id):
    """
    Elabora un video YouTube usando il rilevamento delle scene
    """
    try:
        # Scarica il video
        download_result = download_youtube_video(id)
        if not download_result['success']:
            return jsonify({'error': download_result['error']}), 500
        
        video_path = download_result['path']
        
        # Crea una cartella per i risultati
        result_folder = os.path.join(app.config['RESULTS_FOLDER'], id)
        os.makedirs(result_folder, exist_ok=True)
        
        # Esegui il rilevamento delle scene
        scenes, video_info = detect_scenes(video_path, result_folder)
        
        return jsonify({
            'success': True,
            'message': 'Rilevamento scene completato con successo',
            'id': id,
            'scenes': scenes,
            'video_info': video_info
        })
    except Exception as e:
        return jsonify({'error': f'Errore durante l\'elaborazione: {str(e)}'}), 500

@app.route('/process-yt/<id>')
def process_youtube_segments(id):
    """
    Elabora un video YouTube dividendolo in segmenti di 10 secondi
    """
    try:
        # Scarica il video
        download_result = download_youtube_video(id)
        if not download_result['success']:
            return jsonify({'error': download_result['error']}), 500
        
        video_path = download_result['path']
        
        # Crea una cartella per i risultati
        result_folder = os.path.join(app.config['RESULTS_FOLDER'], id)
        os.makedirs(result_folder, exist_ok=True)
        
        # Dividi in segmenti di 10 secondi
        scenes, video_info = detect_scenes_10s(video_path, result_folder)
        
        return jsonify({
            'success': True,
            'message': 'Spezzettamento in segmenti di 10s completato con successo',
            'id': id,
            'scenes': scenes,
            'video_info': video_info
        })
    except Exception as e:
        return jsonify({'error': f'Errore durante l\'elaborazione: {str(e)}'}), 500

def download_youtube_video(video_id):
    """
    Scarica un video YouTube dato l'ID
    """
    try:
        # URL del video
        url = f"https://www.youtube.com/watch?v={video_id}"
        
        # Directory per il download
        upload_dir = os.path.join(app.config['UPLOAD_FOLDER'], video_id)
        os.makedirs(upload_dir, exist_ok=True)
        
        # Nome del file di output
        output_file = os.path.join(upload_dir, f"youtube_{video_id}.mp4")
        
        # Prova prima con pytube
        try:
            print(f"Tentativo di download con pytube: {url}")
            yt = YouTube(url)
            # Seleziona la migliore qualità video con audio
            stream = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first()
            if not stream:
                # Se non trova stream progressive, prova senza filtro progressive
                stream = yt.streams.filter(file_extension='mp4').order_by('resolution').desc().first()
            
            if stream:
                stream.download(output_path=upload_dir, filename=f"youtube_{video_id}.mp4")
                print(f"Download completato con pytube: {output_file}")
                return {
                    'success': True,
                    'path': output_file
                }
            else:
                raise Exception("Nessuno stream disponibile per questo video")
        
        except Exception as e:
            print(f"Errore con pytube: {str(e)}")
            # Se pytube fallisce, prova con yt-dlp
            try:
                print(f"Tentativo di download con yt-dlp: {url}")
                
                # Verifica se yt-dlp è installato
                try:
                    # Try which command on Linux/Mac
                    yt_dlp_path = subprocess.check_output(["which", "yt-dlp"], text=True).strip()
                except:
                    try:
                        # Try where command on Windows
                        yt_dlp_path = subprocess.check_output(["where", "yt-dlp"], text=True).strip()
                    except:
                        # Fall back to assuming yt-dlp is in PATH
                        yt_dlp_path = "yt-dlp"
                
                print(f"yt-dlp path: {yt_dlp_path}")
                
                # Run yt-dlp with verbose output
                command = [yt_dlp_path, "-v", "-f", "best", "-o", output_file, url]
                print(f"Comando yt-dlp: {' '.join(command)}")
                
                result = subprocess.run(
                    command,
                    check=True,
                    text=True,
                    capture_output=True,
                    timeout=300  # timeout di 5 minuti
                )
                
                print(f"Output yt-dlp: {result.stdout}")
                if result.stderr:
                    print(f"Errore yt-dlp: {result.stderr}")
                
                # Verifica se il file esiste e ha dimensioni valide
                if os.path.exists(output_file) and os.path.getsize(output_file) > 0:
                    print(f"Download completato con yt-dlp: {output_file}")
                    return {
                        'success': True,
                        'path': output_file
                    }
                else:
                    raise Exception("Il file scaricato è vuoto o non esiste")
                
            except subprocess.CalledProcessError as e:
                error_message = f"Errore durante l'esecuzione di yt-dlp: {str(e)}"
                if hasattr(e, 'output'):
                    error_message += f" Output: {e.output}"
                if hasattr(e, 'stderr'):
                    error_message += f" Stderr: {e.stderr}"
                print(error_message)
                return {
                    'success': False,
                    'error': error_message
                }
            except Exception as e:
                error_message = f"Errore durante il download con yt-dlp: {str(e)}"
                print(error_message)
                return {
                    'success': False,
                    'error': error_message
                }
    
    except Exception as e:
        error_message = f"Errore durante il download del video: {str(e)}"
        print(error_message)
        return {
            'success': False,
            'error': error_message
        }

# Security headers middleware
@app.after_request
def add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    return response

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5004)
    
# Necessary for Vercel
app.config['VERCEL_DEPLOYMENT'] = os.environ.get('VERCEL_DEPLOYMENT') == 'true'
