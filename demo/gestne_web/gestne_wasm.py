import numpy as np
import json

# JS interop (Pyodide)
try:
    from js import Float32Array
    _HAS_PYODIDE = True
except ImportError:
    _HAS_PYODIDE = False
    Float32Array = None

# Constants
DAMPING = 0.95
GRAVITY = 6000.0
CENTER_PULL = 0.005
MAX_SPEED = 15.0

class PatientNode:
    def __init__(self, x, y, cluster, imc, insu, id_label):
        self.x = float(x)
        self.y = float(y)
        self.vx = 0.0
        self.vy = 0.0
        self.cluster = int(cluster)
        self.imc = float(imc)
        self.insu = float(insu)
        self.id_label = id_label
        # Mass based on BMI
        self.mass = max(1.0, self.imc / 20.0)
        # Radius based on BMI
        self.radius = max(5.0, self.imc / 4.0)

class GestneWASMEngine:
    def __init__(self, patients_json):
        self.nodes = []
        data = json.loads(patients_json)
        
        # Centroids for attraction
        self.centroids = {
            1: [400, 450], # Metabolic
            2: [1000, 450] # Reproductive
        }
        
        for i, p in enumerate(data):
            # Initial random positions
            x = 700 + (np.random.random() - 0.5) * 400
            y = 450 + (np.random.random() - 0.5) * 400
            
            self.nodes.append(PatientNode(
                x=x, y=y,
                cluster=p.get('Cluster_Cuantitativo', 1),
                imc=p.get('IMC', 25.0),
                insu=p.get('Insu basal', 10.0),
                id_label=p.get('Unnamed: 1', f'P{i}')
            ))
            
        self._buf = np.zeros(len(self.nodes) * 5, dtype=np.float32)

    def set_canvas_size(self, w, h):
        self.centroids[1] = [w * 0.3, h * 0.5]
        self.centroids[2] = [w * 0.7, h * 0.5]

    def tick(self, mouse_x, mouse_y, mode="attract"):
        n = len(self.nodes)
        for i, node in enumerate(self.nodes):
            fx, fy = 0.0, 0.0
            
            # 1. Cluster Attraction (Scientific core)
            target = self.centroids[node.cluster]
            dx = target[0] - node.x
            dy = target[1] - node.y
            dist = np.sqrt(dx*dx + dy*dy) + 1.0
            
            # Spring-like force to centroid
            stiffness = 0.002
            fx += dx * stiffness
            fy += dy * stiffness
            
            # 2. Mouse Interaction
            if mouse_x > 0:
                mdx = mouse_x - node.x
                mdy = mouse_y - node.y
                mdist_sq = mdx*mdx + mdy*mdy + 100.0
                m_force = GRAVITY * node.mass / mdist_sq
                mdist = np.sqrt(mdist_sq)
                
                if mode == "attract":
                    fx += m_force * mdx / mdist
                    fy += m_force * mdy / mdist
                elif mode == "repel":
                    fx -= m_force * mdx / mdist
                    fy -= m_force * mdy / mdist

            # 3. Vibration based on Insulin (Visual cue)
            jitter = (node.insu / 30.0) * 0.5
            fx += (np.random.random() - 0.5) * jitter
            fy += (np.random.random() - 0.5) * jitter

            # Integrate
            node.vx = (node.vx + fx) * DAMPING
            node.vy = (node.vy + fy) * DAMPING
            
            speed = np.sqrt(node.vx**2 + node.vy**2)
            if speed > MAX_SPEED:
                node.vx *= MAX_SPEED / speed
                node.vy *= MAX_SPEED / speed
                
            node.x += node.vx
            node.y += node.vy

            # Pack buffer: [x, y, radius, cluster, speed]
            self._buf[i*5] = node.x
            self._buf[i*5 + 1] = node.y
            self._buf[i*5 + 2] = node.radius
            self._buf[i*5 + 3] = float(node.cluster)
            self._buf[i*5 + 4] = speed

        if _HAS_PYODIDE:
            return Float32Array.new(self._buf)
        return self._buf

# Instance global for JS
EngineInstance = None

def init_engine(json_str):
    global EngineInstance
    EngineInstance = GestneWASMEngine(json_str)
    return True
