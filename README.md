# Sistema Experto — Proyecto SBC Extraordinaria 2025/26

Motor de inferencia basado en reglas de producción implementado en Python. Soporta encadenamiento hacia adelante y hacia atrás, restricciones aritméticas y lógica difusa. Incluye una base de conocimiento completa para resolver el caso detectivesco de la **Mansión Blackwood** (temática *Cluedo*).

## Documentación

| Documento | Contenido |
|---|---|
| [doc/arquitectura.md](doc/arquitectura.md) | Módulos, algoritmos, gramática EBNF, decisiones de diseño |
| [doc/dominio-cluedo.md](doc/dominio-cluedo.md) | El caso, la KB, la cadena de inferencia y las certezas |
| [doc/manual-usuario.md](doc/manual-usuario.md) | Instalación, referencia de comandos y tutorial paso a paso |
| [doc/tareas-y-pruebas.md](doc/tareas-y-pruebas.md) | Tareas resueltas y descripción de la suite de tests |

## Estructura del repositorio

```
fdi-sbc-25DAA/
├── doc/           ← documentación técnica
├── kb/            ← bases de conocimiento (.txt)
│   └── cluedo.txt ← caso principal (100 hechos, 46 reglas)
├── sbc/           ← código fuente
│   ├── parser.py  ← gramática EBNF con pyparsing
│   ├── memory.py  ← gestión de hechos y reglas
│   ├── engine.py  ← motor de inferencia (forward + backward)
│   └── cli.py     ← consola REPL interactiva
└── test/          ← 150 tests unitarios y funcionales
```

## Instalación y ejecución

```bash
uv sync                  # instala dependencias
uv run -m sbc.cli        # arranca la consola interactiva
uv run python -m unittest discover test   # ejecuta los tests
```

## Uso rápido

```
SBC> cargar!
SBC> descubrir!
SBC> X es_culpable crimen?
  X = coronel_mostaza  [Certeza: 0.46]
SBC> razona si X es_arma_homicida crimen?
  X = candelabro       [Certeza: 0.77]
```

## Comandos principales

| Comando | Acción |
|---|---|
| `cargar! <ruta>` | Carga una base de conocimiento |
| `descubrir!` | Encadenamiento hacia adelante (satura la memoria) |
| `razona si <tripleta>?` | Encadenamiento hacia atrás (demuestra hipótesis) |
| `<tripleta>?` | Consulta directa en memoria |
| `<tripleta>.` / `no <tripleta>.` | Aserción / retractación de hechos |
| `memoria!` | Muestra el estado actual de la memoria |