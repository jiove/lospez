// Animazione stellare di sfondo basata su Three.js
document.addEventListener('DOMContentLoaded', () => {
    // Configurazione della scena
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
    camera.position.z = 15;

    // Renderer
    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(window.innerWidth, window.innerHeight);
    renderer.setClearColor(0x000000, 1);
    
    // Aggiungi il renderer al DOM
    const starsBackground = document.getElementById('stars-background');
    starsBackground.appendChild(renderer.domElement);
    
    // Crea le stelle
    const starsGeometry = new THREE.BufferGeometry();
    const starsMaterial = new THREE.PointsMaterial({
        color: 0xffffff,
        size: 0.05,
        transparent: true,
        blending: THREE.AdditiveBlending
    });
    
    // Genera posizioni casuali per le stelle
    const starsCount = 5000;
    const starsPositions = new Float32Array(starsCount * 3);
    
    for (let i = 0; i < starsCount * 3; i += 3) {
        starsPositions[i] = (Math.random() - 0.5) * 40;
        starsPositions[i + 1] = (Math.random() - 0.5) * 40;
        starsPositions[i + 2] = (Math.random() - 0.5) * 40;
    }
    
    starsGeometry.setAttribute('position', new THREE.BufferAttribute(starsPositions, 3));
    
    // Crea il sistema di particelle
    const stars = new THREE.Points(starsGeometry, starsMaterial);
    scene.add(stars);
    
    // Aggiungi nebbia per dare profondità
    scene.fog = new THREE.Fog(0x000000, 0, 40);
    
    // Aggiungi luce ambientale
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.5);
    scene.add(ambientLight);
    
    // Funzione di animazione
    function animate() {
        requestAnimationFrame(animate);
        
        // Ruota lentamente le stelle
        stars.rotation.x -= 0.0005;
        stars.rotation.y -= 0.0007;
        
        // Rendering della scena
        renderer.render(scene, camera);
    }
    
    // Gestisci il ridimensionamento della finestra
    window.addEventListener('resize', () => {
        camera.aspect = window.innerWidth / window.innerHeight;
        camera.updateProjectionMatrix();
        renderer.setSize(window.innerWidth, window.innerHeight);
    });
    
    // Avvia l'animazione
    animate();
});
