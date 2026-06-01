from typing import List, Dict, Any, Generator, Tuple
from loguru import logger
from sbc.parser import Tripleta, Hecho, Regla, Restriccion
from sbc.memory import Memoria

# Un diccionario de sustituciones es simplemente { "Variable": "Valor" }
Sustitucion = Dict[str, str]

def es_variable(termino: str) -> bool:
    """Según tu EBNF, las variables empiezan siempre por mayúscula."""
    return termino[0].isupper()

def unificar(patron: Tripleta, hecho: Tripleta, sust_previa: Sustitucion) -> Sustitucion | None:
    """
    Compara un patrón (con posibles variables) con un hecho real.
    Devuelve un diccionario con las variables descubiertas, o None si no encajan.
    """
    sust = sust_previa.copy()
    
    # Comparamos sujeto, predicado y objeto de uno en uno
    for p, h in zip([patron.sujeto, patron.predicado, patron.objeto], 
                    [hecho.sujeto, hecho.predicado, hecho.objeto]):
        if es_variable(p):
            if p in sust:
                # Si la variable ya tenía un valor asignado antes, DEBE coincidir
                if sust[p] != h:
                    return None
            else:
                # Si es una variable nueva, guardamos su valor
                sust[p] = h
        elif p != h:
            # Si es un literal (ej. "biblioteca") y no coinciden, fallamos
            return None
            
    return sust

def sustituir(tripleta: Tripleta, sust: Sustitucion) -> Tripleta:
    """Crea una nueva tripleta reemplazando las variables por sus valores."""
    sujeto = sust.get(tripleta.sujeto, tripleta.sujeto)
    predicado = sust.get(tripleta.predicado, tripleta.predicado)
    objeto = sust.get(tripleta.objeto, tripleta.objeto)
    return Tripleta(sujeto, predicado, objeto)

def evaluar_restricciones(restricciones: List[Restriccion], sust: Sustitucion) -> bool:
    """Evalúa las desigualdades matemáticas (Tarea 7)."""
    for r in restricciones:
        if r.variable not in sust:
            return False # Si la variable no tiene valor, la regla falla
            
        try:
            # Convertimos el valor deducido a número para poder comparar
            valor_var = int(sust[r.variable])
            
            if r.operador == "<" and not (valor_var < r.valor): return False
            if r.operador == "<=" and not (valor_var <= r.valor): return False
            if r.operador == ">" and not (valor_var > r.valor): return False
            if r.operador == ">=" and not (valor_var >= r.valor): return False
            if r.operador == "=" and not (valor_var == r.valor): return False
        except ValueError:
            return False # Si intentamos comparar texto con números, falla
            
    return True

class MotorInferencia:
    def __init__(self, memoria: Memoria):
        self.memoria = memoria

    def _buscar_combinaciones(self, antecedentes: List[Tripleta], sust_actual: Sustitucion) -> Generator[Tuple[Sustitucion, float], None, None]:
        """
        Función recursiva que busca todas las combinaciones de hechos que cumplan
        todos los antecedentes de una regla a la vez.
        Devuelve la sustitución final y la certeza mínima encontrada (Lógica difusa).
        """
        # Caso base: si no quedan antecedentes, hemos triunfado.
        if not antecedentes:
            yield sust_actual, 1.0
            return
            
        condicion = antecedentes[0]
        resto_condiciones = antecedentes[1:]
        
        # Buscamos qué hechos encajan con esta primera condición
        for hecho in self.memoria.hechos:
            nueva_sust = unificar(condicion, hecho.tripleta, sust_actual)
            
            if nueva_sust is not None:
                # Si encaja, llamamos recursivamente para el resto de condiciones
                for sust_final, certeza_minima in self._buscar_combinaciones(resto_condiciones, nueva_sust):
                    # Lógica difusa: La certeza de una cadena de condiciones es el mínimo de sus certezas
                    certeza_combinada = min(hecho.certeza, certeza_minima)
                    yield sust_final, certeza_combinada

    def encadenamiento_hacia_adelante(self) -> int:
        """
        Algoritmo 'descubrir!'. Itera sobre las reglas infiriendo nuevos hechos
        hasta que el sistema se estabilice (no se pueda deducir nada nuevo).
        Devuelve el número de hechos nuevos descubiertos.
        """
        hechos_descubiertos = 0
        modificado = True
        
        while modificado:
            modificado = False
            
            # Revisamos cada regla de nuestra base de conocimiento
            for regla in self.memoria.reglas:
                # Buscamos todas las combinaciones de hechos que activan esta regla
                for sustitucion, certeza_antecedentes in self._buscar_combinaciones(regla.antecedentes, {}):
                    
                    # Tarea 7: Comprobamos las líneas temporales/restricciones
                    if not evaluar_restricciones(regla.restricciones, sustitucion):
                        continue
                        
                    # Fabricamos el nuevo hecho
                    nueva_tripleta = sustituir(regla.consecuente, sustitucion)
                    
                    # Tarea 8: Calculamos la certeza final (Certeza de las pruebas * Certeza de la regla)
                    certeza_final = certeza_antecedentes * regla.certeza
                    
                    nuevo_hecho = Hecho(tripleta=nueva_tripleta, certeza=certeza_final)
                    
                    # Comprobamos si el hecho es realmente nuevo (o si mejora la certeza de uno existente)
                    es_nuevo = True
                    for h in self.memoria.hechos:
                        if h.tripleta == nueva_tripleta:
                            if certeza_final > h.certeza:
                                # Si ya lo sabíamos pero ahora estamos más seguros, actualizamos
                                h.certeza = certeza_final
                                modificado = True
                            es_nuevo = False
                            break
                            
                    if es_nuevo:
                        self.memoria.agregar_hecho(nuevo_hecho)
                        logger.info(f"Deducido: {nueva_tripleta.sujeto} {nueva_tripleta.predicado} {nueva_tripleta.objeto} [Certeza: {certeza_final:.2f}]")
                        hechos_descubiertos += 1
                        modificado = True # Como hay un hecho nuevo, habrá que dar otra vuelta
                        
        return hechos_descubiertos