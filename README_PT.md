# Aetheris UI

> **Física-como-UI** — O primeiro motor de interface de usuário de alto desempenho impulsionado por álgebra linear para Python e WebAssembly.

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Licença: MIT](https://img.shields.io/badge/Licença-MIT-green.svg)](LICENSE)
[![Testes](https://img.shields.io/badge/testes-31%20aprovados-brightgreen.svg)](tests/)

O Aetheris UI trata o layout de interface de usuário como um **sistema físico dinâmico** governado pelas leis da mecânica clássica. Em vez de regras de posicionamento estáticas, cada elemento da UI é uma partícula com posição, velocidade e aceleração — evoluindo através de **integração de Euler** com forças restauradoras da **Lei de Hooke**, **amortecimento crítico** e **limitação por norma L2** para estabilidade numérica.

A mesma lógica física em Python impulsiona **três pipelines de renderização nativos**: HTML5 Canvas via Pyodide/WASM, OpenGL desktop via ModernGL, e mobile via Kivy — todos consumindo a mesma ponte de dados NumPy estruturado.

---

## Índice

- [Recursos](#recursos)
- [Instalação](#instalação)
- [Início Rápido](#início-rápido)
- [A Trindade do Multi-Renderizador](#a-trindade-do-multi-renderizador)
- [Resumo da Arquitetura](#resumo-da-arquitetura)
- [Fundamentos Matemáticos](#fundamentos-matemáticos)
- [Referência da API](#referência-da-api)
- [Contribuindo](#contribuindo)
- [Licença](#licença)

---

## Recursos

- **Layout Impulsionado por Física** — Cada elemento é uma partícula com estado, velocidade e aceleração. Transições de UI são sistemas massa-mola, não animações CSS.
- **Três Renderizadores Nativos** — Um motor de física, três backends de renderização:
  - **Web**: Pyodide/WASM → HTML5 Canvas 2D + sobreposição DOM (pronto para PWA)
  - **Desktop**: ModernGL com shaders SDF + texturas de texto Pillow
  - **Mobile**: Kivy com inversão do eixo Y + labels híbridos
- **Segurança Aether-Guard** — Limitação por norma L2, divisão protegida por épsilon, detecção de NaN/Inf, e a Regra dos 99% (Ajuste por Épsilon) previnem explosões numéricas.
- **Ponte Aether-Data** — População de elementos UI de bancos de dados SQLite ou PostgreSQL com normalização Min-Max automática e visualização de embeddings de IA.
- **UI Impulsionada por Servidor** — Definições de Intenção JSON compiladas em coeficientes de física em tempo de execução via TensorCompiler.
- **Hiper-Amortecimento** — Absorção automática de choques quando as dimensões da janela mudam drasticamente (>200px), prevenindo o overshoot cinético da Lei de Hooke.
- **Composição de Texto Híbrida** — Texto renderizado no Canvas (rápido, não selecionável) e sobreposições de labels DOM/Kivy (selecionáveis, acessíveis) coexistem na mesma cena.
- **Gerenciamento de Memória Sem Vazamentos** — Objetos PyProxy destruídos a cada frame no WASM; caches de texturas no ModernGL; reciclagem de nós DOM no Kivy.

---

## Instalação

### Pré-requisitos

- Python 3.12+
- NumPy 1.26.4+
- Para WASM: Um navegador moderno com suporte a SharedArrayBuffer (requer cabeçalhos COOP/COEP)

### Desktop (Renderizador ModernGL)

```bash
git clone https://github.com/your-org/aetheris-ui.git
cd aetheris-ui
pip install -r requirements.txt

# Executar com renderizador GPU (validação headless)
xvfb-run -a python3 main.py --gl --frames 50

# Executar com renderizador de depuração Tkinter
python3 main.py --tkinter

# Executar com MockRenderer (headless, sem display)
python3 main.py
```

### Web (Renderizador Pyodide/WASM)

```bash
# Iniciar o servidor Flask com suporte PWA
python3 app_server.py

# Abrir no navegador
# http://localhost:5000/
```

O servidor Flask serve o manifesto PWA, o Service Worker, e injeta o JSON de Intenção de UI. O navegador carrega o Pyodide (~15MB), monta os arquivos Python do núcleo no sistema de arquivos virtual, e executa o motor de física a 60 FPS.

### Mobile (Renderizador Kivy)

```bash
# Executar com renderizador Kivy
python3 main.py --kivy
```

O Kivy gerencia o loop de eventos, o desenho do canvas, e a inversão de coordenadas do eixo Y automaticamente.

### Docker

```bash
docker build -t aetheris-ui .
docker run --rm aetheris-ui
```

---

## Início Rápido

### Olá Física

```python
from core.engine import AetherEngine
from core.elements import SmartPanel
from core.renderer_base import MockRenderer

# 1. Criar o motor de física
engine = AetherEngine()

# 2. Registrar um painel responsivo (5% de margem de todas as bordas)
panel = SmartPanel(color=(0.9, 0.2, 0.6, 0.8), z=0)
engine.register_element(panel)

# 3. Criar um renderizador
renderer = MockRenderer()
renderer.init_window(800, 600, "Olá Física")

# 4. Executar o loop de física
for frame in range(60):
    # O motor calcula forças, integra física, e devolve
    # um array NumPy estruturado para o renderizador
    data = engine.tick(800, 600)
    
    renderer.clear_screen((0.1, 0.1, 0.1, 1.0))
    renderer.render_frame(data)
    renderer.swap_buffers()
    
    # O painel converge suavemente para sua assíntota:
    # x = 800 * 0.05 = 40, y = 600 * 0.05 = 30
    # w = 800 * 0.90 = 720, h = 600 * 0.90 = 540
    if frame % 10 == 0:
        print(f"Frame {frame}: rect={data[0]['rect']}")
```

### Layout Impulsionado por Servidor

```python
from core.engine import AetherEngine
from core.ui_builder import UIBuilder

engine = AetherEngine()

intent = {
    "layout": "column",
    "spacing": 20,
    "animation": "organic",
    "padding": 10,
    "elements": [
        {"id": "header", "type": "smart_panel", "padding": 0.03, "z": 0},
        {"id": "title", "type": "canvas_text", "x": 40, "y": 15, "w": 400, "h": 40,
         "text_content": "Olá Aetheris", "font_size": 24, "z": 5},
        {"id": "content", "type": "smart_panel", "padding": 0.05, "z": 1},
    ]
}

builder = UIBuilder()
builder.build_from_intent(engine, intent)
# engine agora tem 3 elementos com posições impulsionadas por física
```

### Layout Impulsionado por Banco de Dados (Ponte Aether-Data)

```python
from core.engine import AetherEngine
from core.ui_builder import UIBuilder
from core.data_bridge import SQLiteProvider

engine = AetherEngine()
builder = UIBuilder()

# Conectar a um banco de dados SQLite local
db = SQLiteProvider("./meu_app.db")
db.connect()

# Definir como colunas do BD mapeiam para propriedades de física
template = {
    "type": "static_box",
    "columns": {
        "x": {"source": "pos_x", "scale": [0, 1000, 10, 790]},
        "y": {"source": "pos_y", "scale": [0, 1000, 10, 590]},
        "w": {"source": "width", "scale": [0, 10000, 50, 500]},
        "h": {"source": "height", "scale": [0, 10000, 50, 500]},
        "z": {"source": "layer"},
    },
    "metadata_fields": ["title", "rating"],
}

# Construir elementos diretamente da consulta do banco de dados
count = builder.build_from_datasource(engine, db, "SELECT * FROM movies", template)
print(f"Criados {count} elementos do banco de dados")

db.disconnect()
```

---

## A Trindade do Multi-Renderizador

A inovação central do Aetheris UI é a **arquitetura de renderização desacoplada**. O motor de física produz um único array NumPy estruturado por frame:

```python
dtype=[('rect', 'f4', 4), ('color', 'f4', 4), ('z', 'i4')]
```

Este array — contendo `[x, y, largura, altura]`, `[r, g, b, a]`, e `índice_z` para cada elemento — é o **único** dado que o renderizador recebe. O renderizador não tem conhecimento de objetos `DifferentialElement`, constantes de mola, ou cálculos de assíntota.

| Renderizador | Tecnologia | Suporte de Texto | Plataforma |
|-------------|-----------|-----------------|------------|
| **GLRenderer** | ModernGL + shaders SDF + texturas Pillow | Texturas de texto rasterizadas na GPU | Desktop (Linux/Windows/macOS) |
| **Pyodide Canvas** | HTML5 Canvas 2D + sobreposição DOM | Híbrido: Canvas fillText + HTML `<div>` | Web (qualquer navegador) |
| **KivyRenderer** | Kivy Graphics + widgets Label | Híbrido: texturas CoreLabel + Labels Kivy | Mobile (iOS/Android) |
| **TkinterRenderer** | Tkinter Canvas | Texto de depuração via `create_text` | Desktop (apenas depuração) |
| **MockRenderer** | impressão stdout | N/A | CI/CD headless |

Todos os renderizadores consomem o **idêntico** array NumPy da **idêntica** chamada `AetherEngine.tick()`. Trocar de renderizador requer alterar uma única linha de código.

---

## Resumo da Arquitetura

```
┌─────────────────────────────────────────────────────────────┐
│                    MOTOR AETHERIS UI                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────┐    ┌──────────────────────────────────┐│
│  │  Domínio        │    │     Pipeline de Renderização     ││
│  │  Matemático     │    │                                  ││
│  │                 │    │  ┌──────────┐ ┌──────────┐      ││
│  │ ┌─────────────┐ │    │  │GLRenderer│ │KivyRender│      ││
│  │ │StateTensor  │ │    │  │(ModernGL)│ │ (Kivy)   │      ││
│  │ │- state[4]   │ │    │  └────┬─────┘ └────┬─────┘      ││
│  │ │- velocity[4]│ │    │       │             │            ││
│  │ │- accel[4]   │ │    │       └──────┬──────┘            ││
│  │ └─────────────┘ │    │              │                   ││
│  │        │        │    │  ┌───────────▼───────────────┐  ││
│  │ ┌─────────────┐ │    │  │  Array NumPy Estruturado  │  ││
│  │ │   Solver    │ │    │  │  [('rect','f4',4),        │  ││
│  │ │- Lei de     │ │    │  │   ('color','f4',4),       │  ││
│  │ │  Hooke      │ │    │  │   ('z','i4')]             │  ││
│  │ └─────────────┘ │    │  └───────────────────────────┘  ││
│  │        │        │    │              │                   ││
│  │ ┌─────────────┐ │    │  ┌───────────▼───────────────┐  ││
│  │ │StateManager │ │    │  │     Metadados JSON        │  ││
│  │ │- Lerp       │ │    │  │  (texto, fonte, dados     │  ││
│  │ │- HyperDamp  │ │    │  │   DOM)                    │  ││
│  │ └─────────────┘ │    │  └───────────────────────────┘  ││
│  └────────┬────────┘    └──────────────────────────────────┘│
│           │                                                   │
│  ┌────────▼────────┐                                         │
│  │  AetherEngine   │                                         │
│  │  - tick()       │                                         │
│  │  - registro     │                                         │
│  │  - rastreamento │                                         │
│  │    de dt        │                                         │
│  └─────────────────┘                                         │
└─────────────────────────────────────────────────────────────┘
```

Ver [docs/ARCHITECTURE_PT.md](docs/ARCHITECTURE_PT.md) para a imersão profunda matemática completa.

---

## Fundamentos Matemáticos

### Integração de Euler

Cada frame, o estado do elemento evolui via:

```
v(t+dt) = (v(t) + a(t) · dt) · (1 - viscosidade)
s(t+dt) = s(t) + v(t+dt) · dt
```

### Lei de Hooke

A força restauradora atrai elementos para sua assíntota:

```
F = (alvo - atual) · k
```

### Amortecimento Crítico

Para um sistema massa-mola com m=1:

```
c_crítico = 2 · √k
```

### Limitação por Norma L2 (Aether-Guard)

```
se ||v|| > V_max:
    v = (v / ||v||) · V_max
```

### Ajuste por Épsilon (Regra dos 99%)

```
se ||s - alvo|| < 0.5 E ||v|| < 5.0:
    s = alvo
    v = 0
```

Ver [docs/ARCHITECTURE_PT.md](docs/ARCHITECTURE_PT.md) para derivações completas.

---

## Referência da API

Ver [docs/API_REFERENCE_PT.md](docs/API_REFERENCE_PT.md) para documentação completa de classes e métodos.

---

## Contribuindo

1. Faça um fork do repositório
2. Crie um branch de funcionalidade (`git checkout -b feature/funcionalidade-incrivel`)
3. Execute a suíte de testes: `pytest tests/ -v`
4. Confirme suas mudanças (`git commit -m 'Adicionar funcionalidade incrível'`)
5. Envie para o branch (`git push origin feature/funcionalidade-incrivel`)
6. Abra um Pull Request

---

## Licença

Licença MIT. Ver [LICENSE](LICENSE) para detalhes.
