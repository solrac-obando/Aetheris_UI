# Plan: Aetheris UI en la Web — Motor Rust WASM

## Contexto Actual

| Plataforma | Límite 60fps | Problema |
|-----------|-------------|----------|
| **Rust nativo (desktop)** | ~49,400 elementos | ✅ Sin problemas |
| **Python nativo (desktop)** | ~2,100 elementos | ⚠️ Aceptable para UIs normales |
| **Web Pyodide (Python→WASM)** | ~700-1,000 elementos | ❌ Cuello de botella: NumPy en WASM es 2-3x más lento |

**El problema**: Pyodide ejecuta Python en WASM con un overhead de 3-5x. NumPy funciona pero no está optimizado para SIMD. El motor Python puro es 5-10x más lento en web.

**La solución**: Compilar el motor Rust directamente a WASM, eliminando la capa Python del navegador.

---

## Opción 1: Rust WASM + Canvas 2D (MVP)

### Complejidad: ⭐⭐ (2-3 semanas)

### Qué se hace
- Compilar `aether-core` + `aether-math` a WASM con `wasm-pack`
- Crear un JavaScript wrapper mínimo que conecte el motor WASM con Canvas 2D
- El motor corre a ~60fps con **7,000-15,000 elementos** en el navegador
- Sin framework JS — vanilla JS + Canvas API

### Arquitectura
```
┌──────────────────────────────────────────────┐
│                  Navegador                    │
│                                              │
│  ┌─────────────┐    ┌────────────────────┐  │
│  │  Canvas 2D  │◄───│  Rust WASM Engine  │  │
│  │  (render)   │    │  (aether-core)     │  │
│  └─────────────┘    │  - Vec4            │  │
│                     │  - Solver          │  │
│  ┌─────────────┐    │  - StateTensor     │  │
│  │  Event Loop │───►│  - InputManager    │  │
│  │  (pointer)  │    └────────────────────┘  │
│  └─────────────┘                             │
└──────────────────────────────────────────────┘
```

### Puertas que se abren
| Oportunidad | Impacto |
|------------|---------|
| **Dashboards web ligeros** | Visualización de datos en tiempo real sin servidor |
| **Embeddable widget** | Un `<script>` de ~500KB que cualquier web puede usar |
| **Sin dependencias JS** | No React, no Vue, no build tools — solo WASM + Canvas |
| **Compatible con cualquier framework** | Se integra en React, Angular, Vue, Svelte como componente |
| **Demo técnica convincente** | Un solo HTML que muestra 10K elementos a 60fps |

### Limitaciones
- Canvas 2D tiene límite de ~50K elementos antes de saturar el GPU del navegador
- Sin texturas de texto avanzadas (solo `fillText`)
- Sin aceleración GPU avanzada (SDF shaders)

### Estimación de rendimiento web
| Elementos | FPS estimado |
|-----------|-------------|
| 1,000 | 60 fps |
| 5,000 | 60 fps |
| 10,000 | 45-60 fps |
| 15,000 | 30-45 fps |

---

## Opción 2: Rust WASM + WebGL2 + SDF Text (Producción)

### Complejidad: ⭐⭐⭐⭐ (4-6 semanas)

### Qué se hace
- Todo lo de la Opción 1, PLUS:
- Renderer WebGL2 con SDF (Signed Distance Field) shaders para texto nítido
- Texturas de texto rasterizadas en el worker y subidas como atlas
- Web Worker para el motor (no bloquea el main thread)
- SharedArrayBuffer para comunicación zero-copy entre worker y renderer
- COOP/COEP headers para habilitar SharedArrayBuffer

### Arquitectura
```
┌──────────────────────────────────────────────────────────────┐
│                        Navegador                              │
│                                                               │
│  ┌─────────────────┐         ┌──────────────────────────┐   │
│  │   Main Thread   │         │      Web Worker          │   │
│  │                 │         │                          │   │
│  │  ┌───────────┐  │  SAB    │  ┌────────────────────┐  │   │
│  │  │  WebGL2   │◄─┼─────────┼──│  Rust WASM Engine  │  │   │
│  │  │  (render) │  │  zero   │  │  (aether-core)     │  │   │
│  │  │  + SDF    │  │  copy   │  │  - Batch parallel  │  │   │
│  │  │  shaders  │  │         │  │  - NaN sanitize    │  │   │
│  │  └─────────┬─┘  │         │  └────────────────────┘  │   │
│  │            │    │         │                          │   │
│  │  ┌────────▼─┐  │         │  ┌────────────────────┐  │   │
│  │  │  Event   │  │         │  │  Texture Atlas     │  │   │
│  │  │  Handler │──┼─────────┼──│  (Pillow→WASM)     │  │   │
│  │  │  (touch) │  │         │  └────────────────────┘  │   │
│  │  └─────────┘  │         │                          │   │
│  └─────────────────┘         └──────────────────────────┘   │
└──────────────────────────────────────────────────────────────┘
SAB = SharedArrayBuffer (requiere COOP/COEP headers)
```

### Puertas que se abren
| Oportunidad | Impacto |
|------------|---------|
| **SaaS de dashboards** | Producto comercial: dashboards físicos como servicio |
| **Herramienta de diseño** | Figma-like pero con física — diseñadores pagan por esto |
| **Visualización de IA** | Embeddings de 100K+ puntos interactivos en el navegador |
| **Juegos 2D ligeros** | Motor de UI para juegos web con física orgánica |
| **Educación interactiva** | Simulaciones de física que los estudiantes pueden manipular |
| **Integración con LLMs** | Visualización de cadenas de pensamiento como grafos físicos |
| **PWA offline** | Funciona sin internet una vez cargado |

