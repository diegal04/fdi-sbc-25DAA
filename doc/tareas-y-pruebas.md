# Tareas Resueltas y Suite de Pruebas

## Índice
1. [Tareas resueltas](#tareas-resueltas)
2. [Ejecución de los tests](#ejecución-de-los-tests)
3. [Estructura de la suite de pruebas](#estructura-de-la-suite-de-pruebas)
4. [Descripción detallada por archivo](#descripción-detallada-por-archivo)
5. [Casos de prueba funcionales sobre cluedo.txt](#casos-de-prueba-funcionales-sobre-cluedotxt)

---

## Tareas resueltas

El proyecto implementa un sistema experto completo. Las funcionalidades se organizan en las siguientes tareas, inferidas del código y la suite de pruebas:

### Tarea 1 — Gramática y parser (EBNF)

**Qué resuelve:** Leer bases de conocimiento en texto plano y convertirlas en estructuras de datos internas.

**Implementación:** `sbc/parser.py` con `pyparsing`.

**Capacidades:**
- Parseo de hechos simples, negaciones y hechos con certeza difusa.
- Parseo de reglas con múltiples antecedentes y extensiones (certeza, precedencia, restricciones aritméticas).
- Parseo de consultas directas y con backward chaining (`razona si`).
- Variables (inicio mayúscula) y literales (inicio minúscula) distinguidos léxicamente.
- Comentarios Python-style `#` ignorados en cualquier posición del fichero.
- Detección de errores sintácticos con línea y columna exactas.

**Tests:** `test/test_parser.py` — 5 clases, ~45 tests.

---

### Tarea 2 — Memoria de trabajo

**Qué resuelve:** Gestionar el estado mutable de hechos y reglas durante la ejecución.

**Implementación:** `sbc/memory.py` — clase `Memoria`.

**Capacidades:**
- Carga de ficheros `.txt` (UTF-8, `parse_all=True`).
- Carga de **directorios**: si la ruta apunta a una carpeta, concatena en orden alfabético todos los `.txt` que contiene (los demás tipos de archivo se ignoran) y los parsea como si fueran uno solo.
- Aserción de hechos: inserta nuevo o actualiza certeza (solo si la nueva es mayor).
- Retractación de hechos mediante negación (`no hecho.`).
- Deduplicación de hechos y reglas.
- Ordenación automática de reglas por precedencia descendente.
- Acumulación de conocimiento desde múltiples ficheros.

**Tests:** `test/test_memoria.py` — 5 clases, ~38 tests.

---

### Tarea 3 — Encadenamiento hacia adelante (*forward chaining*)

**Qué resuelve:** Derivar todos los hechos posibles a partir de la KB hasta alcanzar el punto fijo.

**Implementación:** `sbc/engine.py` — `MotorInferencia.encadenamiento_hacia_adelante()`.

**Capacidades:**
- Bucle de punto fijo (itera hasta que no hay cambios).
- Unificación de antecedentes con hechos de la memoria.
- Evaluación de restricciones aritméticas tras la unificación.
- Propagación de certeza: $\min(c_i) \times c_{regla}$.
- La certeza de un hecho conocido solo se actualiza si la nueva es mayor.
- Devuelve el conteo de hechos nuevos descubiertos.

**Tests:** `TestEncadenamientoAdelante` en `test/test_motor.py` — 10 tests.

---

### Tarea 4 — Restricciones aritméticas

**Qué resuelve:** Filtrar la aplicación de reglas mediante comparaciones numéricas sobre variables.

**Implementación:** `sbc/engine.py` — `evaluar_restricciones()` + sintaxis en `sbc/parser.py`.

**Capacidades:**
- Operadores: `<`, `<=`, `>`, `>=`, `=`.
- Las restricciones se evalúan después de unificar (las variables ya están ligadas).
- Múltiples restricciones en una misma regla actúan como conjunción (AND).
- La resolución profunda (`_resolver`) gestiona cadenas de sustitución.

**Caso de uso en la KB:**
```
# Solo son culpables quienes estaban en la mansión en el momento exacto del crimen
P estuvo_en_mansion crimen <- P llega_mansion LlegaH,
                               P sale_mansion SaleH. [ LlegaH <= 2215; SaleH >= 2215 ]
```

**Tests:** `TestEvaluarRestricciones` (11 tests) + `TestFronterasMatemáticas` (9 tests) en `test/test_motor.py`.

---

### Tarea 5 — Lógica difusa (certeza)

**Qué resuelve:** Cuantificar la confianza en los hechos derivados propagando la incertidumbre de los antecedentes.

**Implementación:** `sbc/engine.py` — cálculo de `certeza_final` en ambos modos de encadenamiento.

**Modelo:**

$$\mathrm{certeza\_derivada} = \min(c_1, c_2, \ldots, c_n) \times \mathrm{certeza\_regla}$$

**Propiedades garantizadas:**
- La certeza nunca excede 1.0.
- La certeza de un hecho en memoria nunca disminuye.
- Forward y backward chaining producen la misma certeza para el mismo hecho.

**Tests:** `TestLogicaDifusa` (6 tests) + certezas verificadas en `TestEncadenamientoAdelante` en `test/test_motor.py`.

---

### Tarea 6 — Encadenamiento hacia atrás (*backward chaining*)

**Qué resuelve:** Demostrar una hipótesis concreta recorriendo el árbol de prueba desde el objetivo hacia los hechos base.

**Implementación:** `sbc/engine.py` — `MotorInferencia.encadenamiento_hacia_atras()`.

**Capacidades:**
- Generador perezoso: produce resultados bajo demanda.
- Consultas con variables (`razona si X es_culpable crimen?`).
- Límite de profundidad (15 niveles) para prevenir bucles infinitos.
- Anti-colisión de espacios de nombres mediante inversión de argumentos en la unificación.
- Limpieza de la sustitución: solo devuelve las variables de la consulta original.

**Tests:** `TestEncadenamientoAtras` (7 tests) en `test/test_motor.py`.

---

### Tarea 7 — Precedencia de reglas

**Qué resuelve:** Controlar el orden de evaluación de reglas para que las más importantes se apliquen primero.

**Implementación:** `sbc/parser.py` (token de 3 dígitos) + `sbc/memory.py` (ordenación) + `sbc/engine.py` (iteración ordenada).

**Capacidades:**
- Precedencia expresada como entero de 3 dígitos (000-999).
- La memoria mantiene las reglas ordenadas en todo momento.
- Permite modelar prioridades lógicas: descartes (999) > evidencia objetiva (900) > culpable (800) > sospechoso fuerte (500) > sospechoso débil (200).

**Tests:** `TestPrecedenciaReglas` en `test/test_motor.py`.

---

### Tarea 8 — Interfaz de usuario (CLI interactiva)

**Qué resuelve:** Proporcionar una consola REPL para interactuar con el sistema en tiempo real.

**Implementación:** `sbc/cli.py` con `click` y `rich`.

**Capacidades:**
- Todos los comandos del sistema (`cargar!`, `descubrir!`, `memoria!`, `ayuda!`, `salir!`).
- Entrada y salida formateada con colores (`rich`).
- Aserción y retractación interactiva de hechos.
- Consultas directas y backward chaining desde el prompt.
- Gestión de errores: parse errors con sugerencias, fichero no encontrado, etc.

---

## Ejecución de los tests

Desde la raíz del repositorio:

```bash
# Ejecutar todos los tests
uv run python -m unittest discover test

# Con verbosidad máxima (nombre de cada test)
uv run python -m unittest discover test -v

# Un fichero concreto
uv run python -m unittest test.test_motor -v

# Una clase concreta
uv run python -m unittest test.test_motor.TestEncadenamientoAdelante -v

# Un test concreto
uv run python -m unittest test.test_motor.TestEncadenamientoAdelante.test_tarea3_culpable_deducido -v
```

**Resultado esperado:**
```
Ran 160 tests in ~0.7s
OK
```

---

## Estructura de la suite de pruebas

```
test/
├── __init__.py
├── test_parser.py    — 5 clases,  ~45 tests   → gramática y dataclasses
├── test_memoria.py   — 5 clases,  ~38 tests   → gestión de estado
└── test_motor.py     — 13 clases, ~77 tests   → algoritmos de inferencia
                                    ──────────
                                    ~160 tests totales
```

---

## Descripción detallada por archivo

### `test/test_parser.py`

| Clase | Tests | Qué verifica |
|---|---|---|
| `TestEstructurasDeDatos` | 4 | Igualdad de `Tripleta`, valores por defecto de `Hecho` y `Restriccion` |
| `TestParserHechos` | 13 | Afirmaciones simples, certezas (0.1–1.0), negaciones, comentarios en línea, errores sin punto, tripleta incompleta, certeza inválida (1.5) |
| `TestParserReglas` | 14 | Regla simple, múltiples antecedentes, con certeza, con precedencia, con restricción, combinaciones, variables en consecuente |
| `TestParserConsultas` | 5 | Consulta directa `?`, `razona si ?`, variables, error sin `?` |
| `TestParserPrecedencia` | 9 | Token de 3 dígitos exactos, distinción con certeza, valores 000-999, combinado con certeza y restricciones |

### `test/test_memoria.py`

| Clase | Tests | Qué verifica |
|---|---|---|
| `TestMemoriaCargarArchivo` | 11 | Carga de `cluedo.txt` (100 hechos, 46 reglas), fichero inexistente, error sintáctico, UTF-8, comentario al final, solo comentarios, múltiples ficheros |
| `TestMemoriaAgregarHecho` | 12 | Inserción, duplicado, actualización de certeza (solo sube), retractación de existente, retractación de inexistente, retractación selectiva |
| `TestMemoriaAgregarRegla` | 3 | Inserción, duplicado, acumulación de reglas distintas |
| `TestMemoriaLimpiar` | 2 | Limpieza de `cluedo.txt`, limpieza de memoria vacía |
| `TestMemoriaCargarDirectorio` | 10 | Carga de directorio con múltiples `.txt`, ignora archivos no-`.txt`, directorio vacío devuelve `False`, directorio inexistente devuelve `False`, orden alfabético garantizado, error sintáctico en un fichero falla todo, acumulación sobre memoria previa |

### `test/test_motor.py`

| Clase | Tests | Qué verifica |
|---|---|---|
| `TestEsVariable` | 5 | Distinción literal/variable por mayúscula inicial |
| `TestUnificacion` | 7 | Literales iguales, distintos, variable libre, coherencia, incoherencia, misma variable en dos posiciones |
| `TestResolutor` | 4 | Cadena directa, en cadena (`P→X→valor`), ciclo infinito (terminación garantizada) |
| `TestSustituir` | 3 | Sustitución en sujeto, en todos los campos, sin sustitución |
| `TestEvaluarRestricciones` | 11 | Todos los operadores (`<`,`<=`,`>`,`>=`,`=`), variable no resuelta, conjunción AND |
| `TestEncadenamientoAdelante` | 10 | Tareas 1-5 con `cluedo.txt`: arma homicida, sospechosos, culpable, inocentes, certezas, idempotencia |
| `TestEncadenamientoAtras` | 7 | Hipótesis confirmada/denegada, variable libre, predicado inexistente, hecho base, hecho falso |
| `TestConsultarHechos` | 6 | Hecho existente, certeza correcta, hecho inexistente, variable, certeza difusa, ontología completa |
| `TestRobustezBucleCircular` | 2 | Forward y backward chaining no colapsan con reglas circulares |
| `TestRobustezCadenaProfunda` | 3 | Cadena de 3 saltos resuelta en forward y backward |
| `TestFronterasMatemáticas` | 9 | Fronteras exactas de todos los operadores aritméticos |
| `TestLogicaDifusa` | 6 | T-norma mínimo, multiplicación por certeza de regla, no degradación, coherencia forward/backward |
| `TestPrecedenciaReglas` | 4 | Ordenación por precedencia en memoria, reglas con misma precedencia, evaluación en orden |

---

## Casos de prueba funcionales sobre cluedo.txt

Los siguientes tests reproducen el razonamiento real del sistema con la KB completa. Son los tests más representativos para demostrar el funcionamiento end-to-end:

### Tarea 1 — Identificación del arma homicida

```python
# El candelabro debe deducirse como arma homicida tras forward chaining
h = _buscar(memoria, "candelabro", "es_arma_homicida", "crimen")
assert h is not None
assert round(h.certeza, 2) == 0.77
```

**Por qué pasa:** el candelabro tiene sangre (0.85) + huellas (0.90) en la escena, es contundente y pesado, y la víctima tiene contusión. Todas las condiciones se cumplen.

### Tarea 4 — Descarte por coartada

```python
# Doctor Orquideo sale a las 21:30 < 22:15 → tiene coartada → inocente
h = _buscar(memoria, "doctor_orquideo", "es_inocente", "crimen")
assert h is not None
assert h.certeza == 1.0
```

### Tarea 3 — Culpable deducido

```python
# El coronel es culpable (confirmado por cámara + sospechoso fuerte)
h = _buscar(memoria, "coronel_mostaza", "es_culpable", "crimen")
assert h is not None
assert round(h.certeza, 2) == 0.46
```

### Backward chaining sobre culpable

```python
# Backward chaining debe encontrar al culpable sin forward previo
resultados = list(motor.encadenamiento_hacia_atras(
    Tripleta("X", "es_culpable", "crimen")
))
valores = {sust["X"] for sust, _ in resultados if "X" in sust}
assert "coronel_mostaza" in valores
```
