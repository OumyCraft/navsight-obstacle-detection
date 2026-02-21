import cv2
import os
import shutil
import numpy as np
from ultralytics import YOLO
import torch
from transformers import AutoImageProcessor, Mask2FormerForUniversalSegmentation
from PIL import Image
import json 

# ---------------------------------------------------------
# CONFIGURATION DES CHEMINS
# ---------------------------------------------------------
# Le répertoire actuel est projet_detection_obstacle
CURRENT_FILE_DIR = os.path.dirname(os.path.abspath(__file__)) 
# Le répertoire racine est EXAMEN_COMPUTER_VISION (un niveau au-dessus)
BASE_DIR = os.path.dirname(CURRENT_FILE_DIR) 

# Chemins de ressources dans EXAMEN_COMPUTER_VISION
RESOURCES_DIR = os.path.join(BASE_DIR, "ressources")
MODELS_DIR = os.path.join(RESOURCES_DIR, "models") # Répertoire de stockage des fichiers .pt et cache Hugging Face
IMAGES_DIR = os.path.join(RESOURCES_DIR, "images")
VIDEOS_DIR = os.path.join(RESOURCES_DIR, "videos")

# Chemins de sortie dans projet_detection_obstacle
OUTPUT_DIR = os.path.join(CURRENT_FILE_DIR, "output")
ANNOTATED_IMAGES_DIR = os.path.join(OUTPUT_DIR, "annotated_images")
JSON_DIR = os.path.join(OUTPUT_DIR, "json") # Chemin pour l'export des métadonnées

# Créer les répertoires nécessaires (avec exist_ok=True pour éviter les erreurs)
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(ANNOTATED_IMAGES_DIR, exist_ok=True)
os.makedirs(JSON_DIR, exist_ok=True) # Création du répertoire JSON
os.makedirs(MODELS_DIR, exist_ok=True)

# ---------------------------------------------------------
# CONFIGURATION DES OBSTACLES - MAPILLARY VISTAS (Inchangée)
# ---------------------------------------------------------
# Ce dictionnaire sert de filtre pour les classes du modèle Mask2Former et leur assigne une priorité
MAPILLARY_OBSTACLES = {
    # Critiques - Dénivelés (Priorité 1: Danger immédiat)
    "Manhole": {"priority": 1, "color": (0, 0, 255)}, # BGR: Rouge
    "Curb": {"priority": 1, "color": (0, 0, 255)},
    "Curb Cut": {"priority": 1, "color": (0, 0, 255)},
    
    # Obstacles verticaux - Poteaux et lampadaires (Priorité 2: Obstacles à éviter)
    "Pole": {"priority": 2, "color": (0, 165, 255)}, # BGR: Orange
    "Utility Pole": {"priority": 2, "color": (0, 165, 255)},
    "Street Light": {"priority": 2, "color": (0, 165, 255)},
    "Traffic Light - General (Upright)": {"priority": 2, "color": (0, 165, 255)},
    "Traffic Light - Pedestrians": {"priority": 2, "color": (0, 165, 255)},
    
    # Végétation
    "Vegetation": {"priority": 2, "color": (0, 200, 100)},
    
    # Signalisation
    "Traffic Sign (Front)": {"priority": 2, "color": (255, 165, 0)},
    "Traffic Sign (Back)": {"priority": 2, "color": (255, 165, 0)},
    "Traffic Sign - Direction (Front)": {"priority": 2, "color": (255, 165, 0)},
    
    # Obstacles au sol (Priorité 3: Moins critiques, encombrement)
    "Fire Hydrant": {"priority": 3, "color": (0, 255, 255)}, # BGR: Jaune
    "Bench": {"priority": 3, "color": (0, 255, 255)},
    "Bike Rack": {"priority": 3, "color": (0, 255, 255)},
    "Billboard": {"priority": 3, "color": (0, 255, 255)},
    
    # Barrières
    "Fence": {"priority": 2, "color": (0, 165, 255)},
    "Guard Rail": {"priority": 2, "color": (0, 165, 255)},
    "Wall": {"priority": 2, "color": (0, 165, 255)},
}

# Seuil d'aire minimale (en pixels) pour accepter une détection Mapillary
MIN_AREA_THRESHOLD = {
    1: 150, 
    2: 300,
    3: 250
}

