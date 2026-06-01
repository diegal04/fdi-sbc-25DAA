from typing import List, Dict, Generator, Tuple
from loguru import logger
from sbc.parser import Tripleta, Hecho, Regla, Restriccion
from sbc.memory import Memoria

Sustitucion = Dict[str, str]

def es_variable(termino: str) -> bool:
    return termino[0].isupper()

def unificar(patron: Tripleta, hecho: Tripleta, sust_previa: Sustitucion) -> Sustitucion | None:
    sust = sust_previa.copy()
    for p, h in zip([patron.sujeto, patron.predicado, patron.objeto], 
                    [hecho.sujeto, hecho.predicado, hecho.objeto]):
        if es_variable(p):
            if p in sust:
                if sust[p] != h: return None
            else:
                sust[p] = h
        elif p != h:
            return None
    return sust

def _resolver(termino: str, sust: Sustitucion) -> str:
    """Busca en profundidad para traducir variables encadenadas (ej: P -> X -> coronel_mostaza)."""
    visitados = set()
    while termino in sust and termino not in visitados:
        visitados.add(termino)
        termino = sust[termino]
    return termino

def sustituir(tripleta: Tripleta, sust: Sustitucion) -> Tripleta:
    """Aplica las sustituciones usando el resolutor profundo para evitar colisiones."""
    sujeto = _resolver(tripleta.sujeto, sust)
    predicado = _resolver(tripleta.predicado, sust)
    objeto = _resolver(tripleta.objeto, sust)
    return Tripleta(sujeto, predicado, objeto)

def evaluar_restricciones(restricciones: List[Restriccion], sust: Sustitucion) -> bool:
    for r in restricciones:
        valor_resuelto = _resolver(r.variable, sust)
        try:
            valor_var = int(valor_resuelto)
            if r.operador == "<" and not (valor_var < r.valor): return False
            if r.operador == "<=" and not (valor_var <= r.valor): return False
            if r.operador == ">" and not (valor_var > r.valor): return False
            if r.operador == ">=" and not (valor_var >= r.valor): return False
            if r.operador == "=" and not (valor_var == r.valor): return False
        except ValueError:
            return False
    return True

class MotorInferencia:
    def __init__(self, memoria: Memoria):
        self.memoria = memoria

    # ==========================================
    # ENCADENAMIENTO HACIA ADELANTE
    # ==========================================
    def _buscar_combinaciones(self, antecedentes: List[Tripleta], sust_actual: Sustitucion) -> Generator[Tuple[Sustitucion, float], None, None]:
        if not antecedentes:
            yield sust_actual, 1.0
            return
            
        condicion = antecedentes[0]
        resto_condiciones = antecedentes[1:]
        
        for hecho in self.memoria.hechos:
            nueva_sust = unificar(condicion, hecho.tripleta, sust_actual)
            if nueva_sust is not None:
                for sust_final, certeza_minima in self._buscar_combinaciones(resto_condiciones, nueva_sust):
                    yield sust_final, min(hecho.certeza, certeza_minima)

    def encadenamiento_hacia_adelante(self) -> int:
        hechos_descubiertos = 0
        modificado = True
        
        while modificado:
            modificado = False
            for regla in self.memoria.reglas:
                for sustitucion, certeza_antecedentes in self._buscar_combinaciones(regla.antecedentes, {}):
                    if not evaluar_restricciones(regla.restricciones, sustitucion):
                        continue
                        
                    nueva_tripleta = sustituir(regla.consecuente, sustitucion)
                    certeza_final = certeza_antecedentes * regla.certeza
                    nuevo_hecho = Hecho(tripleta=nueva_tripleta, certeza=certeza_final)
                    
                    es_nuevo = True
                    for h in self.memoria.hechos:
                        if h.tripleta == nueva_tripleta:
                            if certeza_final > h.certeza:
                                h.certeza = certeza_final
                                modificado = True
                            es_nuevo = False
                            break
                            
                    if es_nuevo:
                        self.memoria.agregar_hecho(nuevo_hecho)
                        logger.info(f"Deducido: {nueva_tripleta.sujeto} {nueva_tripleta.predicado} {nueva_tripleta.objeto} [Certeza: {certeza_final:.2f}]")
                        hechos_descubiertos += 1
                        modificado = True
                        
        return hechos_descubiertos

    # ==========================================
    # BÚSQUEDA DIRECTA (Consultas con ?)
    # ==========================================
    def consultar_hechos(self, consulta: Tripleta) -> List[Tuple[Sustitucion, float]]:
        resultados = []
        for hecho in self.memoria.hechos:
            sust = unificar(consulta, hecho.tripleta, {})
            if sust is not None:
                resultados.append((sust, hecho.certeza))
        return resultados

    # ==========================================
    # ENCADENAMIENTO HACIA ATRÁS (razona si)
    # ==========================================
    def encadenamiento_hacia_atras(self, objetivo: Tripleta, nivel: int = 0) -> Generator[Tuple[Sustitucion, float], None, None]:
        if nivel > 15: # Evitar bucles infinitos
            return

        # 1. CASO BASE (Comprobar en los hechos)
        for hecho in self.memoria.hechos:
            sust = unificar(objetivo, hecho.tripleta, {})
            if sust is not None:
                yield sust, hecho.certeza

        # 2. CASO RECURSIVO (Buscar en reglas)
        for regla in self.memoria.reglas:
            # MAGIA ANTI-COLISIONES: Invertimos los argumentos.
            # regla.consecuente es el patrón, objetivo es el hecho a igualar.
            sust_regla = unificar(regla.consecuente, objetivo, {})
            
            if sust_regla is not None:
                for sust_final, certeza_final in self._verificar_antecedentes_atras(
                    antecedentes=regla.antecedentes,
                    sust_actual=sust_regla,
                    restricciones=regla.restricciones,
                    certeza_acumulada=regla.certeza,
                    nivel=nivel + 1
                ):
                    # LIMPIEZA DE COLISIONES: Solo devolvemos al usuario las variables 
                    # que originalmente estaban en su consulta.
                    vars_objetivo = [t for t in [objetivo.sujeto, objetivo.predicado, objetivo.objeto] if es_variable(t)]
                    sust_limpia = {}
                    
                    for v in vars_objetivo:
                        valor_final = _resolver(v, sust_final)
                        if valor_final != v: # Si realmente descubrió algo
                            sust_limpia[v] = valor_final
                            
                    yield sust_limpia, certeza_final

    def _verificar_antecedentes_atras(self, antecedentes: List[Tripleta], sust_actual: Sustitucion, restricciones: List[Restriccion], certeza_acumulada: float, nivel: int) -> Generator[Tuple[Sustitucion, float], None, None]:
        if not antecedentes:
            if evaluar_restricciones(restricciones, sust_actual):
                yield sust_actual, certeza_acumulada
            return

        condicion_actual = sustituir(antecedentes[0], sust_actual)
        resto_antecedentes = antecedentes[1:]

        for sust_parcial, certeza_parcial in self.encadenamiento_hacia_atras(condicion_actual, nivel):
            nueva_sust = sust_actual.copy()
            nueva_sust.update(sust_parcial)
            certeza_minima = min(certeza_acumulada, certeza_parcial)
            
            yield from self._verificar_antecedentes_atras(
                resto_antecedentes, 
                nueva_sust, 
                restricciones, 
                certeza_minima, 
                nivel
            )