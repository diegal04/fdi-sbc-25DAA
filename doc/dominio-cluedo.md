# Dominio: La Mansión Blackwood

## Índice
1. [Descripción del caso](#descripción-del-caso)
2. [Entidades del dominio](#entidades-del-dominio)
3. [Estructura de la base de conocimiento](#estructura-de-la-base-de-conocimiento)
4. [Datos del crimen](#datos-del-crimen)
5. [Cadena de inferencia completa](#cadena-de-inferencia-completa)
6. [Certezas calculadas paso a paso](#certezas-calculadas-paso-a-paso)
7. [Mejoras implementadas sobre el diseño inicial](#mejoras-implementadas-sobre-el-diseño-inicial)
8. [Resumen de resultados](#resumen-de-resultados)

---

## Descripción del caso

La KB `kb/cluedo.txt` modela un caso detectivesco ambientado en el universo de *Cluedo*. En la **Mansión Blackwood**, una víctima ha sido hallada muerta en la biblioteca con una contusión. El sistema debe razonar a partir de evidencias físicas, ubicaciones, coartadas y móviles para identificar al culpable, el arma y el método.

El motor parte de **100 hechos** y **46 reglas** y es capaz de derivar automáticamente la culpabilidad con un grado de certeza cuantificado.

---

## Entidades del dominio

### Sospechosos (6)

| Nombre | Profesión | Carácter |
|---|---|---|
| `coronel_mostaza` | militar | impulsivo |
| `senora_escarlata` | actriz | calculador |
| `doctor_orquideo` | médico | calculador |
| `senora_pavo_real` | aristócrata | codiciosa |
| `reverendo_verde` | clérigo | nervioso |
| `profesora_ciruelo` | científica | calculador |

### Armas (6)

| Arma | Tipo de daño | Peso (g) | Pesada |
|---|---|---|---|
| `candelabro` | contundente | 1800 | ✓ |
| `llave_inglesa` | contundente | 900 | ✓ |
| `tubo_plomo` | contundente | 2200 | ✓ |
| `daga` | cortante | 300 | — |
| `cuerda` | estrangulante | 250 | — |
| `revolver` | de fuego | 850 | ✓ |

### Habitaciones (8 + jardín)

`biblioteca`, `salon`, `cocina`, `estudio`, `bodega`, `invernadero`, `pasillo`, `galeria` y (exterior) `jardin`.

El plano conecta las habitaciones formando una red:
```
jardin ← invernadero ← salon ← cocina
                         ↕
                       pasillo ↔ biblioteca ↔ estudio
                         ↕
                       bodega
                         ↕
                       galeria
```

---

## Estructura de la base de conocimiento

La KB está organizada en 15 secciones numeradas:

| Sección | Nombre | Tipo | Hechos/Reglas |
|---|---|---|---|
| 1 | Ontología | Hechos | 20 `es_tipo` |
| 2 | Propiedades de armas | Hechos | 12 propiedades fijas |
| 3 | Perfil de sospechosos y plano | Hechos | 22 (profesión, carácter, adyacencia) |
| 4 | Datos del crimen | Hechos | 3 (ubicación víctima, herida, hora) |
| 5 | Ubicación en el crimen | Hechos | 6 ubicaciones |
| 6 | Cronología (coartadas) | Hechos | 12 (llegada/salida) |
| 7 | Evidencia física | Hechos | 14 (ubicación armas, sangre, huellas) |
| 8 | Móviles | Hechos | 11 (testamento, deudas, conflictos, cámaras) |
| 8b | Perfil psicológico y capacidad | Reglas | 5 (derivadas de S3) |
| 9 | Clasificación de armas | Reglas | 5 |
| 10 | Identificación del arma homicida | Reglas | 6 |
| 11 | Accesibilidad espacial | Reglas | 4 (incluyendo transitiva) |
| 12 | Presencia y coartada | Reglas | 7 |
| 13 | Móvil | Reglas | 4 |
| 14 | Vinculación física | Reglas | 1 |
| 15 | Sospecha y acusación | Reglas | 9 |

---

## Datos del crimen

- **Víctima hallada en:** `biblioteca`
- **Tipo de herida:** `contusion`
- **Hora del crimen:** `2215` (22:15)

### Coartadas por registro horario

| Sospechoso | Llegada | Salida | ¿Presente a las 22:15? | Resultado |
|---|---|---|---|---|
| `coronel_mostaza` | 20:00 | 23:00 | ✓ | Sin coartada |
| `senora_escarlata` | 21:00 | 24:00 | ✓ | Sin coartada |
| `doctor_orquideo` | 19:00 | **21:30** | ✗ | **Coartada — inocente** |
| `senora_pavo_real` | 21:30 | 23:59 | ✓ | Sin coartada |
| `reverendo_verde` | 20:00 | **22:00** | ✗ | **Coartada — inocente** |
| `profesora_ciruelo` | 18:00 | 23:00 | ✓ | Sin coartada |

### Evidencia física

| Arma | Ubicación | Sangre | Huellas |
|---|---|---|---|
| `candelabro` | biblioteca | ✓ (0.85) | ✓ (0.90) |
| `cuerda` | biblioteca | — | ✓ (0.60) |
| `llave_inglesa` | estudio | ✓ (0.30) | — |
| `daga` | invernadero | ✓ (0.50) | — |
| `tubo_plomo` | bodega | — | — |
| `revolver` | salon | — | — |

### Huellas dactilares identificadas

| Persona | Arma | Certeza |
|---|---|---|
| `coronel_mostaza` | `candelabro` | 0.88 |
| `profesora_ciruelo` | `candelabro` | 0.55 |
| `reverendo_verde` | `cuerda` | 0.65 |


---

Aquí tienes una versión mucho más directa, concisa y al grano. Perfecta para un "vistazo rápido" o para llevarla como guion mental a la defensa:

---

## Lógica de Resolución: El Caso Blackwood

El motor de inferencia procesa los hechos a través de un **embudo deductivo** de cuatro fases, utilizando lógica difusa para arrastrar la certeza de las pruebas hasta la conclusión final.

### 1. Descarte Temprano (Prioridad Máxima)

Antes de buscar culpables, el sistema poda el árbol de búsqueda descartando inocentes. Utiliza matemáticas (`<`, `>`) para cruzar la hora del crimen con los registros de entrada y salida de la mansión. Quien no estaba en el edificio recibe el estado `es_inocente` y deja de ser procesado.

### 2. Búsqueda del Arma Homicida

El motor deduce qué objeto se usó en el crimen cruzando tres factores:

* **Capacidad de daño:** Propiedades intrínsecas del arma (ej. peso > 800g = contundente) vs. la herida de la víctima.
* **Evidencia forense:** Presencia de sangre y huellas.
* **Conclusión:** Se establece el hecho `es_arma_homicida`.

### 3. El Embudo de Acusación (Niveles 1 a 3)

Los personajes sin coartada pasan por tres niveles de sospecha progresiva:

* **Nivel 1 (Sospechoso Débil - Oportunidad):** Personas en la mansión que tenían acceso físico a la escena y además poseen un móvil, capacidad violenta o perfil impulsivo.
* **Nivel 2 (Sospechoso Fuerte - Evidencia):** Requiere ser sospechoso de Nivel 1 y estar **vinculado físicamente** al crimen (tener sus huellas dactilares exactamente en el objeto declarado como arma homicida).
* **Nivel 3 (Culpable - Confirmación):** El cierre del caso. Exige ser de Nivel 2 y estar confirmado en la escena por un testigo/cámara, o tener un móvil/premeditación irrefutable.

---

## Resumen de resultados

Tras ejecutar el encadenamiento hacia adelante sobre `kb/cluedo.txt`:

| Conclusión | Certeza |
|---|---|
| `candelabro es_arma_homicida crimen` | **0.77** |
| `coronel_mostaza es_culpable crimen` | **0.46** |
| `profesora_ciruelo es_culpable crimen` | **0.42** |
| `doctor_orquideo es_inocente crimen` | **1.00** |
| `reverendo_verde es_inocente crimen` | **1.00** |

El sistema identifica al `coronel_mostaza` como principal sospechoso (certeza 0.46), seguido de cerca por `profesora_ciruelo` (certeza 0.42), con el **candelabro** como arma homicida (certeza 0.77).