# ---------------------------------------------------------
# CHARGEMENT DES MODÈLES
# ---------------------------------------------------------
print("[INFO] Chargement des modèles pour detector_module...")
# Charger YOLOv8m (Détection d'objets)
yolo_path = os.path.join(MODELS_DIR, "yolov8m.pt")
try:
    if os.path.exists(yolo_path):
        yolo = YOLO(yolo_path) # Chargement local
    else:
        print(f"[INFO] Poids YOLO absents en local. Téléchargement vers cache Ultralytics puis copie vers: {yolo_path}")
        temp_yolo = YOLO("yolov8m.pt") # Téléchargement par Ultralytics

        downloaded_path = getattr(temp_yolo, "ckpt_path", None)
        if downloaded_path and os.path.exists(downloaded_path):
            shutil.copy2(downloaded_path, yolo_path)
            yolo = YOLO(yolo_path)
            print(f"[OK] Poids YOLO copiés dans {yolo_path}")
        else:
            local_fallback = os.path.join(CURRENT_FILE_DIR, "yolov8m.pt")
            if os.path.exists(local_fallback):
                shutil.move(local_fallback, yolo_path)
                yolo = YOLO(yolo_path)
                print(f"[OK] Poids YOLO déplacés vers {yolo_path}")
            else:
                print("[WARN] Chemin de poids téléchargé non détecté, utilisation du modèle chargé en mémoire.")
                yolo = temp_yolo

        stray_local = os.path.join(CURRENT_FILE_DIR, "yolov8m.pt")
        if os.path.exists(stray_local) and os.path.abspath(stray_local) != os.path.abspath(yolo_path):
            try:
                os.remove(stray_local)
            except Exception:
                pass
except Exception as e:
    print(f"[ERREUR] Échec du chargement de YOLO: {e}")
    yolo = None # Mettre à None permet de sauter la détection si le modèle échoue

# Charger Mask2Former (Segmentation sémantique Mapillary Vistas)
try:
    MAPILLARY_MODEL = "facebook/mask2former-swin-large-mapillary-vistas-semantic"
    # Le 'processor' prépare l'image pour le modèle (normalisation, redimensionnement, etc.)
    processor = AutoImageProcessor.from_pretrained(MAPILLARY_MODEL, cache_dir=MODELS_DIR) 
    # Le modèle effectue la segmentation
    mapillary_model = Mask2FormerForUniversalSegmentation.from_pretrained(
        MAPILLARY_MODEL, 
        cache_dir=MODELS_DIR
    )
except Exception as e:
    print(f"[ERREUR] Échec du chargement de Mask2Former: {e}")
    processor = None
    mapillary_model = None

print("[OK] Modèles chargés")

# ---------------------------------------------------------
# FONCTIONS DE DÉTECTION (Inchangées)
# ---------------------------------------------------------

def non_maximum_suppression(boxes, scores, threshold=0.5):
    """ pour éliminer les boîtes redondantes après la fusion des deux modèles."""
    if len(boxes) == 0:
        return []
    
    boxes = np.array(boxes)
    scores = np.array(scores)
    
    # 1. Extraction des coordonnées des boîtes
    x1 = boxes[:, 0]
    y1 = boxes[:, 1]
    x2 = boxes[:, 2]
    y2 = boxes[:, 3]
    
    areas = (x2 - x1 + 1) * (y2 - y1 + 1)
    # Tri des détections par score décroissant
    order = scores.argsort()[::-1]
    
    keep = []
    while order.size > 0:
        i = order[0] # Prendre la boîte avec le score le plus élevé
        keep.append(i)
        
        # Calcul des coordonnées de chevauchement (Intersection)
        xx1 = np.maximum(x1[i], x1[order[1:]])
        yy1 = np.maximum(y1[i], y1[order[1:]])
        xx2 = np.minimum(x2[i], x2[order[1:]])
        yy2 = np.minimum(y2[i], y2[order[1:]])
        
        # Calcul de la surface d'intersection
        w = np.maximum(0.0, xx2 - xx1 + 1)
        h = np.maximum(0.0, yy2 - yy1 + 1)
        inter = w * h
        
        # Calcul de l'Intersection sur Union (IoU)
        ovr = inter / (areas[i] + areas[order[1:]] - inter)
        
        # Conserver les boîtes dont l'IoU est inférieur au seuil (non-chevauchantes)
        inds = np.where(ovr <= threshold)[0]
        order = order[inds + 1]
    
    return keep

