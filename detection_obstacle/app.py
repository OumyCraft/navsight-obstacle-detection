from flask import Flask, jsonify, send_from_directory, request
import os
import cv2
import json

# Importez vos fonctions clés depuis le module de détection
from detector_module import detect_obstacles_combined, annotate_frame, export_detections_json

# --- Définition des chemins relatifs à app.py ---
CURRENT_FILE_DIR = os.path.dirname(os.path.abspath(__file__)) 
BASE_DIR = os.path.dirname(CURRENT_FILE_DIR) # EXAMEN_COMPUTER_VISION

# Chemins de ressources utilisés par l'API
IMAGES_DIR = os.path.join(BASE_DIR, "ressources", "images")
OUTPUT_DIR = os.path.join(CURRENT_FILE_DIR, "output")
ANNOTATED_IMAGES_DIR = os.path.join(OUTPUT_DIR, "annotated_images")

# Initialisation de Flask
app = Flask(__name__, static_folder='.', static_url_path='/')

# --- Routes Flask ---

@app.route('/')
def index():
    """Route principale pour servir la nouvelle interface holographique"""
    return send_from_directory(CURRENT_FILE_DIR, 'holographic_viewer.html')

@app.route('/api/images', methods=['GET'])
def list_images():
    """Liste les images disponibles pour le panneau de sélection."""
    try:
        # Lister TOUS les fichiers du dossier
        all_files = os.listdir(IMAGES_DIR)
        print(f"[DEBUG] Tous les fichiers trouvés: {all_files}")
        
        # Filtrer les images
        image_files = [f for f in all_files 
                       if f.lower().endswith((".jpg", ".png", ".jpeg"))]
        
        print(f"[DEBUG] Images filtrées ({len(image_files)}): {image_files}")
        
        return jsonify({'images': image_files})
    except Exception as e:
        print(f"[ERREUR] Liste des images: {e}")
        return jsonify({'error': f'Erreur lors de la liste des images: {e}'}), 500


@app.route('/api/detect/<filename>', methods=['POST'])
def run_detection(filename):
    """
    Déclenche la détection, sauvegarde l'image annotée et retourne les données JSON.
    """
    
    image_path_full = os.path.join(IMAGES_DIR, filename)
    if not os.path.exists(image_path_full):
        return jsonify({'error': f'Image source non trouvée: {filename}'}), 404

    print(f"[API] Lancement de la détection pour {filename}...")
    
    # 1. Lire l'image
    frame = cv2.imread(image_path_full)
    if frame is None:
        return jsonify({'error': 'Erreur de lecture de l\'image (OpenCV)'}), 500
    
    # 2. Effectuer la détection
    try:
        obstacles = detect_obstacles_combined(frame) 
    except Exception as e:
        print(f"[ERREUR] Échec de la détection: {e}")
        return jsonify({'error': f'Échec de la détection du modèle: {e}'}), 500

    # 3. Annotation et Sauvegarde de l'image annotée
    output_frame = annotate_frame(frame, obstacles)
    annotated_filename = f"annotated_{filename}"
    output_image_path = os.path.join(ANNOTATED_IMAGES_DIR, annotated_filename)
    
    # Sauvegarde
    if filename.lower().endswith(('.jpg', '.jpeg')):
        cv2.imwrite(output_image_path, output_frame, [cv2.IMWRITE_JPEG_QUALITY, 90])
    else:
        cv2.imwrite(output_image_path, output_frame)

    # 4. Exporter les détections en JSON
    json_path = export_detections_json(filename, obstacles)
    
    # 5. Lire et retourner le contenu du fichier JSON
    try:
        with open(json_path, 'r') as f:
            json_data = json.load(f)
    except Exception as e:
        return jsonify({'error': f'Erreur de lecture du JSON: {e}'}), 500
    
    # Ajouter l'URL de l'image annotée pour le frontend
    json_data['image_url'] = f'/output/annotated_images/{annotated_filename}'
    
    print(f"[API] Détection terminée. Image annotée: {output_image_path}")
    
    return jsonify(json_data)


# Route pour servir les fichiers des dossiers de sortie (images annotées, JSON)
@app.route('/output/<path:filepath>')
def serve_output_file(filepath):
    """Permet au frontend d'accéder aux images annotées."""
    return send_from_directory(OUTPUT_DIR, filepath)

# Route pour servir les modèles 3D
@app.route('/3Dmodels/<path:filename>')
def serve_3d_model(filename):
    """Permet au frontend d'accéder aux modèles 3D."""
    return send_from_directory(os.path.join(CURRENT_FILE_DIR, '3Dmodels'), filename)

# Route pour servir les images originales (pour l'affichage progressif)
@app.route('/ressources/images/<path:filename>')
def serve_original_image(filename):
    """Permet au frontend d'accéder aux images originales."""
    return send_from_directory(IMAGES_DIR, filename)

#Route pour servir les fichiers audio 
@app.route('/audio/<path:filename>')
def serve_audio(filename):
    """Permet au frontend d'accéder aux fichiers audio."""
    audio_dir = os.path.join(CURRENT_FILE_DIR, 'audio')
    print(f"[DEBUG] Tentative de lecture audio: {os.path.join(audio_dir, filename)}")
    return send_from_directory(audio_dir, filename)


if __name__ == '__main__':
    print("\n" + "="*50)
    print("SERVEUR FLASK DÉMARRÉ")
    print("Accédez à l'interface holographique sur: http://127.0.0.1:5000")
    print("="*50 + "\n")
    app.run(debug=True, host='0.0.0.0', port=5000, threaded=False)