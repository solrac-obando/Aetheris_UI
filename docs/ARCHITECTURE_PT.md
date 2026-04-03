# Aetheris UI — Imersão Profunda em Arquitetura

> A Alma Matemática de um Motor de Interface Impulsionado por Física

---

## Índice

- [1. A Filosofia Central: Física-como-UI](#1-a-filosofia-central-física-como-ui)
- [2. Integração de Euler: O Pulso Temporal](#2-integração-de-euler-o-pulso-temporal)
- [3. Lei de Hooke e o Solver de Restrições](#3-lei-de-hooke-e-o-solver-de-restrições)
- [4. Aether-Guard: Camada de Segurança Matemática](#4-aether-guard-camada-de-segurança-matemática)
- [5. Gerenciamento de Estado e Estabilidade](#5-gerenciamento-de-estado-e-estabilidade)
- [6. A Ponte de Desacoplamento](#6-a-ponte-de-desacoplamento)
- [7. Arquitetura do Pipeline de Renderização](#7-arquitetura-do-pipeline-de-renderização)
- [8. UI Impulsionada por Servidor e o Tensor Compiler](#8-ui-impulsionada-por-servidor-e-o-tensor-compiler)
- [9. Características de Desempenho](#9-características-de-desempenho)

---

## 1. A Filosofia Central: Física-como-UI

Os motores de interface de usuário tradicionais utilizam **algoritmos de layout estáticos**: flexbox, grid, posicionamento absoluto. Estes são determinísticos mas rígidos — saltam instantaneamente do estado A ao estado B sem física intermediária.

O Aetheris UI trata cada elemento da interface como uma **partícula física** com quatro graus de liberdade: posição (x, y) e dimensões (largura, altura). Cada partícula possui:

- Um **vetor de estado** `s = [x, y, w, h]` em `np.float32`
- Um **vetor de velocidade** `v = [vx, vy, vw, vh]`
- Um **vetor de aceleração** `a = [ax, ay, aw, ah]`

O layout da interface emerge da **integração de forças** ao longo do tempo, não de um passe de layout. Isso produz transições naturais e suaves com momento, overshoot e amortecimento — o mesmo comportamento físico que você esperaria de um objeto real se movendo pelo espaço.

### Fundamento Matemático

O sistema se fundamenta em duas tradições matemáticas:

1. **Álgebra de Baldor** — Proporcionalidade e escalonamento linear para layouts responsivos (por exemplo, a margem do SmartPanel como fração do tamanho do contêiner). A influência de Baldor é explícita na aplicação de proporções diretas e inversas para calcular posições e dimensões relativas ao contêiner.

2. **Pré-Cálculo** — Sistemas lineares, análise de estabilidade, e a relação entre constantes de mola, razões de amortecimento e tempo de assentamento. Os conceitos de limites e derivadas do Pré-Cálculo fundamentam a integração de Euler e o cálculo de velocidades por diferenças finitas.

---

## 2. Integração de Euler: O Pulso Temporal

### O Loop de Integração

Cada frame, `AetherEngine.tick()` executa a seguinte sequência:

```
1. Calcular delta de tempo: dt = t_atual - t_anterior
2. Para cada elemento:
   a. Calcular assíntota alvo (estado desejado)
   b. Computar força restauradora (Lei de Hooke)
   c. Computar forças de fronteira (restrições do contêiner)
   d. Aplicar forças ao tensor de aceleração
   e. Integrar: atualizar velocidade e estado
   f. Aplicar verificações de segurança Aether-Guard
   g. Verificar condição de Ajuste por Épsilon
3. Extrair array NumPy estruturado para o renderizador
```

### Fórmula de Integração de Euler

A integração utiliza **Euler semi-implícito (simplético)**:

```python
# Atualização de velocidade com viscosidade (fricção)
v(t+dt) = (v(t) + a(t) · dt) · (1 - viscosidade)

# Atualização de estado
s(t+dt) = s(t) + v(t+dt) · dt
```

O termo de viscosidade `(1 - viscosidade)` atua como um fator de amortecimento. Com `viscosidade = 0.1`, a velocidade decai 10% a cada frame na ausência de forças — simulando a resistência do ar.

### Validação do Delta de Tempo

O valor `dt` é validado através da **divisão protegida por épsilon do Aether-Guard**:

```python
dt_seguro = safe_divide(dt, 1.0)  # Protegido por épsilon
dt_seguro = max(dt_seguro, 0.0)    # Sem tempo negativo
dt_seguro = min(dt_seguro, 1.0)    # Limitado a 1 segundo máximo
```

Isso previne a "espiral da morte" onde um `dt` grande (por exemplo, de uma pausa do coletor de lixo) faz a física explodir.

---

## 3. Lei de Hooke e o Solver de Restrições

### Força Restauradora

A força principal que atrai elementos para seu alvo é a **Lei de Hooke**:

```
F_restauradora = (alvo - atual) · k
```

Onde:
- `alvo` é a assíntota calculada pelo método `calculate_asymptotes()` do elemento
- `atual` é o estado atual do elemento
- `k` é a constante de mola (rigidez)

**Maior k** = mola mais rígida, convergência mais rápida, maior potencial de overshoot.
**Menor k** = mola mais suave, convergência mais lenta, movimento mais fluido.

### Forças de Fronteira

Elementos que cruzam os limites do contêiner experimentam uma **força de repulsão**:

```python
se x < 0:
    F_x += (0 - x) · rigidez_fronteira
senão se x + w > largura_contêiner:
    F_x -= ((x + w) - largura_contêiner) · rigidez_fronteira
```

Isso previne que os elementos escapem da área visível, atuando como paredes invisíveis.

### Otimização com Numba

As funções do solver são decoradas com `@njit(cache=True)` para execução em desktop, compilando-se para código máquina em tempo de execução. Para WASM/Pyodide (que carece de Numba), um fallback puro de NumPy em `solver_wasm.py` fornece comportamento idêntico.

---

## 4. Aether-Guard: Camada de Segurança Matemática

Motores de física são inerentemente instáveis. Rigidez alta, amortecimento baixo, ou passos de tempo grandes podem produzir **velocidades explosivas** que travam a aplicação. O Aetheris UI implementa quatro mecanismos de segurança:

### 4.1 Divisão Protegida por Épsilon

```python
def safe_divide(numerador, denominador, epsilon=1e-9):
    denom = max(|denominador|, epsilon)
    return numerador / (denom · sign(denominador))
```

Baseada na **definição de limite** do Cálculo: quando x → 0, f(x)/x é indefinida. Substituímos o denominador com `max(|x|, ε)` para garantir que nunca chegue a zero. Esta proteção é fundamental para prevenir resultados infinitos ou NaN que corromperiam toda a simulação.

### 4.2 Limitação de Velocidade por Norma L2

```python
def clamp_magnitude(vetor, max_val):
    mag = ||vetor||  # Norma L2
    se mag > max_val:
        return (vetor / mag) · max_val
    return vetor
```

Baseada na **normalização de vetores** da Álgebra Linear: se a magnitude de um vetor excede o limiar, o escalamos para baixo preservando sua direção. Isso previne que os elementos se movam mais rápido que `VELOCIDADE_MAX = 5000 px/s`.

A norma L2 (também chamada norma euclidiana) se calcula como:

```
||v|| = √(v₁² + v₂² + v₃² + v₄²)
```

### 4.3 Limitação de Aceleração

De maneira similar, a aceleração se limita a `ACELERACAO_MAX = 10,000 px/s²`. Isso previne que uma única força grande (por exemplo, de um erro de deslocamento massivo) crie aceleração incontrolável.

### 4.4 Detecção e Recuperação de NaN/Inf

```python
def check_and_fix_nan(array, nome="tensor"):
    se any(isnan(array)) ou any(isinf(array)):
        advertir(f"Aether-Guard: NaN/Inf detectado em {nome}")
        return array_zeros
    return array
```

Se qualquer cálculo produzir `NaN` ou `Infinito` (por exemplo, de divisão por zero ou transbordamento), o tensor afetado se reinicia a zero com um aviso. Isso previne que a corrupção se propague pela simulação.

---

## 5. Gerenciamento de Estado e Estabilidade

### 5.1 A Regra dos 99% (Ajuste por Épsilon)

Quando os elementos se aproximam de seu alvo, a força restauradora se aproxima de zero mas nunca o alcança. Em teoria, isso cria o **Paradoxo de Zenão** — passos infinitos para alcançar o alvo. Na prática, ajustamos:

```python
se ||estado - alvo|| < 0.5 E ||velocidade|| < 5.0:
    estado = alvo
    velocidade = 0
    aceleração = 0
```

Os limiares (0.5 pixels, 5.0 px/s) se escolhem para estar **abaixo da percepção visual humana** em DPI típico de tela. Uma vez ajustado, o elemento deixa de consumir ciclos de CPU até que uma nova força seja aplicada.

### 5.2 Hiper-Amortecimento (Absorção de Choques de Layout)

Quando o tamanho da janela muda drasticamente (por exemplo, 1920px → 375px para mobile), as assíntotas saltam instantaneamente. A Lei de Hooke gera uma força massiva do grande erro de deslocamento, potencialmente causando que os elementos transbordem selvagemente.

**Solução**: Detectar o choque e aumentar temporariamente a viscosidade:

```python
se |delta_largura| > 200px:
    quadros_hiper_amortecimento = 15

se quadros_hiper_amortecimento > 0:
    return viscosidade × 5.0  # 5x amortecimento
return viscosidade × 1.0      # Amortecimento normal
```

Isso é análogo ao **amortecedor de um automóvel** golpeando um buraco — o fluido de amortecimento se espessa momentaneamente para absorver o impacto, depois volta ao normal. O sistema mantém um contador de quadros que decai gradualmente, proporcionando uma transição suave entre o estado de choque e o estado normal.

### 5.3 Interpolação Linear (Lerp) para Transições de Estado

Ao transicionar entre estados nomeados (por exemplo, desktop → mobile), o motor utiliza **interpolação linear**:

```
P_novo = (1 - t) · P_base + t · P_alvo
```

Com `t = 0.1`, cada frame move 10% da distância restante — produzindo uma transição suave e eased em vez de um salto instantâneo. Esta fórmula provém diretamente da **Álgebra de Baldor**, capítulo de proporções e misturas, aplicada ao domínio de vetores de estado.

---

## 6. A Ponte de Desacoplamento

### Array NumPy Estruturado

O canal de comunicação entre o motor de física e o renderizador é um **array estruturado plano e eficiente em memória**:

```python
tipo_dado = [
    ('rect', 'f4', 4),    # [x, y, largura, altura] como float32
    ('color', 'f4', 4),   # [r, g, b, a] como float32
    ('z', 'i4'),          # índice-z como int32
]
```

**Por que este formato?**

1. **Compatível com GPU**: `float32` se mapeia diretamente a atributos de vértice OpenGL/WebGL.
2. **Eficiente em memória**: Layout de memória contígua permite transferências sem cópia.
3. **Seguro em tipos**: O tipo estruturado previne discordâncias acidentais de tipo.
4. **Agnóstico do renderizador**: Qualquer renderizador que entenda este formato pode consumir os dados.

### Ponte de Metadados JSON

Dado que o array estruturado só pode conter tipos numéricos, os **metadados de texto** (strings, tamanhos de fonte, famílias de fonte) se expõem através de uma ponte JSON separada:

```python
engine.get_ui_metadata()
# Retorna: {"5": {"tipo": "canvas_text", "texto": "Título", "tamanho": 24, ...}}
```

O renderizador lê tanto o array NumPy (para posições) quanto os metadados JSON (para propriedades de texto) a cada frame.

---

## 7. Arquitetura do Pipeline de Renderização

### Desktop: ModernGL + Shaders SDF

```
AetherEngine.tick()
    → Array NumPy Estruturado
    → GLRenderer.render_frame()
        → Carga VBO (np.hstack → bytes)
        → Matriz de projeção ortográfica
        → Shader de vértices (geração de quad por gl_VertexID)
        → Shader de fragmentos (retângulos arredondados SDF)
        → Texturas de texto (rasterização Pillow → textura GPU)
    → ctx.finish()
```

O shader de fragmentos SDF (Signed Distance Function / Função de Distância com Sinal) produz **retângulos arredondados anti-aliased** em qualquer resolução:

```glsl
float roundedRectSDF(vec2 p, vec2 b, float r) {
    vec2 q = abs(p) - b + r;
    return min(max(q.x, q.y), 0.0) + length(max(q, 0.0)) - r;
}
```

A **translação de eixos** no shader (`vec2 p = (v_texcoord - 0.5) * size`) centraliza o sistema de coordenadas no centro do retângulo, simplificando enormemente o cálculo da SDF. Sem esta translação, teríamos que calcular distâncias de cada esquina individualmente.

### Web: Pyodide + HTML5 Canvas

```
AetherEngine.tick()
    → Array NumPy Estruturado (PyProxy)
    → aether_bridge.js renderLoop()
        → Extrair rects/cores via .getBuffer().data
        → Canvas 2D: fillRect / roundRect
        → Canvas 2D: fillText (para canvas_text)
        → DOM: createElement('div') + translate3d (para dom_text)
        → Destruir todos os objetos PyProxy (sem vazamentos)
    → requestAnimationFrame(renderLoop)
```

### Mobile: Kivy

```
AetherEngine.tick()
    → Array NumPy Estruturado
    → KivyRenderer.render_frame()
        → Inversão do eixo Y: kivy_y = altura - y - h
        → kivy.graphics: Color + Rectangle/RoundedRectangle
        → kivy.core.text: textura CoreLabel (para canvas_text)
        → kivy.uix.label: widget Label (para dom_text)
    → Clock.schedule_interval(1/60)
```

---

## 8. UI Impulsionada por Servidor e o Tensor Compiler

### Intenção JSON

Os layouts se definem como JSON, não como Python codificado:

```json
{
  "layout": "column",
  "spacing": 20,
  "animation": "organic",
  "padding": 10,
  "elements": [
    {"id": "header", "type": "smart_panel", "padding": 0.03, "z": 0},
    {"id": "title", "type": "canvas_text", "x": 40, "y": 15, "w": 400, "h": 40,
     "text_content": "Olá", "font_size": 24, "z": 5}
  ]
}
```

### TensorCompiler

O `TensorCompiler` traduz este JSON em **coeficientes de física**:

```python
compiler = TensorCompiler()
coeficientes = compiler.compile_intent(intent)
# Retorna: array estruturado com [rigidez, viscosidade, margem_fronteira, espaçamento]
```

### Derivação de Rigidez desde Tempo de Transição

O compiler pode derivar a constante de mola `k` desde uma duração de transição desejada `T`:

```
Para amortecimento crítico (m=1):
  c = 2√k
  τ = 1/√k  (constante de tempo)
  T_assentamento = 4τ = 4/√k

Resolvendo para k:
  k = 16 / T²
```

Uma transição de 300ms requer `k = 16 / 0.3² ≈ 177.8`. Esta derivação provém diretamente da análise de sistemas lineares do **Pré-Cálculo**, aplicando as propriedades das equações diferenciais de segunda ordem para sistemas massa-mola amortecidos.

---

## 9. Características de Desempenho

### Desktop (otimizado com Numba)

| Operação | Tempo (μs) |
|----------|------------|
| Força restauradora (por elemento) | ~0.1 |
| Forças de fronteira (por elemento) | ~0.2 |
| Integração de Euler (por elemento) | ~0.3 |
| Tick completo (10 elementos) | ~5 |
| Tick completo (100 elementos) | ~50 |

### Web (NumPy puro via Pyodide)

| Operação | Tempo (μs) |
|----------|------------|
| Força restauradora (por elemento) | ~0.5 |
| Forças de fronteira (por elemento) | ~1.0 |
| Integração de Euler (por elemento) | ~1.5 |
| Tick completo (10 elementos) | ~25 |
| Tick completo (100 elementos) | ~250 |

Todas as operações estão bem dentro do **orçamento de 16.67ms** para 60 FPS, mesmo em WASM.

### Memória

- Array estruturado: 36 bytes por elemento (16 + 16 + 4)
- Sobrecarga PyProxy: ~100 bytes por proxy (destruído a cada frame)
- Cache de texturas de texto: ~1KB por string de texto única

---

*Para documentação completa da API, ver [API_REFERENCE_PT.md](API_REFERENCE_PT.md).*
*Para o README principal em português, ver [../README_PT.md](../README_PT.md).*

---

## 10. Aether-Data: A Ponte de Banco de Dados

### Resumo

O Aether-Data fornece uma interface unificada para popular elementos da UI a partir de bancos de dados. Suporta:

- **SQLite** — Persistência local, compatível com WASM usando o sistema de arquivos virtual do Pyodide
- **PostgreSQL (via proxy REST)** — Dados remotos de alto desempenho, com proteção de credenciais do lado do servidor

### Normalização de Dados (Escalonamento Min-Max)

Os valores do banco de dados frequentemente têm intervalos que causariam comportamento de física "explosivo" (por exemplo, classificações de filmes de 0 a 10.000). O Aether-Data aplica **Escalonamento Min-Max de Álgebra Linear** para normalizar esses valores para intervalos de pixels seguros:

```
escalado = alvo_min + (valor - dados_min) * (alvo_max - alvo_min) / (dados_max - dados_min)
```

**Proteção Aether-Guard:** A divisão usa proteção por épsilon (`1e-9`) para prevenir divisão por zero quando `dados_min == dados_max`. A saída é limitada a `[alvo_min, alvo_max]`.

Intervalo alvo padrão: `[10.0, 500.0]` pixels — grande o suficiente para ser visível, pequeno o suficiente para permanecer na tela.

### Arquitetura de Provedores

```
┌─────────────────────────────────────────────────┐
│              Motor Aetheris UI                  │
│                                                  │
│  UIBuilder.build_from_datasource()              │
│         │                                        │
│         ▼                                        │
│  ┌──────────────────┐    ┌──────────────────┐   │
│  │  SQLiteProvider  │    │RemoteAetherProv. │   │
│  │  (Local/SQLite)  │    │ (Proxy REST)     │   │
│  │                  │    │                  │   │
│  │  - Connect       │    │  - /api/v1/      │   │
│  │  - CRUD ops      │    │    db-bridge     │   │
│  │  - Disconnect    │    │  - Sem creds BD  │   │
│  └────────┬─────────┘    │    expostos      │   │
│           │              └────────┬─────────┘   │
│           │                       │             │
│           ▼                       ▼             │
│    BD SQLite               Servidor Flask       │
│    (arquivo local)        ┌──────────────┐      │
│                           │  PostgreSQL  │      │
│                           │  (simulado)  │      │
│                           └──────────────┘      │
└─────────────────────────────────────────────────┘
```

### Vetor-para-Tensor: Visualizando Embeddings de IA

A utilidade `vector_to_tensor()` converte embeddings `pgvector` do PostgreSQL em forças de física:

```python
embedding = [0.5, -0.3, 0.8, -0.1]  # Embedding de IA
forca = vector_to_tensor(embedding, scale=100.0)
# forca = [50.0, -30.0, 80.0, -10.0]
elemento.tensor.apply_force(forca)
```

Isso permite "Visualizar Embeddings de IA" — cada dimensão do embedding se torna um eixo de força (x, y, largura, altura), permitindo que similaridade semântica se manifeste como proximidade física.

### Segurança de Conexão

- **SQLiteProvider**: Implementa `__del__`, `__enter__`, e `__exit__` para limpeza garantida. Conexões se fecham automaticamente na coleta de lixo ou ao sair do gerenciador de contexto.
- **RemoteAetherProvider**: Requisições HTTP sem estado com timeouts configuráveis (`REMOTE_CONNECT_TIMEOUT = 5s`, `REMOTE_REQUEST_TIMEOUT = 10s`).
