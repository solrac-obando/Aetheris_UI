# 🏛️ Propuesta de Arquitectura: Aetheris M3 (ECS)

El paso de **POO (Programación Orientada a Objetos)** a **ECS (Entity Component System)** permitirá a Aetheris cruzar la barrera de los **150,000 elementos** a 60 FPS delegando la gestión de datos a arrays contiguos en memoria.

## 1. Conceptos Fundamentales

### A. Entity (La Identidad)
Una entidad ya no es una clase `DifferentialElement`. Es simplemente un **ID entero (uint32)**.
*   **Ejemplo:** `EntityID: 1024`

### B. Component (Los Datos)
Los componentes son structs puros o fragmentos de arrays de NumPy. No contienen lógica.
```python
# Component Arrays (EntityManager)
pos_x = np.array([...], dtype=np.float32)
pos_y = np.array([...], dtype=np.float32)
vel_x = np.array([...], dtype=np.float32)
color = np.array([...], dtype=np.float32) # RGBA empaquetado
```

### C. System (La Lógica)
Los sistemas son funciones que iteran sobre "Queries" de entidades que poseen ciertos componentes.
```python
def physics_system(entities, dt):
    # Kernel Numba que opera solo sobre los arrays de posición y velocidad
    apply_gravity_kernel[blocks, threads](pos_x, pos_y, vel_x, vel_y, dt)
```

---

## 2. Estructura de Datos Propuesta

| Componente | Datos | Almacenamiento |
|---|---|---|
| **Transform** | x, y, w, h | `batch_states` (NumPy f4) |
| **Motion** | vx, vy, ax, ay | `batch_velocities` (NumPy f4) |
| **AetherAsymptote** | tx, ty, tw, th | `batch_targets` (NumPy f4) |
| **Visual** | r, g, b, a, z | `batch_styles` (NumPy f4 + i4) |
| **Metadata** | JSON strings | `Dict[int, str]` (Fuera del loop crítico) |

---

## 3. Ejemplo de Flujo de Trabajo (Tick ECS)

1.  **Input Collection:** Se actualizan los componentes `Force` de las entidades tocadas.
2.  **Asymptote Calculation:** Sistema paralelo que actualiza `batch_targets`.
3.  **Physics Integration:** Un solo kernel masivo que procesa `States + Velocities + Forces`.
4.  **Boundary System:** Aplica colisiones de bordes sobre los arrays.
5.  **Render Bridge:** El array `batch_states` se pasa directamente a WebGL o Kivy (zero-allocation).

---

## 4. Configuración Necesaria

Para habilitar M3, se requiere una configuración de "Pool de Memoria":
```python
# engine_config.json
{
    "ecs_enabled": true,
    "initial_pool_size": 50000,
    "batch_size": 256,
    "growth_factor": 1.5,
    "use_rust_backend": true
}
```

---

## 5. Prevención de "Breaking Changes" (The Bridge Pattern)

Para no romper el proyecto actual, implementaremos una **Capa de Emulación (Proxy)**:
- La clase `DifferentialElement` se convierte en un "Handle" o puntero a un ID en el ECS.
- Cada vez que se crea un objeto, el motor le asigna un slot en los arrays globales.
- Las propiedades `.x`, `.y` del objeto se convierten en getters/setters que acceden directamente al array de NumPy mediante el ID de la identidad.

Esto permite que el código actual siga funcionando mientras el core del motor corre en modo ECS puro.
