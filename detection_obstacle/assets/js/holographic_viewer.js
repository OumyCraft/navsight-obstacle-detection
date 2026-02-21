        import * as THREE from 'three';
        import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';

        // Traduction des noms d'obstacles en français
        const FRENCH_NAMES = {
            'person': 'Personne',
            'bicycle': 'Vélo',
            'car': 'Voiture',
            'motorcycle': 'Moto',
            'bus': 'Bus',
            'truck': 'Camion',
            'traffic light': 'Feu de signalisation',
            'fire hydrant': 'Bouche d\'incendie',
            'stop sign': 'Stop',
            'bench': 'Banc',
            'chair': 'Chaise',
            'potted plant': 'Plante en pot',
            'backpack': 'Sac à dos',
            'handbag': 'Sac à main',
            'suitcase': 'Valise',
            'Manhole': 'Plaque d\'égout',
            'Curb': 'Bordure',
            'Curb Cut': 'Bateau de trottoir',
            'Pole': 'Poteau',
            'Utility Pole': 'Poteau électrique',
            'Street Light': 'Lampadaire',
            'Traffic Light - General (Upright)': 'Feu tricolore',
            'Traffic Light - Pedestrians': 'Feu piéton',
            'Vegetation': 'Végétation',
            'Traffic Sign (Front)': 'Panneau (face)',
            'Traffic Sign (Back)': 'Panneau (dos)',
            'Traffic Sign - Direction (Front)': 'Panneau directionnel',
            'Fire Hydrant': 'Borne incendie',
            'Bench': 'Banc',
            'Bike Rack': 'Parking à vélos',
            'Billboard': 'Panneau publicitaire',
            'Fence': 'Clôture',
            'Guard Rail': 'Barrière de sécurité',
            'Wall': 'Mur'
        };

        function getFrenchName(englishName) {
            return FRENCH_NAMES[englishName] || englishName;
        }

        // THREE.JS SCENE
        let scene, camera, renderer;
        let handsModel;
        let modelsLoaded = 0;
        const totalModels = 1;

        function initThreeJS() {
            document.body.classList.add('loading');
            
            scene = new THREE.Scene();
            camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
            camera.position.set(0, 0, 0);
            
            renderer = new THREE.WebGLRenderer({ 
                canvas: document.getElementById('three-canvas'),
                alpha: true,
                antialias: true
            });
            renderer.setSize(window.innerWidth, window.innerHeight);
            renderer.outputColorSpace = THREE.SRGBColorSpace;
            renderer.setClearColor(0x000000, 0);

            const ambientLight = new THREE.AmbientLight(0xffffff, 1.2);
            scene.add(ambientLight);

            const mainLight = new THREE.DirectionalLight(0xffffff, 2);
            mainLight.position.set(0, 3, 0);
            mainLight.target.position.set(0, -2, -3);
            scene.add(mainLight);
            scene.add(mainLight.target);

            const fillLight = new THREE.DirectionalLight(0xffffff, 1.5);
            fillLight.position.set(0, 0, 2);
            scene.add(fillLight);

            const pointLight1 = new THREE.PointLight(0x00ffff, 0.5);
            pointLight1.position.set(2, 2, -2);
            scene.add(pointLight1);

            const pointLight2 = new THREE.PointLight(0x00ffff, 0.3);
            pointLight2.position.set(-2, -1, -2);
            scene.add(pointLight2);

            createHolographicGrid();
            createParticles();
            updateLoadingProgress('Chargement des mains 3D...');
            loadModels();
            animate();

            window.addEventListener('resize', onWindowResize);
        }

        function createHolographicGrid() {
            const gridHelper1 = new THREE.GridHelper(30, 30, 0x00ffff, 0x00ffff);
            gridHelper1.material.opacity = 0.15;
            gridHelper1.material.transparent = true;
            gridHelper1.position.y = -3;
            scene.add(gridHelper1);

            const gridHelper2 = new THREE.GridHelper(30, 30, 0x00ffff, 0x00ffff);
            gridHelper2.material.opacity = 0.1;
            gridHelper2.material.transparent = true;
            gridHelper2.rotation.x = Math.PI / 2;
            gridHelper2.position.z = -8;
            scene.add(gridHelper2);

            const boxGeometry = new THREE.BoxGeometry(9, 5, 9);
            const boxEdges = new THREE.EdgesGeometry(boxGeometry);
            const boxLines = new THREE.LineSegments(
                boxEdges,
                new THREE.LineBasicMaterial({ color: 0x00ffff, transparent: true, opacity: 0.2 })
            );
            scene.add(boxLines);
        }

        let particles;
        function createParticles() {
            const geometry = new THREE.BufferGeometry();
            const vertices = [];
            
            for (let i = 0; i < 1500; i++) {
                vertices.push(
                    Math.random() * 20 - 10,
                    Math.random() * 15 - 7,
                    Math.random() * 20 - 10
                );
            }
            
            geometry.setAttribute('position', new THREE.Float32BufferAttribute(vertices, 3));
            
            const material = new THREE.PointsMaterial({
                color: 0x00ffff,
                size: 0.04,
                transparent: true,
                opacity: 0.6,
                blending: THREE.AdditiveBlending
            });
            
            particles = new THREE.Points(geometry, material);
            scene.add(particles);
        }

        function updateLoadingProgress(text) {
            const progressEl = document.getElementById('loading-progress');
            if (progressEl) {
                progressEl.textContent = text;
            }
        }

        function loadModels() {
            const loader = new GLTFLoader();
            
            loader.load(
                '/3Dmodels/hands.glb',
                (gltf) => {
                    updateLoadingProgress('Mains chargées avec succès !');
                    handsModel = gltf.scene;
                    handsModel.position.set(0, -1.5, -1.5);
                    handsModel.scale.set(0.8, 0.8, 0.8);
                    scene.add(handsModel);
                    onModelLoaded();
                },
                (progress) => {
                    const percent = Math.round((progress.loaded / progress.total) * 100);
                    updateLoadingProgress(`Chargement mains: ${percent}%`);
                },
                (error) => {
                    console.error('Erreur chargement mains:', error);
                    updateLoadingProgress('⚠ Erreur de chargement');
                    onModelLoaded();
                }
            );
        }

        function onModelLoaded() {
            modelsLoaded++;
            if (modelsLoaded >= totalModels) {
                updateLoadingProgress('✓ Chargement terminé');
                
                setTimeout(() => {
                    const loader = document.getElementById('loading');
                    loader.classList.add('hidden');
                    document.body.classList.remove('loading');
                    playBackgroundMusic();
                }, 500);
            }
        }

        function animate() {
            requestAnimationFrame(animate);

            const time = Date.now() * 0.001;

            scene.children.forEach((child) => {
                if (child instanceof THREE.GridHelper) {
                    child.rotation.y += 0.0005;
                }
            });

            if (particles) {
                particles.rotation.y += 0.0003;
            }

            if (handsModel) {
                handsModel.position.y = -1.5 + Math.sin(time * 0.5) * 0.05;
            }

            renderer.render(scene, camera);
        }

        function onWindowResize() {
            camera.aspect = window.innerWidth / window.innerHeight;
            camera.updateProjectionMatrix();
            renderer.setSize(window.innerWidth, window.innerHeight);
        }

        // AUDIO
        const bgMusic = document.getElementById('background-music');
        const audioControl = document.getElementById('audio-control');
        let isMusicPlaying = false;

        function playBackgroundMusic() {
            bgMusic.volume = 0.3;
            bgMusic.play()
                .then(() => {
                    isMusicPlaying = true;
                    audioControl.textContent = '🔊';
                })
                .catch(error => {
                    console.log('Autoplay bloqué:', error);
                    isMusicPlaying = false;
                    audioControl.textContent = '🔇';
                });
        }

        audioControl.addEventListener('click', () => {
            if (isMusicPlaying) {
                bgMusic.pause();
                audioControl.textContent = '🔇';
                audioControl.classList.add('muted');
                isMusicPlaying = false;
            } else {
                bgMusic.play();
                audioControl.textContent = '🔊';
                audioControl.classList.remove('muted');
                isMusicPlaying = true;
            }
        });

        // SYSTÈME DE NOTIFICATIONS
        function showNotification(title, content, icon = '🔍') {
            const container = document.getElementById('notifications-container');
            const notif = document.createElement('div');
            notif.className = 'notification';
            notif.innerHTML = `
                <div style="display: flex; align-items: center;">
                    <span class="notification-icon">${icon}</span>
                    <div>
                        <div class="notification-title">${title}</div>
                        <div class="notification-content">${content}</div>
                    </div>
                </div>
            `;
            container.appendChild(notif);
            
            setTimeout(() => {
                notif.remove();
            }, 4000);
        }

        // SYSTÈME DE DÉTECTION
        let detectionData = null;
        let canvas, ctx;
        let detectedObstacles = { 1: {}, 2: {}, 3: {} };
        const audioContext = new (window.AudioContext || window.webkitAudioContext)();

        function playBeep(freq, duration) {
            const osc = audioContext.createOscillator();
            const gain = audioContext.createGain();
            osc.connect(gain);
            gain.connect(audioContext.destination);
            osc.frequency.value = freq;
            osc.type = 'sine';
            gain.gain.setValueAtTime(0.08, audioContext.currentTime);
            gain.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + duration / 1000);
            osc.start(audioContext.currentTime);
            osc.stop(audioContext.currentTime + duration / 1000);
        }

        async function fetchImageList() {
            try {
                const response = await fetch('/api/images');
                const data = await response.json();
                displayImageList(data.images);
            } catch (error) {
                console.error('Erreur chargement images:', error);
                document.getElementById('loading-images').textContent = '⚠ Erreur de connexion';
            }
        }

        function displayImageList(images) {
            const container = document.getElementById('image-list');
            const loadingDiv = document.getElementById('loading-images');
            
            if (images.length === 0) {
                loadingDiv.textContent = 'Aucune image trouvée';
                return;
            }
            
            loadingDiv.remove();
            
            images.sort((a, b) => {
                const numA = parseInt(a.match(/\d+/)?.[0] || 0);
                const numB = parseInt(b.match(/\d+/)?.[0] || 0);
                return numA - numB;
            });
            
            images.forEach((filename) => {
                const btn = document.createElement('button');
                btn.className = 'file-button';
                btn.textContent = `▸ ${filename}`;
                btn.onclick = () => scanImage(filename);
                container.appendChild(btn);
            });
        }

        async function scanImage(filename) {
            document.querySelectorAll('.file-button').forEach(b => b.disabled = true);
            
            // Réinitialiser les tooltips et les données
            detectedObstacles = { 1: {}, 2: {}, 3: {} };
            updateTooltips();
            
            document.getElementById('instructions').classList.add('hidden');
            document.getElementById('current-file').textContent = filename;
            
            showMessage('INITIALISATION DU SCAN...');
            playBeep(800, 200);
            
            try {
                const response = await fetch(`/api/detect/${filename}`, { method: 'POST' });
                detectionData = await response.json();
                
                if (detectionData.error) {
                    showMessage('⚠ ERREUR: ' + detectionData.error);
                    setTimeout(hideMessage, 3000);
                    document.querySelectorAll('.file-button').forEach(b => b.disabled = false);
                    return;
                }
                
                await displayOriginalImage(filename);
                updateStats(detectionData);
                await animateScan(detectionData);
                
                playBeep(1200, 300);
                showMessage('✓ SCAN TERMINÉ');
                setTimeout(() => {
                    hideMessage();
                    document.querySelectorAll('.file-button').forEach(b => b.disabled = false);
                }, 2000);
                
            } catch (error) {
                console.error('Erreur scan:', error);
                showMessage('⚠ ÉCHEC DU SCAN');
                setTimeout(hideMessage, 3000);
                document.querySelectorAll('.file-button').forEach(b => b.disabled = false);
            }
        }

        async function displayOriginalImage(filename) {
            return new Promise((resolve) => {
                const imgEl = document.getElementById('detection-image');
                imgEl.onload = () => {
                    imgEl.classList.add('visible');
                    
                    canvas = document.getElementById('detection-canvas');
                    ctx = canvas.getContext('2d');
                    canvas.width = imgEl.naturalWidth;
                    canvas.height = imgEl.naturalHeight;
                    canvas.style.width = imgEl.offsetWidth + 'px';
                    canvas.style.height = imgEl.offsetHeight + 'px';
                    
                    setTimeout(resolve, 500);
                };
                imgEl.src = `/ressources/images/${filename}`;
            });
        }

        function updateStats(data) {
            document.getElementById('obstacles-count').textContent = '0';
            document.getElementById('critical-count').textContent = '0';
            document.getElementById('important-count').textContent = '0';
            document.getElementById('moderate-count').textContent = '0';
        }

        function updateStatsProgress(scannedCount, data) {
            document.getElementById('obstacles-count').textContent = scannedCount + ' / ' + data.total_obstacles;
            
            const scannedDetections = data.detections.slice(0, scannedCount);
            const critical = scannedDetections.filter(d => d.priority === 1).length;
            const important = scannedDetections.filter(d => d.priority === 2).length;
            const moderate = scannedDetections.filter(d => d.priority === 3).length;
            
            document.getElementById('critical-count').textContent = critical;
            document.getElementById('important-count').textContent = important;
            document.getElementById('moderate-count').textContent = moderate;
        }

        function updateTooltips() {
            // Tooltip pour critiques
            const criticalTooltip = document.getElementById('critical-tooltip');
            const criticalObstacles = detectedObstacles[1];
            if (Object.keys(criticalObstacles).length === 0) {
                criticalTooltip.innerHTML = '<div class="stat-tooltip-empty">Aucun obstacle critique détecté</div>';
            } else {
                let html = '<div class="stat-tooltip-title">Obstacles Critiques</div>';
                for (let [name, count] of Object.entries(criticalObstacles)) {
                    html += `<div class="stat-tooltip-item"><span>${getFrenchName(name)}</span><span>${count}</span></div>`;
                }
                criticalTooltip.innerHTML = html;
            }
            
            // Tooltip pour importants
            const importantTooltip = document.getElementById('important-tooltip');
            const importantObstacles = detectedObstacles[2];
            if (Object.keys(importantObstacles).length === 0) {
                importantTooltip.innerHTML = '<div class="stat-tooltip-empty">Aucun obstacle important détecté</div>';
            } else {
                let html = '<div class="stat-tooltip-title">Obstacles Importants</div>';
                for (let [name, count] of Object.entries(importantObstacles)) {
                    html += `<div class="stat-tooltip-item"><span>${getFrenchName(name)}</span><span>${count}</span></div>`;
                }
                importantTooltip.innerHTML = html;
            }
            
            // Tooltip pour modérés
            const moderateTooltip = document.getElementById('moderate-tooltip');
            const moderateObstacles = detectedObstacles[3];
            if (Object.keys(moderateObstacles).length === 0) {
                moderateTooltip.innerHTML = '<div class="stat-tooltip-empty">Aucun obstacle modéré détecté</div>';
            } else {
                let html = '<div class="stat-tooltip-title">Obstacles Modérés</div>';
                for (let [name, count] of Object.entries(moderateObstacles)) {
                    html += `<div class="stat-tooltip-item"><span>${getFrenchName(name)}</span><span>${count}</span></div>`;
                }
                moderateTooltip.innerHTML = html;
            }
        }

        async function animateScan(data) {
            hideMessage();
            
            const groupedByClass = {};
            data.detections.forEach((det) => {
                if (!groupedByClass[det.class]) {
                    groupedByClass[det.class] = [];
                }
                groupedByClass[det.class].push(det);
            });
            
            let scannedCount = 0;
            
            for (let className in groupedByClass) {
                const group = groupedByClass[className];
                const count = group.length;
                const priority = group[0].priority;
                
                // Ajouter au dictionnaire des obstacles
                if (!detectedObstacles[priority][className]) {
                    detectedObstacles[priority][className] = 0;
                }
                detectedObstacles[priority][className] += count;
                
                // Afficher la notification
                const frenchName = getFrenchName(className);
                showNotification(
                    `✓ ${frenchName}`,
                    `${count} ${count > 1 ? 'détecté(e)s' : 'détecté(e)'}`,
                    priority === 1 ? '🚨' : (priority === 2 ? '⚠️' : 'ℹ️')
                );
                
                await Promise.all(group.map(det => scanObstacle(det)));
                scannedCount += group.length;
                updateStatsProgress(scannedCount, data);
                updateTooltips();
                await sleep(300);
            }
        }

        async function scanObstacle(det) {
            const [x1, y1, x2, y2] = det.bbox;
            const w = x2 - x1;
            const h = y2 - y1;
            const color = `rgb(${det.color[0]}, ${det.color[1]}, ${det.color[2]})`;
            
            playBeep(1000 + det.priority * 200, 150);
            await animateBox(x1, y1, w, h, color);
            await typeLabel(x1, y1, det.class, color);
        }

        async function animateBox(x, y, w, h, color) {
            for (let i = 0; i <= 25; i++) {
                ctx.strokeStyle = color;
                ctx.lineWidth = 3;
                ctx.shadowBlur = 0;
                ctx.globalAlpha = 1;
                ctx.strokeRect(x, y, w, h);
                
                const cornerSize = 15;
                ctx.lineWidth = 4;
                drawCorners(x, y, w, h, cornerSize);

                await sleep(20);
            }
        }

        function drawCorners(x, y, w, h, size) {
            ctx.beginPath();
            ctx.moveTo(x, y + size);
            ctx.lineTo(x, y);
            ctx.lineTo(x + size, y);
            ctx.stroke();
            
            ctx.beginPath();
            ctx.moveTo(x + w - size, y);
            ctx.lineTo(x + w, y);
            ctx.lineTo(x + w, y + size);
            ctx.stroke();
            
            ctx.beginPath();
            ctx.moveTo(x, y + h - size);
            ctx.lineTo(x, y + h);
            ctx.lineTo(x + size, y + h);
            ctx.stroke();
            
            ctx.beginPath();
            ctx.moveTo(x + w - size, y + h);
            ctx.lineTo(x + w, y + h);
            ctx.lineTo(x + w, y + h - size);
            ctx.stroke();
        }

        async function typeLabel(x, y, text, color) {
            const chars = text.split('');
            for (let i = 0; i <= chars.length; i++) {
                ctx.font = 'bold 16px Courier New';
                const currentText = i < chars.length ? chars.slice(0, i + 1).join('') + '_' : text;
                const metrics = ctx.measureText(currentText);
                
                ctx.fillStyle = 'rgba(0,0,0,0.95)';
                ctx.fillRect(x, y - 28, metrics.width + 12, 22);
                ctx.strokeStyle = color;
                ctx.lineWidth = 2;
                ctx.strokeRect(x, y - 28, metrics.width + 12, 22);
                ctx.fillStyle = color;
                ctx.shadowBlur = 8;
                ctx.shadowColor = color;
                ctx.fillText(currentText, x + 6, y - 10);
                ctx.shadowBlur = 0;
                
                if (i < chars.length) playBeep(600, 40);
                await sleep(60);
            }
        }

        function showMessage(text) {
            const msg = document.getElementById('system-message');
            msg.textContent = text;
            msg.classList.add('visible');
        }

        function hideMessage() {
            document.getElementById('system-message').classList.remove('visible');
        }

        function sleep(ms) {
            return new Promise(r => setTimeout(r, ms));
        }

        initThreeJS();
        fetchImageList();

        document.getElementById('holo-check').addEventListener('change', function(e) {
            const imageList = document.getElementById('image-list');
            if (e.target.checked) {
                imageList.classList.add('visible');
                playBeep(1200, 200);
            } else {
                imageList.classList.remove('visible');
                playBeep(800, 200);
            }
        });