# Manual de Usuario

## Índice
1. [Requisitos e instalación](#requisitos-e-instalación)
2. [Iniciar el sistema](#iniciar-el-sistema)
3. [Referencia de comandos](#referencia-de-comandos)
4. [Tutorial: caso de la Mansión Blackwood](#tutorial-caso-de-la-mansión-blackwood)
5. [Tipos de consulta en detalle](#tipos-de-consulta-en-detalle)
6. [Sintaxis de la base de conocimiento](#sintaxis-de-la-base-de-conocimiento)
7. [Crear tu propia base de conocimiento](#crear-tu-propia-base-de-conocimiento)

---

## Requisitos e instalación

**Requisitos:**
- Python 3.13 o superior
- [`uv`](https://docs.astral.sh/uv/) (gestor de entornos y paquetes)

**Instalación:**
```bash
# Clonar el repositorio
git clone https://github.com/diegal04/fdi-sbc-25DAA.git
cd fdi-sbc-25DAA

# Instalar dependencias (uv crea el entorno virtual automáticamente)
uv sync
```

---

## Iniciar el sistema

```bash
uv run -m sbc.cli
```

Al arrancar se muestra el prompt interactivo:

```
=== SISTEMA EXPERTO: AGENCIA DE DETECTIVES ===
Escribe un hecho (.), una consulta (?), o un comando (cargar!, descubrir!, memoria!, ayuda!, salir!)

SBC>
```

Escribe `ayuda!` en cualquier momento para ver un resumen de comandos dentro del propio sistema.

---

## Referencia de comandos

### Comandos de sistema

| Comando | Descripción |
|---|---|
| `cargar! <ruta>` | Carga una base de conocimiento desde un **fichero** `.txt` o desde una **carpeta** (concatena en orden alfabético todos los `.txt` que contiene). Ejemplo: `cargar! KB.txt` o `cargar! kb/`. Si se omite la ruta usa `kb/cluedo.txt` por defecto. |
| `descubrir!` | Ejecuta el **encadenamiento hacia adelante** y satura la memoria con todos los hechos deducibles. |
| `memoria!` | Muestra todos los hechos actualmente en memoria (con sus certezas) y la lista de reglas cargadas. |
| `ayuda!` | Muestra el manual de ayuda dentro del sistema. |
| `salir!` | Cierra el programa. |

### Aserción y retractación de hechos

```
# Añadir un hecho con certeza 1.0
SBC> coronel_mostaza esta_en biblioteca.

# Añadir un hecho con incertidumbre
SBC> candelabro tiene_sangre si. [ 0.85 ]

# Retirar un hecho de la memoria
SBC> no coronel_mostaza esta_en biblioteca.
```

### Consultas

| Tipo | Sintaxis | Comportamiento |
|---|---|---|
| **Directa** | `sujeto predicado objeto?` | Busca en la memoria de trabajo sin disparar reglas. |
| **Con variable** | `X predicado objeto?` | Devuelve todos los valores que X puede tomar. |
| **Deducción** | `razona si sujeto predicado objeto?` | Activa el encadenamiento hacia atrás para demostrar la hipótesis a partir de reglas. |
| **Variable + deducción** | `razona si X predicado objeto?` | Enumera todas las soluciones posibles mediante backward chaining. |

---

## Tutorial: caso de la Mansión Blackwood

Este tutorial resuelve el caso completo paso a paso.

### Paso 1 — Cargar la base de conocimiento

```
SBC> cargar! kb/cluedo.txt
```

También puedes apuntar directamente a la carpeta; se cargarán todos los `.txt` en orden alfabético:

```
SBC> cargar! kb/kb-optativa
```

Salida esperada:
```
✓ Cargados 100 hechos y 46 reglas desde cluedo.txt
```

### Paso 2 — Ejecutar el motor de inferencia

```
SBC> descubrir!
```

El motor encadena hacia adelante hasta el punto fijo. Verás en la salida algo como:

```
Iniciando motor de inferencia (Encadenamiento hacia adelante)...
¡Eureka! El detective ha deducido 79 nuevos hechos.
```

### Paso 3 — Consultar el arma homicida

```
SBC> X es_arma_homicida crimen?
```

Salida:
```
X = candelabro   [Certeza: 0.77]
X = llave_inglesa [Certeza: 0.19]
```

El candelabro está en la biblioteca (donde fue hallada la víctima), tiene sangre (certeza 0.85) y huellas (0.90), y puede causar contusión. Es el arma con más evidencia vinculante.

### Paso 4 — Ver quién es culpable

```
SBC> X es_culpable crimen?
```

Salida:
```
X = coronel_mostaza   [Certeza: 0.46]
X = profesora_ciruelo [Certeza: 0.42]
```

### Paso 5 — Verificar un inocente

```
SBC> doctor_orquideo es_inocente crimen?
```

Salida:
```
VERDADERO (Certeza: 1.00)
```

El doctor salió de la mansión a las 21:30, antes de que ocurriera el crimen (22:15), por lo que tiene coartada probada.

### Paso 6 — Razonar hacia atrás sobre un sospechoso

```
SBC> razona si coronel_mostaza es_culpable crimen?
```

Salida:

```
HIPÓTESIS CONFIRMADA (Certeza: 0.46)
```

### Paso 7 — Añadir nueva evidencia en caliente

Puedes añadir hechos durante la sesión sin recargar el archivo:

```
SBC> senora_escarlata huellas_en revolver. [ 0.95 ]
SBC> descubrir!
SBC> senora_escarlata es_culpable crimen?
```

### Paso 8 — Inspeccionar la memoria

```
SBC> memoria!
```

Muestra todos los hechos (con certeza) y reglas cargadas, útil para depurar el estado del sistema.

---

## Tipos de consulta en detalle

### Consulta directa vs. razona si

```
# Consulta directa: solo busca en lo que ya está en memoria
SBC> X es_culpable crimen?

# Si aún no has ejecutado descubrir!, la memoria no tendrá hechos derivados
# y la consulta devuelve vacío.

# Backward chaining: deduce en el acto, sin necesitar descubrir! previo
SBC> razona si X es_culpable crimen?
```

### Variables en las tres posiciones

```
# Quién está en la biblioteca
SBC> X ubicacion_crimen biblioteca?

# Qué propiedad tiene el candelabro
SBC> candelabro X Y?

# Qué objetos conectan con el pasillo
SBC> X conecta_con pasillo?
```

### Consulta con literales parciales

```
# ¿Cuándo ocurrió el crimen?
SBC> crimen ocurrio_a X?

# ¿Qué armas están en la biblioteca?
SBC> X esta_en biblioteca?
```

---

## Sintaxis de la base de conocimiento

Los archivos `.txt` de conocimiento siguen esta gramática:

### Hechos

```
# Hecho simple (certeza 1.0)
coronel_mostaza ubicacion_crimen biblioteca.

# Hecho con certeza difusa
candelabro tiene_sangre si.  [ 0.85 ]

# Negación (retracta el hecho si está en memoria)
no coronel_mostaza ubicacion_crimen salon.

# Comentario (ignorado por el parser)
# Esto es un comentario
```

### Reglas

```
# Regla simple
A es pesada <- A peso_gramos G. [ G > 800 ]

# Regla con certeza
A puede_causar contusion <- A es contundente, A es pesada. [ 0.90 ]

# Regla con precedencia alta (evaluar antes)
P descartado crimen <- P tiene_coartada crimen. [ 999 ]

# Regla con precedencia y certeza
P es_culpable crimen <- P es_sospechoso_fuerte crimen,
                         P confirmado_en_escena crimen. [ 800; 0.95 ]

# Regla con restricción aritmética
P estuvo_en_mansion crimen <- P llega_mansion LlegaH,
                               P sale_mansion SaleH. [ LlegaH <= 2215; SaleH >= 2215 ]
```

### Extensiones entre corchetes `[ ]`

| Tipo | Formato | Ejemplo | Descripción |
|---|---|---|---|
| Certeza | `0.xx` o `1` | `[ 0.85 ]` | Grado de confianza (0.0–1.0) |
| Precedencia | 3 dígitos exactos | `[ 999 ]` | Orden de evaluación (0–999, mayor primero) |
| Restricción | `VARIABLE op NUMERO` | `[ G > 800 ]` | Filtro aritmético |
| Combinados | separados por `;` | `[ 800; 0.95 ]` | Precedencia y certeza juntos |