### Limitaciones
- Requiere servidor con headers COOP/COEP (configuración simple)
- Safari tiene limitaciones con SharedArrayBuffer (mejoró en v15.4+)
- Tamaño del bundle: ~800KB-1.2MB (WASM + JS + shaders)

### Estimación de rendimiento web
| Elementos | FPS estimado |
|-----------|-------------|
| 5,000 | 60 fps |
| 15,000 | 60 fps |
| 30,000 | 45-60 fps |
| 50,000 | 25-40 fps |

---

## Opción 3: Rust WASM + GPU Compute + Ecosistema (Plataforma)

### Complejidad: ⭐⭐⭐⭐⭐ (8-12 semanas)

### Qué se hace
- Todo lo de la Opción 2, PLUS:
- WebGPU para compute shaders (física en el GPU, no CPU)
- Plugin system en WASM para extensiones custom
- CLI para generar proyectos web (`aether init --web`)
- NPM package (`@aetheris/engine`) para integración con cualquier framework
- React/Vue/Svelte components oficiales
- Editor visual web (drag & drop con preview en tiempo real)
- Sistema de temas y animaciones declarativas
- Exportar layouts a JSON/CSS

### Arquitectura
```
┌──────────────────────────────────────────────────────────────────────┐
│                           Navegador                                   │
│                                                                       │
│  ┌──────────────────────────────────────────────────────────────────┐│
│  │                        WebGPU Pipeline                            ││
│  │                                                                  ││
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐ ││
│  │  │  Compute    │  │  Render     │  │  Post-Processing        │ ││
│  │  │  Shader     │──│  Shader     │──│  (bloom, motion blur)   │ ││
│  │  │  (physics)  │  │  (SDF+UI)   │  │                         │ ││
│  │  └──────┬──────┘  └──────┬──────┘  └─────────────────────────┘ ││
│  │         │                │                                     ││
│  └─────────┼────────────────┼─────────────────────────────────────┘│
│            │                │                                       │
│  ┌─────────▼────────────────▼─────────────────────────────────────┐│
│  │                    Rust WASM Core                               ││
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐││
│  │  │  aether-    │  │  Plugin     │  │  State Manager          │││
│  │  │  math       │  │  System     │  │  (undo/redo, history)   │││
│  │  └─────────────┘  └─────────────┘  └─────────────────────────┘││
│  └─────────────────────────────────────────────────────────────────┘│
│                                                                       │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │                    Framework Layer                                ││
│  │  React Component │ Vue Component │ Svelte Component │ Vanilla JS ││
│  └─────────────────────────────────────────────────────────────────┘│
└──────────────────────────────────────────────────────────────────────┘
```

### Puertas que se abren
| Oportunidad | Impacto |
|------------|---------|
| **Plataforma de visualización** | Competidor de D3.js pero con física — mercado de $2B+ |
| **Editor visual SaaS** | Canva para dashboards — suscripción mensual |
| **Framework UI alternativo** | "React pero con física" — nicho de desarrolladores |
| **Motor para game engines** | Exportar a Unity/Godot como plugin de UI |
| **Metaverso/3D** | UI física para entornos WebXR/Three.js |
| **Enterprise contracts** | Licencias para empresas que necesiten dashboards custom |
| **Open-source community** | GitHub stars → contribuciones → ecosistema |
| **Adquisición** | Figma, Vercel, o Datadog podrían adquirir el proyecto |

### Limitaciones
- WebGPU no está en todos los navegadores (Firefox lo habilitó en v127, Safari en v17)
- Complejidad de mantenimiento significativa
- Necesita equipo dedicado o comunidad activa

### Estimación de rendimiento web
| Elementos | FPS estimado |
|-----------|-------------|
| 10,000 | 60 fps |
| 50,000 | 60 fps |
| 100,000 | 45-60 fps |
| 200,000 | 25-40 fps |

---

## Comparación de Opciones

| Criterio | Opción 1 | Opción 2 | Opción 3 |
|----------|----------|----------|----------|
| **Complejidad** | ⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Tiempo** | 2-3 semanas | 4-6 semanas | 8-12 semanas |
| **Elementos 60fps** | ~10,000 | ~30,000 | ~100,000 |
| **Bundle size** | ~500KB | ~1.2MB | ~2MB |
| **Valor comercial** | Demo técnica | Producto SaaS | Plataforma |
| **Inversión necesaria** | 1 dev | 1-2 devs | Equipo completo |
| **Riesgo técnico** | Bajo | Medio | Alto |
| **Retorno potencial** | $0-$5K | $10K-$50K/año | $100K+/año |

---

## Recomendación

**Empezar con Opción 1** como prueba de concepto:
1. Compilar `aether-math` + `aether-core` a WASM con `wasm-pack`
2. Crear un HTML de demostración con Canvas 2D
3. Medir rendimiento real en navegadores (no estimado)
4. Si los números son buenos → invertir en Opción 2

**No saltar a Opción 3** sin validar que:
- Hay demanda real del mercado
- El rendimiento de Opción 1 y 2 es comprobable
- Hay recursos para mantener un ecosistema

---

## Próximos Pasos (cuando se decida implementar)

1. `cargo install wasm-pack`
2. Crear `aetheris-rust/crates/aether-wasm/` con `crate-type = ["cdylib"]`
3. Configurar `wasm-pack build --target web`
4. Crear `demo/web/index.html` con Canvas 2D
5. Benchmark en Chrome, Firefox, Safari

---

*Documento creado: 2026-04-06*
*Estado: Plan registrado, pendiente de implementación*
