from pathlib import Path
from typing import List
from loguru import logger
from pyparsing import ZeroOrMore, ParseException

# Importamos las piezas que creamos en el parser
from sbc.parser import Hecho, Regla, hecho_parser, reglas_parser, comentario

# Creamos un súper-parser capaz de leer un archivo entero línea a línea
# Un archivo es "Cero o más" declaraciones (que pueden ser reglas o hechos)
declaracion = reglas_parser | hecho_parser
archivo_parser = ZeroOrMore(declaracion)
# Necesario para que parse_all=True no falle al encontrar comentarios al
# final del archivo (el ZeroOrMore top-level no hereda el ignore de sus hijos)
archivo_parser.ignore(comentario)


class Memoria:
    def __init__(self):
        # Aquí guardamos el estado del conocimiento
        self.hechos: List[Hecho] = []
        self.reglas: List[Regla] = []

    def cargar_archivo(self, ruta_archivo: str | Path) -> bool:
        """Lee un fichero txt y carga su conocimiento en memoria."""
        ruta = Path(ruta_archivo)

        if not ruta.exists():
            logger.error(f"No se ha encontrado el archivo de conocimiento: {ruta}")
            return False

        try:
            # Obligamos a leer en UTF-8, requisito técnico estricto de las normas
            texto = ruta.read_text(encoding="utf-8")

            # parse_all=True es vital: si hay una sola letra mal puesta en el txt,
            # en vez de ignorarla, pyparsing lanzará una excepción para avisarnos.
            resultados = archivo_parser.parse_string(texto, parse_all=True)

            # Clasificamos lo que el parser ha leído
            for item in resultados:
                if isinstance(item, Hecho):
                    self.agregar_hecho(item)
                elif isinstance(item, Regla):
                    self.agregar_regla(item)

            logger.success(
                f"Cargados {len(self.hechos)} hechos y {len(self.reglas)} reglas desde {ruta.name}"
            )
            return True

        except ParseException as e:
            # Si el profesor mete un txt con errores a propósito para probar tu programa,
            # esto imprimirá exactamente en qué línea y columna está el error. ¡Le encantará!
            logger.error(
                f"Error de sintaxis en {ruta.name} (Línea {e.lineno}, Columna {e.col}):\n{e.line}"
            )
            return False

    def agregar_regla(self, nueva_regla: Regla):
        """Añade una regla evitando duplicados exactos. Mantiene el orden por precedencia descendente."""
        for r in self.reglas:
            if (
                r.consecuente == nueva_regla.consecuente
                and r.antecedentes == nueva_regla.antecedentes
            ):
                return  # Si es idéntica, la ignoramos silenciosamente
        self.reglas.append(nueva_regla)
        # El motor itera self.reglas en orden: las reglas de mayor precedencia
        # se evalúan primero sin necesidad de ningún cambio en el motor.
        self.reglas.sort(key=lambda r: r.precedencia, reverse=True)

    def agregar_hecho(self, nuevo_hecho: Hecho) -> bool:
        """Añade un hecho a la memoria, o lo revoca si es una negación. Devuelve True si tuvo efecto."""

        # 1. ¿Es una orden de revocación? (Ej: "no coronel_mostaza esta_en biblioteca.")
        if nuevo_hecho.negado:
            longitud_original = len(self.hechos)
            self.hechos = [h for h in self.hechos if h.tripleta != nuevo_hecho.tripleta]

            if len(self.hechos) < longitud_original:
                logger.info(
                    f"Hecho revocado: {nuevo_hecho.tripleta.sujeto} {nuevo_hecho.tripleta.predicado} {nuevo_hecho.tripleta.objeto}."
                )
                return True
            return False  # <--- AÑADIDO: Si la lista mide lo mismo, no borró nada.

        # 2. Es una afirmación normal. Comprobamos si ya existía para actualizar su certeza.
        for h in self.hechos:
            if h.tripleta == nuevo_hecho.tripleta:
                if h.certeza != nuevo_hecho.certeza:
                    h.certeza = nuevo_hecho.certeza
                    logger.debug(
                        f"Hecho actualizado con nueva certeza [{h.certeza}]: {h.tripleta.sujeto}"
                    )
                return True  # <--- AÑADIDO: Salimos devolviendo éxito

        # 3. Si es totalmente nuevo, lo añadimos al final de la lista.
        self.hechos.append(nuevo_hecho)
        return True  # <--- AÑADIDO: Salimos devolviendo éxito

    def limpiar(self):
        """Borra toda la memoria (útil si el usuario quiere reiniciar el sistema)."""
        self.hechos.clear()
        self.reglas.clear()
        logger.info("Memoria de trabajo borrada por completo.")