def detect_obstacles_yolo(frame):
    """Détection YOLO avec classes filtrées et priorités."""
    if yolo is None:
        return []
        
    obstacles = []
    
    # Classes YOLO acceptées par le système d'obstacle et leur priorité assignée
    YOLO_OBSTACLES = {
        "person": 1, # Les personnes sont des obstacles critiques/dynamiques
        "bicycle": 2,
        "car": 2,
        "motorcycle": 2,
        "bus": 2,
        "truck": 2,
        "traffic light": 2,
        "fire hydrant": 2,
        "stop sign": 2,
        "bench": 3,
        "chair": 3,
        "potted plant": 3,
        "backpack": 3,
        "handbag": 3,
        "suitcase": 3
    }
    
    # Exécution du modèle YOLO
    results = yolo(frame, verbose=False)[0]
    
    # Extraction et filtrage des résultats
    for box in results.boxes:
        cls = int(box.cls[0])
        label = yolo.names[cls]
        conf = float(box.conf[0])
        
        # POINT DE DÉTECTION CONCRET YOLO: Filtrage par classe et confiance
        if label in YOLO_OBSTACLES and conf > 0.3:
            x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int)
            obstacles.append({
                'bbox': [int(x1), int(y1), int(x2), int(y2)],
                'class': label,
                'confidence': float(conf),
                'priority': int(YOLO_OBSTACLES[label]),
                'source': 'yolo'
            })
    
    return obstacles

def detect_obstacles_mapillary(frame):
    """Détection avec Mask2Former (Mapillary Vistas) via segmentation sémantique."""
    if mapillary_model is None or processor is None:
        return []
        
    obstacles = []
    
    # 1. Préparation de l'image (Conversion BGR -> RGB -> PIL -> Tenseur)
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    pil_image = Image.fromarray(frame_rgb)
    inputs = processor(images=pil_image, return_tensors="pt")
    
    # 2. Exécution du modèle de segmentation
    with torch.no_grad():
        outputs = mapillary_model(**inputs)
    
    # 3. Post-traitement: Obtention de la carte de segmentation (chaque pixel est un ID de classe)
    predicted_map = processor.post_process_semantic_segmentation(
        outputs, 
        target_sizes=[frame.shape[:2]]
    )[0]
    
    seg_map = predicted_map.cpu().numpy()
    id2label = mapillary_model.config.id2label
    
    # 4. Analyse des classes pertinentes (Obstacles)
    for class_id, class_name in id2label.items():
        if class_name in MAPILLARY_OBSTACLES:
            info = MAPILLARY_OBSTACLES[class_name]
            
            # Création d'un masque binaire pour la classe actuelle
            mask = (seg_map == class_id).astype(np.uint8)
            # Trouver les régions connectées (contours) de cette classe
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for cnt in contours:
                area = cv2.contourArea(cnt)
                min_area = MIN_AREA_THRESHOLD[info['priority']]
                
                # POINT DE DÉTECTION CONCRET MAPILLARY: Filtrage par aire minimale
                if area > min_area:
                    # Calcul de la boîte englobante à partir du contour
                    x, y, w, h = cv2.boundingRect(cnt)
                    
                    confidence = 0.95 # Confiance arbitrairement haute pour la segmentation
                    
                    obstacles.append({
                        'bbox': [int(x), int(y), int(x + w), int(y + h)],
                        'class': class_name,
                        'confidence': float(confidence),
                        'priority': int(info['priority']),
                        'source': 'mapillary',
                        'color': info['color']
                    })
    
    return obstacles

def merge_detections(yolo_obstacles, mapillary_obstacles):
    """Fusionne les détections des deux modèles et applique le NMS."""
    all_obstacles = yolo_obstacles + mapillary_obstacles
    
    if len(all_obstacles) == 0:
        return []
    
    boxes = [obs['bbox'] for obs in all_obstacles]
    # Pondération du score pour favoriser les priorités critiques lors du NMS
    # Priorité 1 -> Facteur (4-1)=3 ; Priorité 3 -> Facteur (4-3)=1
    scores = [obs['confidence'] * (4 - obs['priority']) for obs in all_obstacles] 
    
    # Application du NMS pour ne garder que les meilleures boîtes non-chevauchantes
    keep_indices = non_maximum_suppression(boxes, scores, threshold=0.4)
    merged = [all_obstacles[i] for i in keep_indices]
    merged.sort(key=lambda x: x['priority']) # Tri par priorité pour l'affichage
    
    return merged

def detect_obstacles_combined(frame):
    """Pipeline complet de détection (fonction appelée par l'API app.py)."""
    yolo_obs = detect_obstacles_yolo(frame)
    mapillary_obs = detect_obstacles_mapillary(frame)
    merged_obs = merge_detections(yolo_obs, mapillary_obs)
    
    return merged_obs

