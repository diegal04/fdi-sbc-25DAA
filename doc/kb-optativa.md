# Base de Conocimiento de Reciclaje

## Nota sobre esta KB

Esta base de conocimiento fue desarrollada como **trabajo optativo en clase** para obtener crédito extra. Se incluye en el proyecto de recuperación extraordinaria para demostrar la versatilidad y robustez del motor de inferencia. El sistema ha sido validado y **funciona correctamente** con esta KB, procesando consultas complejas sobre la gestión de residuos, aplicando encadenamiento hacia adelante y hacia atrás, y manejando restricciones lógicas sin problemas. La documentación completa sobre su estructura y uso se encuentra en este documento.

## Descripción

Este repositorio contiene una **Base de Conocimiento (Knowledge Base)** diseñada para automatizar la toma de decisiones en la gestión de residuos en una empresa. Utiliza un enfoque basado en reglas (sintaxis declarativa) para determinar el destino óptimo de un residuo basándose en su composición y propiedades, siguiendo la **Jerarquía de Residuos** europea (Minimización > Reutilización > Reciclaje > Valorización > Eliminación).

Este módulo es agnóstico a la tecnología: define la *lógica*, no la implementación de software.

Este problema es críticamente importante porque la gestión ineficiente de residuos representa tanto una emergencia ambiental global (contribuyendo significativamente a la contaminación y al cambio climático) como una enorme oportunidad económica desaprovechada dentro del modelo de economía circular. Automatizar esta decisión con conocimiento estructurado permite reducir el impacto ambiental, generar ahorros sustanciales, garantizar el cumplimiento legal y transformar un pasivo operativo en una ventaja competitiva sostenible.

## Estructura del Proyecto

El conocimiento está desacoplado en tres capas lógicas:

### 1. Capa de Estrategia y Flujo

Define **qué hacer** con los residuos y **cuánto** se genera. Contiene:

* **`kbResiduosGenerados`:** Información sobre los residuos generados por la empresa y sus cantidades.
* **`kbJerarquia`:** Define el orden de preferencia de los tratamientos.
* **`kbMedicionPlanes`:** Define:
  * **Planes de Acción:** Reglas lógicas (`IF-THEN`) que asignan planes (e.g., `Plan de Valorización Energética`).
  * **Destinos Finales:** Mapeo a contenedores (Azul, Amarillo, Marrón) o plantas específicas.
  * **Beneficios de la empresas**

### 2. Capa de Datos y Propiedades (`kbSeleccion`)

Define **qué son** los residuos y su clasificación. Actúa como base de datos de materiales:

* **Composición:** Mapeo de residuos a materiales (e.g., `toner -> sustancias_toxicas`).
* **Propiedades:** Atributos físicos (biodegradable, manchado, estado).
* **Clasificación:** Reglas de seguridad (Peligroso, Inerte, RAEE).
* **Potencial:** Determina si un material es técnicamente reciclable, reutilizable o minimizable.

### 3. Información del usuario/empresa

Define las prioridades y los contratos que tiene la empresa que pueden ser configurados por el usuario.

* **Contratos con plantas:** Afectará a si los residuos de la empresa pueden destinarse o no a la planta de procesamiento correspondiente como opción. Para la empresa ideada, tendrá todos los contratos activos.
* **Prioridades:** Afectará a si la empresa tratará los residuos de forma que se pueda reducir más el impacto medio ambiental o no. Para la empresa en cuestión, tiene que su prioridad es minimizar el impacto.

---

## Cómo Configurar (Inventario de Empresa)

Actualmente, en `kbResiduosGenerados` plasma los datos de los residuos que se genera normalmente o de media en la empresa, de haber **outliers** (por ejemplo, ese intervalo de tiempo se han generado menos `cajas_embalaje_carton` de la cantidad usual (`alta`)). El usuario puede editar esta información de dos formas:

1. Editar directamente `kbResiduosGenerados` para adaptar a lo que haya generado la empresa en ese intervalo.
2. Hacer consultas de añadir hechos o revocación de hechos directamente desde el la interfaz del motor de inferencia.

> **Nota:** Si eliminas una línea en `kbResiduosGenerados`, el sistema dejará de procesar ese residuo, aunque las definiciones sigan existiendo en `kbSeleccion`.

---

## Lógica de Inferencia

El sistema funciona cruzando datos automáticamente entre los dos archivos. Ejemplo de trazabilidad:

1. **Input:** En `kbResiduosGenerados` se define: `restos_comida_comedor cantidad alta`.
2. **Dato:** El sistema detecta en `kbSeleccion` que `restos_comida_comedor` es `materia_organica` y `biodegradable`.
3. **Regla:** Al ser orgánico y de cantidad alta (definido en `kbMedicionPlanes`), se activa el **Plan de Valorización** (además de cumplir otros antecedentes como que no es minimizable, no es reciclable ni reutilizable) y también valorará si la empresa tiene prioridad minimizar el impacto medioambiental o reducir el coste.
4. **Inferencia:** * Destino -> `planta_digestion_anaerobica`. Para que se pueda llevar los residuos a la `planta_digestion_anaerobica`, necesitamos que se cumpla `empresa contrato planta_anaerobica`.
    * Output -> `biogas` + `digestato`.
    * Beneficio -> `reduccion_impacto_medioambiental`.

## Cobertura de Residuos

Actualmente, la KB soporta reglas para:

| Categoría | Ejemplos Soportados |
| :--- | :--- |
| **Envases** | Cartón, Plástico PET, Vidrio, Latas. |
| **Orgánico** | Restos de comedor, Biomasa, Poda. |
| **Peligrosos** | Aceites usados, Baterías, Disolventes, Fluorescentes. |
| **RAEE** | Ordenadores, Tóners, Electrodomésticos. |
| **Industrial** | Palets, Madera, Chatarra, Escombros (RCD). |

## Ejemplos de consultas

Ambas pruebas con la base de conociemiento actual.
Prueba 1:

```bash
  usuario define_prioridad minimizacion_impacto ?
  T

  razona si empresa prioridad minimizacion_impacto ?
  T

  empresa reduce impacto_medioambiental ?
  F

  razona si empresa reduce impacto_medioambiental ?
  T

  no usuario define_prioridad minimizacion_impacto .

  usuario define_prioridad reduccion_costes .

  usuario define_prioridad minimizacion_impacto ?
  F

  razona si empresa prioridad minimizacion_impacto ?
  F

  razona si empresa prioridad reduccion_costes ?
  T

  razona si empresa reduce impacto_medioambiental ?
  F
```

Prueba 2:

```bash

  usuario define_contrato planta_reciclaje ?
  T

  papel_taller cantidad Cuanto ?
  baja

  cajas_embalaje_carton cantidad Cuanto ?
  alta

  razona si papel_taller destino contenedor_azul ?
  T

  razona si cajas_embalaje_carton destino contenedor_azul ?
  F

  razona si cajas_embalaje_carton destino planta_reciclaje ? # Por las cantidades, se llevan a plantas de reciclaje
  T

  no usuario define_contrato planta_reciclaje .

  usuario define_no_contrato planta_reciclaje .

  razona si papel_taller destino contenedor_azul ?
  T

  razona si cajas_embalaje_carton destino contenedor_azul ? # Como no podemos llevarlos a la planta de reciclaje, una opción ya sí es tirarlos en los contenedores azules
  T

  razona si cajas_embalaje_carton destino planta_reciclaje ?
  F

```

## Participantes

Este proyecto ha sido desarrollado por:

* **Diego Alonso**
* **Álvaro Arbona**
* **Vega García**
* **Alicia Pereda**
* **Iris Wang**