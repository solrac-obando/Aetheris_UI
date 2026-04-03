# Aetheris UI — Referência da API

> Guia completo do desenvolvedor para todas as classes, métodos e funções públicas.

---

## Índice

- [Módulos do Núcleo](#módulos-do-núcleo)
- [Fundamento Matemático (`aether_math.py`)](#fundamento-matemático-aether_mathpy)
- [Elementos (`elements.py`)](#elementos-elementspy)
- [Motor (`engine.py`)](#motor-enginepy)
- [Solver (`solver.py` / `solver_wasm.py`)](#solver-solverpy--solver_wasmpy)
- [Gerenciador de Estado (`state_manager.py`)](#gerenciador-de-estado-state_managerpy)
- [Tensor Compiler (`tensor_compiler.py`)](#tensor-compiler-tensor_compilerpy)
- [UI Builder (`ui_builder.py`)](#ui-builder-ui_builderpy)
- [Renderizadores](#renderizadores)
- [Base do Renderizador (`renderer_base.py`)](#base-do-renderizador-renderer_basepy)
- [Renderizador GL (`gl_renderer.py`)](#renderizador-gl-gl_rendererpy)
- [Renderizador Kivy (`kivy_renderer.py`)](#renderizador-kivy-kivy_rendererpy)
- [Renderizador Tkinter (`tkinter_renderer.py`)](#renderizador-tkinter-tkinter_rendererpy)
- [Ponte do Solver (`solver_bridge.py`)](#ponte-do-solver-solver_bridgepy)

---

## Módulos do Núcleo

Todos os módulos do núcleo residem em `core/` e são importados como:

```python
from core.engine import AetherEngine
from core.elements import SmartPanel, StaticBox, CanvasTextNode, DOMTextNode
from core.tensor_compiler import TensorCompiler
from core.ui_builder import UIBuilder
```

---

## Fundamento Matemático (`aether_math.py`)

### Constantes do Módulo

| Constante | Tipo | Valor | Descrição |
|-----------|------|-------|-------------|
| `EPSILON` | `np.float32` | `1e-9` | Denominador mínimo para divisão segura |
| `MAX_VELOCITY` | `np.float32` | `5000.0` | Velocidade máxima em pixels/segundo |
| `MAX_ACCELERATION` | `np.float32` | `10000.0` | Aceleração máxima em pixels/segundo² |
| `SNAP_DISTANCE` | `np.float32` | `0.5` | Limiar de distância para o Ajuste por Épsilon (pixels) |
| `SNAP_VELOCITY` | `np.float32` | `5.0` | Limiar de velocidade para o Ajuste por Épsilon (px/s) |

### `safe_divide(numerator, denominator, epsilon=EPSILON)`

Divisão segura com proteção por épsilon para prevenir divisão por zero.

**Parâmetros:**
- `numerator`: Dividendo (escalar ou array NumPy)
- `denominator`: Divisor (escalar ou array NumPy)
- `epsilon`: Valor absoluto mínimo para o denominador (padrão: `1e-9`)

**Retorna:**
- Resultado de divisão seguro, nunca `inf` ou `NaN` por divisão por zero.

**Lança:**
- Nenhuma — sempre retorna um valor finito.

**Exemplo:**
```python
from core.aether_math import safe_divide
resultado = safe_divide(10.0, 0.0)  # Retorna ~1e10, não inf
```

### `clamp_magnitude(vector, max_val)`

Limita a norma L2 (magnitude) de um vetor preservando sua direção.

**Parâmetros:**
- `vector`: Array NumPy que representa um vetor
- `max_val`: Magnitude máxima permitida

**Retorna:**
- Vetor limitado com `||v|| <= max_val`.

**Exemplo:**
```python
from core.aether_math import clamp_magnitude
v = np.array([3000.0, 4000.0], dtype=np.float32)  # ||v|| = 5000
limitado = clamp_magnitude(v, 3000.0)  # ||limitado|| = 3000
```

### `check_and_fix_nan(array, name="tensor")`

Detecta valores NaN/Inf e retorna um array zerado com um aviso.

**Parâmetros:**
- `array`: Array NumPy a verificar
- `name`: Identificador para a mensagem de aviso

**Retorna:**
- Array original se estiver limpo, array zerado se detectar NaN/Inf.

**Lança:**
- `RuntimeWarning`: Se detectar NaN ou Inf.

### `class StateTensor`

Representa um elemento da interface como uma partícula física com vetores de estado, velocidade e aceleração.

#### `__init__(x=0.0, y=0.0, w=100.0, h=100.0)`

Inicializa um StateTensor com posição e dimensões.

**Parâmetros:**
- `x`: Posição X em pixels
- `y`: Posição Y em pixels (origem superior-esquerda)
- `w`: Largura em pixels
- `h`: Altura em pixels

**Atributos:**
- `state`: `np.ndarray` de forma `(4,)`, tipo `float32` — `[x, y, w, h]`
- `velocity`: `np.ndarray` de forma `(4,)`, tipo `float32` — vetor de velocidade
- `acceleration`: `np.ndarray` de forma `(4,)`, tipo `float32` — vetor de aceleração

#### `apply_force(force)`

Aplica um vetor de força ao tensor de aceleração.

Assume massa `m=1`, portanto `F = ma` se torna `F = a`. As forças se acumulam.

**Parâmetros:**
- `force`: `np.ndarray` de forma `(4,)`, tipo `float32` — vetor de força `[fx, fy, fw, fh]`

**Lança:**
- `RuntimeWarning`: Se o Aether-Guard detectar NaN/Inf na força de entrada.

#### `euler_integrate(dt, viscosity=0.1, target_state=None)`

Atualiza o estado de física usando integração de Euler semi-implícita.

**Passos:**
1. Valida `dt` com `safe_divide` (faixa de 0 a 1 segundo)
2. Atualiza velocidade: `v = (v + a·dt) · (1 - viscosidade)`
3. Limita magnitude da velocidade a `MAX_VELOCITY`
4. Atualiza estado: `s = s + v·dt`
5. Limita largura/altura a >= 0
6. Reinicia aceleração a zero
7. Verifica NaN/Inf em estado e velocidade
8. Aplica Ajuste por Épsilon se estiver perto de `target_state`

**Parâmetros:**
- `dt`: Delta de tempo em segundos
- `viscosity`: Fator de amortecimento (0.0 = sem amortecimento, 1.0 = parada total)
- `target_state`: Alvo opcional `[x, y, w, h]` para verificação de ajuste

---

## Elementos (`elements.py`)

### `class DifferentialElement(ABC)`

Classe base abstrata para todos os elementos da interface. Cada elemento possui um `StateTensor` e define como calcular seu estado alvo (assíntota).

#### `__init__(x=0, y=0, w=100, h=100, color=(1,1,1,1), z=0)`

**Parâmetros:**
- `x, y`: Coordenadas de posição
- `w, h`: Largura e altura
- `color`: Tupla RGBA, valores float32 de 0 a 1
- `z`: Índice-Z para profundidade de renderização

#### `calculate_asymptotes(container_w, container_h) -> np.ndarray` *(abstrato)*

Calcula o `[x, y, w, h]` alvo para o solver baseado no tamanho do contêiner.

**Parâmetros:**
- `container_w`: Largura do contêiner/janela em pixels
- `container_h`: Altura do contêiner/janela em pixels

**Retorna:**
- `np.ndarray` de forma `(4,)`, tipo `float32` — estado alvo

#### `rendering_data` *(propriedade)*

Retorna um dicionário com `rect`, `color` e `z` para o renderizador.

### `class StaticBox(DifferentialElement)`

Um elemento estático com posição alvo fixa. Ignora o tamanho do contêiner.

#### `__init__(x, y, w, h, color=(1,1,1,1), z=0)`

**Parâmetros:**
- `x, y`: Posição fixa
- `w, h`: Dimensões fixas
- `color`: Tupla RGBA
- `z`: Índice-Z

### `class SmartPanel(DifferentialElement)`

Um painel responsivo que mantém uma margem percentual das bordas do contêiner.

#### `__init__(x=0, y=0, w=100, h=100, color=(1,1,1,1), z=0, padding=0.05)`

**Parâmetros:**
- `x, y, w, h`: Valores iniciais (sobrescritos pela assíntota)
- `color`: Tupla RGBA
- `z`: Índice-Z
- `padding`: Fração do contêiner para a margem (0.05 = 5%)

#### `calculate_asymptotes(container_w, container_h)`

Retorna `[container_w·padding, container_h·padding, container_w·(1-2·padding), container_h·(1-2·padding)]`.

### `class FlexibleTextNode(DifferentialElement)`

Um elemento de texto com posicionamento estático. Atualmente se comporta como `StaticBox` com metadados de texto.

#### `__init__(x=0, y=0, w=200, h=50, color=(1,1,1,1), z=0, text="Text")`

**Parâmetros:**
- `x, y, w, h`: Posição e dimensões
- `color`: Tupla RGBA
- `z`: Índice-Z
- `text`: Conteúdo do texto

#### `text` *(propriedade)*

Obtém/define o conteúdo do texto.

### `class SmartButton(DifferentialElement)`

Um botão ancorado a um elemento pai com deslocamentos configuráveis.

#### `__init__(parent, offset_x=0, offset_y=0, offset_w=100, offset_h=50, color=(0.8,0.8,0.2,1.0), z=0)`

**Parâmetros:**
- `parent`: `DifferentialElement` pai ao qual se ancorar
- `offset_x`: Deslocamento X desde a borda esquerda do pai
- `offset_y`: Deslocamento Y desde a borda superior do pai
- `offset_w`: Largura do botão
- `offset_h`: Altura do botão
- `color`: Tupla RGBA
- `z`: Índice-Z

#### `calculate_asymptotes(container_w, container_h)`

Retorna `[pai.x + offset_x, pai.y + offset_y, offset_w, offset_h]`.

### `class CanvasTextNode(DifferentialElement)`

Texto renderizado diretamente no Canvas via `ctx.fillText`. Participa completamente na simulação de física.

#### `__init__(x=0, y=0, w=200, h=50, color=(1,1,1,1), z=0, text="Text", font_size=24, font_family="Arial")`

**Parâmetros:**
- `x, y, w, h`: Posição e dimensões impulsionadas por física
- `color`: Tupla RGBA para a cor do texto (float32, 0-1)
- `z`: Índice-Z
- `text`: Conteúdo do texto
- `font_size`: Tamanho da fonte em pixels
- `font_family`: Nome da família de fonte

#### `text_metadata` *(propriedade)*

Retorna `{"type": "canvas_text", "text": ..., "size": ..., "family": ..., "color": ...}`.

### `class DOMTextNode(DifferentialElement)`

Texto renderizado como um `<div>` de HTML sobreposto ao Canvas. Habilita seleção de texto, acessibilidade e SEO.

#### `__init__(x=0, y=0, w=200, h=50, color=(0,0,0,0), z=0, text="Text", font_size=16, font_family="Arial", text_color=(1,1,1,1))`

**Parâmetros:**
- `x, y, w, h`: Posição e dimensões impulsionadas por física
- `color`: RGBA para o fundo do retângulo (tipicamente transparente)
- `z`: Índice-Z
- `text`: Conteúdo do texto
- `font_size`: Tamanho da fonte em pixels
- `font_family`: Nome da família de fonte
- `text_color`: Tupla RGBA para a cor do texto (float32, 0-1)

#### `text_metadata` *(propriedade)*

Retorna `{"type": "dom_text", "text": ..., "size": ..., "family": ..., "color": ..., "bg_color": ...}`.

---

## Motor (`engine.py`)

### `class AetherEngine`

O orquestrador central. Gerencia o registro de elementos, o loop de simulação de física, e a extração de dados.

#### `__init__()`

Inicializa o motor com registro vazio, rastreamento de tempo, StateManager e TensorCompiler.

#### `register_element(element)`

Registra um `DifferentialElement` para simulação de física.

**Parâmetros:**
- `element`: Uma instância de `DifferentialElement`

#### `tick(win_w, win_h) -> np.ndarray`

Executa um frame da simulação de física.

**Passos:**
1. Calcular delta de tempo
2. Verificar choque de layout (hiper-amortecimento)
3. Para cada elemento: calcular assíntota, computar forças, integrar
4. Extrair array NumPy estruturado

**Parâmetros:**
- `win_w`: Largura da janela em pixels
- `win_h`: Altura da janela em pixels

**Retorna:**
- `np.ndarray` estruturado com tipo `[('rect', 'f4', 4), ('color', 'f4', 4), ('z', 'i4')]`

#### `get_ui_metadata() -> str`

Retorna uma string JSON contendo metadados de texto para elementos `CanvasTextNode` e `DOMTextNode`, indexados por índice-Z.

**Retorna:**
- String JSON, por exemplo: `{"5": {"type": "canvas_text", "text": "Título", "size": 24, ...}}`

#### `dt` *(propriedade)*

Delta de tempo do último frame em segundos.

#### `element_count` *(propriedade)*

Número de elementos registrados.

---

## Solver (`solver.py` / `solver_wasm.py`)

### `calculate_restoring_force(current_state, target_state, spring_constant) -> np.ndarray`

Aplica a Lei de Hooke: `F = (alvo - atual) · k`.

**Parâmetros:**
- `current_state`: `[x, y, w, h]` atual como `float32`
- `target_state`: `[x, y, w, h]` alvo como `float32`
- `spring_constant`: Rigidez `k`

**Retorna:**
- Vetor de força como `float32`, magnitude limitada a 10,000.

### `calculate_boundary_forces(state, container_w, container_h, boundary_stiffness) -> np.ndarray`

Calcula forças de repulsão por violações de fronteira.

**Parâmetros:**
- `state`: `[x, y, w, h]` atual como `float32`
- `container_w`: Largura do contêiner
- `container_h`: Altura do contêiner
- `boundary_stiffness`: Constante de mola para repulsão de fronteira

**Retorna:**
- Vetor de força de fronteira como `float32`, magnitude limitada a 5,000.

### `clamp_vector_magnitude(vector, max_val) -> np.ndarray`

Limita a norma L2 do vetor preservando a direção.

**Parâmetros:**
- `vector`: Vetor de entrada
- `max_val`: Magnitude máxima

**Retorna:**
- Vetor limitado.

---

## Gerenciador de Estado (`state_manager.py`)

### `class StateManager`

Gerencia a detecção de choques de layout e a interpolação linear para transições de estado.

#### `__init__()`

Inicializa com dimensões zero e sem amortecimento ativo.

#### `check_teleportation_shock(current_w, current_h) -> float`

Detecta mudanças drásticas no tamanho da janela e retorna um multiplicador de viscosidade.

**Parâmetros:**
- `current_w`: Largura atual da janela
- `current_h`: Altura atual da janela

**Retorna:**
- `5.0` se detectar choque (15 quadros de amortecimento 5x), `1.0` caso contrário.

#### `lerp_arrays(state_a, state_b, t) -> np.ndarray`

Interpolação linear: `(1-t)·a + t·b`.

**Parâmetros:**
- `state_a`: Array de estado inicial
- `state_b`: Array de estado alvo
- `t`: Fator de interpolação [0, 1]

**Retorna:**
- Array interpolado como `float32`.

---

## Tensor Compiler (`tensor_compiler.py`)

### `class TensorCompiler`

Compila intenções de design JSON em arrays de coeficientes de física.

#### `STIFFNESS_MAP` *(atributo de classe)*

Valores de rigidez predefinidos: `{"snappy": 0.8, "organic": 0.1, "fluid": 0.05, "rigid": 2.0, "gentle": 0.02}`

#### `VISCOSITY_MAP` *(atributo de classe)*

Valores de viscosidade predefinidos: `{"snappy": 0.3, "organic": 0.5, "fluid": 0.7, "rigid": 0.1, "gentle": 0.85}`

#### `compile_intent(intent_json) -> np.ndarray`

Compila um JSON de intenção de design em um array de coeficientes de física.

**Parâmetros:**
- `intent_json`: Dicionário com `layout`, `spacing`, `animation`, `padding`, `elements`, etc.

**Retorna:**
- Array estruturado com tipo `[('element_id', 'U64'), ('stiffness', 'f4'), ('viscosity', 'f4'), ('boundary_padding', 'f4', 4), ('spacing', 'f4')]`

#### `apply_coefficients(engine, coefficients)`

Aplica coeficientes compilados a uma instância de `AetherEngine`.

**Parâmetros:**
- `engine`: `AetherEngine` alvo
- `coefficients`: Array estruturado de `compile_intent()`

#### `get_default_coefficients(animation="organic", spacing=0.0, padding=0.0) -> np.ndarray`

Obtém coeficientes padrão para um ajuste de animação dado.

### `speed_to_stiffness(transition_time_ms) -> float`

Deriva a constante de mola desde a duração de transição: `k = 16 / T²`.

**Parâmetros:**
- `transition_time_ms`: Tempo de transição desejado em milissegundos

**Retorna:**
- Constante de mola `k` como `float32`, limitada a 10,000.

### `speed_to_viscosity(transition_time_ms) -> float`

Deriva a viscosidade desde a velocidade de transição.

**Parâmetros:**
- `transition_time_ms`: Tempo de transição desejado em milissegundos

**Retorna:**
- Valor de viscosidade (0.05–0.95) como `float32`.

---

## UI Builder (`ui_builder.py`)

### `class UIBuilder`

Traduz Intenção JSON em elementos `AetherEngine` registrados.

#### `ELEMENT_TYPES` *(atributo de classe)*

Mapeamento: `{"static_box": StaticBox, "smart_panel": SmartPanel, "smart_button": SmartButton, "flexible_text": FlexibleTextNode, "canvas_text": CanvasTextNode, "dom_text": DOMTextNode}`

#### `build_from_intent(engine, intent)`

Analisa a intenção JSON e registra todos os elementos com o motor.

**Parâmetros:**
- `engine`: `AetherEngine` alvo
- `intent`: Dicionário de intenção JSON

#### `element_count` *(propriedade)*

Número de elementos construídos.

---

## Renderizadores

### `renderer_base.py`

#### `class BaseRenderer(ABC)`

Interface abstrata para todos os renderizadores.

**Métodos abstratos:**
- `init_window(width, height, title)` — Inicializa a superfície de renderização
- `clear_screen(color)` — Limpa com cor de fundo
- `render_frame(data_buffer)` — Renderiza o array estruturado
- `swap_buffers()` — Apresenta o frame

### `gl_renderer.py`

#### `class GLRenderer(BaseRenderer)`

Renderizador ModernGL com shaders SDF e texturas de texto Pillow.

**Métodos chave:**
- `init_window(width, height, title)` — Cria contexto OpenGL independente
- `render_frame(data_buffer, engine_metadata=None)` — Renderiza com metadados de texto opcionais
- `_get_or_create_text_texture(text, font_size, color_rgba, font_family)` — Armazena texturas de texto em cache

### `kivy_renderer.py`

#### `class KivyRenderer(BaseRenderer)`

Renderizador Kivy com inversão do eixo Y e suporte de texto híbrido.

**Métodos chave:**
- `init_window(width, height, title)` — Inicializa o renderizador
- `set_canvas(canvas)` — Define o widget canvas do Kivy
- `set_dom_container(container)` — Define o contêiner para labels tipo DOM
- `render_frame(data_buffer, engine_metadata=None)` — Renderiza com inversão do eixo Y
- `cleanup_dom_labels()` — Remove todas as labels de texto DOM

### `tkinter_renderer.py`

#### `class TkinterRenderer(BaseRenderer)`

Renderizador de depuração Tkinter para prototipagem rápida.

**Métodos chave:**
- `init_window(width, height, title)` — Cria janela Tk e Canvas
- `start(engine_instance)` — Inicia o loop principal do Tkinter com atualizações de física
- `stop()` — Para o renderizador e limpa

### `solver_bridge.py`

Detecta automaticamente a disponibilidade de Numba e importa a implementação de solver apropriada.

**Exporta:**
- `calculate_restoring_force` — De `solver.py` (Numba) ou `solver_wasm.py` (NumPy)
- `calculate_boundary_forces` — Mesma lógica de dupla rota
- `HAS_NUMBA` — Booleano indicando qual rota está ativa

---

*Para contexto arquitetônico, ver [ARCHITECTURE_PT.md](ARCHITECTURE_PT.md). Para o README principal, ver [../README_PT.md](../README_PT.md).*

---

## Ponte de Dados (`data_bridge.py`)

### Constantes do Módulo

| Constante | Tipo | Valor | Descrição |
|-----------|------|-------|-----------|
| `DATA_NORMALIZE_MIN` | `float` | `10.0` | Mínimo padrão para escalonamento Min-Max (pixels) |
| `DATA_NORMALIZE_MAX` | `float` | `500.0` | Máximo padrão para escalonamento Min-Max (pixels) |
| `VECTOR_TENSOR_SCALE` | `float` | `100.0` | Fator de escala padrão para conversão vetor-para-tensor |
| `REMOTE_CONNECT_TIMEOUT` | `int` | `5` | Timeout para verificação de conectividade remota (segundos) |
| `REMOTE_REQUEST_TIMEOUT` | `int` | `10` | Timeout para requisições do provedor remoto (segundos) |
| `NORMALIZATION_EPSILON` | `float` | `1e-9` | Épsilon para divisão segura na normalização |

### `min_max_scale(value, data_min, data_max, target_min=DATA_NORMALIZE_MIN, target_max=DATA_NORMALIZE_MAX)`

Escalonamento Min-Max com proteção Aether-Guard.

**Parâmetros:**
- `value`: O valor a escalonar
- `data_min`: Valor mínimo nos dados fonte
- `data_max`: Valor máximo nos dados fonte
- `target_min`: Mínimo do intervalo alvo (padrão: 10.0)
- `target_max`: Máximo do intervalo alvo (padrão: 500.0)

**Retorna:**
- Valor escalonado limitado a `[target_min, target_max]`.

### `normalize_column(values, target_min=DATA_NORMALIZE_MIN, target_max=DATA_NORMALIZE_MAX)`

Normaliza uma coluna inteira de valores usando escalonamento Min-Max.

**Parâmetros:**
- `values`: Lista de valores fonte
- `target_min`: Mínimo do intervalo alvo
- `target_max`: Máximo do intervalo alvo

**Retorna:**
- Lista de valores normalizados.

### `vector_to_tensor(vector, scale=VECTOR_TENSOR_SCALE)`

Converte um vetor embedding do PostgreSQL em uma força StateTensor.

**Parâmetros:**
- `vector`: Lista de floats (embedding de IA)
- `scale`: Fator de escala (padrão: 100.0)

**Retorna:**
- `np.ndarray` de forma `(4,)`, tipo `float32` — vetor de força `[fx, fy, fw, fh]`.

### `class BaseAetherProvider(ABC)`

Classe base abstrata para provedores de dados.

**Métodos abstratos:**
- `connect()` — Estabelecer conexão
- `disconnect()` — Fechar conexão
- `execute_query(query, params)` — Executar consulta, retornar lista de dicionários
- `insert_element_state(element_id, state)` — Salvar estado do elemento
- `get_element_state(element_id)` — Obter estado do elemento
- `delete_element_state(element_id)` — Excluir estado do elemento

### `class SQLiteProvider(BaseAetherProvider)`

Provedor baseado em SQLite para persistência local.

#### `__init__(db_path=None)`

**Parâmetros:**
- `db_path`: Caminho para o banco de dados SQLite. Auto-detecta WASM vs Desktop.

#### `connect()`

Estabelece conexão e cria a tabela `element_states` se necessário.

#### `disconnect()`

Fecha a conexão. Seguro chamar múltiplas vezes.

#### `execute_query(query, params=())`

Executa consulta SQL e retorna lista de dicionários.

#### `insert_element_state(element_id, state)`

Salva estado do elemento usando INSERT OR REPLACE.

**Parâmetros:**
- `element_id`: Identificador único
- `state`: Dicionário com x, y, w, h, r, g, b, a, z, metadata

**Retorna:**
- `True` em sucesso, `False` em falha.

#### `get_element_state(element_id)`

Obtém estado do elemento por ID.

**Retorna:**
- Dicionário com estado do elemento, ou `None` se não encontrado.

#### `delete_element_state(element_id)`

Exclui estado do elemento por ID.

**Retorna:**
- `True` se a linha foi excluída, `False` caso contrário.

### `class RemoteAetherProvider(BaseAetherProvider)`

Provedor proxy REST para PostgreSQL via endpoint do servidor.

#### `__init__(base_url="http://localhost:5000")`

**Parâmetros:**
- `base_url`: URL base do servidor Aetheris.