# ---------------------------------------------------------
# EXPORT JSON ET ANNOTATION (Adaptées)
# ---------------------------------------------------------

def export_detections_json(image_filename, obstacles):
    """Exporte les détections en JSON pour les métadonnées de sortie."""
    
    detections = {
        'image': "annotated_" + image_filename,
        'total_obstacles': len(obstacles),
        # Calcul du décompte par niveau de priorité
        'by_priority': {
            'critical': len([o for o in obstacles if o['priority'] == 1]),
            'important': len([o for o in obstacles if o['priority'] == 2]),
            'moderate': len([o for o in obstacles if o['priority'] == 3])
        },
        'detections': []
    }
    
    for obs in obstacles:
        # Conversion de la couleur BGR (OpenCV) à RGB (standard JSON/Web)
        color_bgr = obs.get('color', get_color_for_priority(obs['priority']))
        color_rgb = [int(color_bgr[2]), int(color_bgr[1]), int(color_bgr[0])] 

        detections['detections'].append({
            'class': obs['class'],
            'bbox': [int(x) for x in obs['bbox']],
            'confidence': float(obs['confidence']),
            'priority': int(obs['priority']),
            'source': obs.get('source', 'unknown'),
            'color': color_rgb # Couleur RGB pour le JSON
        })
    
    json_file_name = image_filename.replace('.jpg', '.json').replace('.png', '.json').replace('.jpeg', '.json')
    json_path = os.path.join(JSON_DIR, json_file_name) 
    
    with open(json_path, 'w') as f:
        json.dump(detections, f, indent=2)
    
    return json_path

def get_color_for_priority(priority):
    """Retourne une couleur par défaut selon la priorité (BGR pour OpenCV)."""
    colors = {
        1: (0, 0, 255),    # Rouge
        2: (0, 165, 255),  # Orange
        3: (0, 255, 255)   # Jaune
    }
    return colors.get(priority, (255, 255, 255))

def annotate_frame(frame, obstacles):
    """Dessine les boîtes englobantes et les statistiques sur l'image (pour l'utilisateur)."""
    annotated = frame.copy()
    
    stats = {1: 0, 2: 0, 3: 0}
    stats_by_source = {"yolo": 0, "mapillary": 0}
    
    for obs in obstacles:
        x1, y1, x2, y2 = obs['bbox']
        priority = obs['priority']
        label = obs['class']
        source = obs.get('source', 'unknown')
        
        # Couleur : utilise la couleur spécifique Mapillary si elle existe, sinon la couleur par défaut
        color = obs.get('color', get_color_for_priority(priority))
        
        # Épaisseur dépendante de la priorité (P1 = plus visible)
        thickness = 4 if priority == 1 else (3 if priority == 2 else 2)
        
        cv2.rectangle(annotated, (x1, y1), (x2, y2), color, thickness)
        
        text = f"{label} P{priority}"
        font_scale = 0.5
        font_thickness = 2
        
        # Affichage du texte de la détection (label + priorité)
        (text_w, text_h), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, font_scale, font_thickness)
        cv2.rectangle(annotated, (x1, y1 - text_h - 10), (x1 + text_w + 5, y1), color, -1)
        cv2.putText(annotated, text, (x1 + 2, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 
                     font_scale, (255, 255, 255), font_thickness)
        
        stats[priority] += 1
        stats_by_source[source] += 1
    
    # Affichage des statistiques sur l'image (Tableau de bord de détection)
    info_y = 30
    cv2.rectangle(annotated, (10, 10), (350, 150), (0, 0, 0), -1)
    cv2.putText(annotated, f"Obstacles critiques (P1): {stats[1]}", (20, info_y), 
                 cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
    cv2.putText(annotated, f"Obstacles importants (P2): {stats[2]}", (20, info_y + 30), 
                 cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 165, 255), 2)
    cv2.putText(annotated, f"Obstacles moderes (P3): {stats[3]}", (20, info_y + 60), 
                 cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
    
    cv2.putText(annotated, f"YOLO: {stats_by_source['yolo']} | Mapillary: {stats_by_source['mapillary']}", 
                 (20, info_y + 100), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    
    return annotated

# Les fonctions process_images() et process_videos() sont supprimées car elles ne sont plus 
# nécessaires pour l'API Flask. Le traitement est déclenché par l'appel HTTP.

# Le bloc if __name__ == "__main__": est supprimé pour que le module soit importé sans exécution.