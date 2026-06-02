# Sistema Experto - Proyecto SBC Extraordinaria 2025/26

Implementación en Python de un Sistema Experto basado en reglas de producción. El sistema incluye un motor de inferencia con soporte para encadenamiento hacia adelante, encadenamiento hacia atrás, evaluación de restricciones aritméticas y propagación de incertidumbre mediante lógica difusa.

## Documentación del Proyecto

Las justificaciones teóricas, la arquitectura del software y las decisiones de diseño técnico (manejo de colisiones de espacios de nombres, prevención de bucles recursivos y algoritmos de unificación) se encuentran detalladas en el directorio `doc/`.

## Descripción del Sistema

El proyecto está modularizado en cuatro componentes principales:

* **Parser Analizador (`sbc.parser`):** Implementado con `pyparsing`, interpreta una gramática EBNF estricta para leer la base de conocimiento, soportando variables, literales, extensiones difusas y restricciones temporales/matemáticas.
* **Memoria de Trabajo (`sbc.memory`):** Estructura encargada de almacenar y gestionar la base de conocimiento empírico (hechos) y deductivo (reglas), permitiendo la aserción y revocación dinámica de afirmaciones en tiempo de ejecución.
* **Motor de Inferencia (`sbc.engine`):** Núcleo lógico que implementa los algoritmos de resolución. Soporta deducción iterativa (hacia adelante), demostración de hipótesis mediante recursividad (hacia atrás), unificación profunda de variables y evaluación de álgebra booleana y difusa (norma T del mínimo y producto escalado).
* **Interfaz de Usuario (`sbc.cli`):** Consola interactiva (REPL) para la ejecución de comandos, consultas, e interrogación del motor, con visualización detallada de las cadenas deductivas y las certezas matemáticas.

## Estructura del Repositorio

```text
.
├── doc/                # Documentación técnica y decisiones de diseño
├── kb/                 # Bases de conocimiento (archivos .txt con ontología y reglas)
├── sbc/                # Código fuente principal del módulo
│   ├── __init__.py
│   ├── cli.py          # Bucle de la consola interactiva
│   ├── engine.py       # Algoritmos de inferencia y resolución
│   ├── memory.py       # Gestión del estado y base de datos interna
│   └── parser.py       # Definición de la gramática y tokens EBNF
├── .gitignore          # Reglas de exclusión para Git
└── README.md           # Presentación del repositorio
```

## Requisitos y Ejecución

El sistema está desarrollado para entornos **Python 3.10+**. Se recomienda gestionar el entorno y la ejecución a través de herramientas estándar como `uv` o entornos virtuales clásicos.

Para ejecutar el sistema en modo interactivo desde la raíz del repositorio:

```bash
uv run -m sbc.cli
```

## Comandos de la CLI

| Comando | Descripción |
| :--- | :--- |
| `cargar! <ruta>` | Carga en memoria una base de conocimiento desde un archivo (ej. `cargar! kb/caso.txt`). |
| `descubrir!` | Ejecuta el Motor de Inferencia en modo **Encadenamiento Hacia Adelante** para deducir todos los hechos posibles hasta la estabilización del sistema. |
| `razona si <consulta>?`| Ejecuta el **Encadenamiento Hacia Atrás** para demostrar una hipótesis. Soporta resolución de variables completas o parciales (ej. `razona si X es asesino?`). |
| `<consulta>?` | Realiza una búsqueda unificada directa en la Memoria de Trabajo sin disparar reglas deductivas. |
| `<hecho>.` | Aserción: Introduce un nuevo hecho manualmente en la memoria. |
| `no <hecho>.` | Revocación: Elimina un hecho existente de la memoria de trabajo. |
| `memoria!` | Muestra el estado actual de la memoria (hechos cargados/deducidos con sus certezas y reglas activas). |
| `ayuda!` | Imprime el manual de uso de la consola. |
| `salir!` | Termina el proceso de forma segura. |

## Ejemplos de Uso

**1. Carga de información y deducción masiva (Hacia adelante)**
```text
SBC> cargar! kb/test_limites.txt
SBC> descubrir!
SBC> memoria!
```

**2. Consulta directa a memoria (con variables)**
```text
SBC> X tiene_coartada no?
```

**3. Demostración de hipótesis (Hacia atrás)**
```text
SBC> razona si coronel_mostaza es asesino?
SBC> razona si X es asesino?
```

**4. Modificación de la memoria en caliente**
```text
SBC> candelabro esta_en biblioteca.
SBC> no coronel_mostaza esta_en salon.
```