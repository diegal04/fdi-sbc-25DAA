from dataclasses import dataclass, field
from typing import List
from pyparsing import (Word, srange, Group, Suppress, Optional, delimitedList, 
                       Literal, Keyword, Combine, pythonStyleComment)

# ==========================================
# 1. ESTRUCTURAS DE DATOS (Dataclasses)
# ==========================================

@dataclass
class Tripleta:
    sujeto: str
    predicado: str
    objeto: str

@dataclass
class Restriccion:
    variable: str
    operador: str
    valor: int

@dataclass
class Hecho:
    tripleta: Tripleta
    certeza: float = 1.0  
    negado: bool = False  

@dataclass
class Regla:
    consecuente: Tripleta
    antecedentes: List[Tripleta]
    certeza: float = 1.0
    # Nueva lista para guardar las desigualdades (Tarea 7)
    restricciones: List[Restriccion] = field(default_factory=list)

@dataclass
class Consulta:
    tripleta: Tripleta
    razona_si: bool = False # Si es True, usará encadenamiento hacia atrás

# ==========================================
# 2. GRAMÁTICA PYPARSING (Traducción EBNF)
# ==========================================

# Ignorar comentarios (todo lo que empiece por # hasta el final de la línea)
comentario = pythonStyleComment

# Literales y Variables
literal = Word(srange("[a-z0-9]"), srange("[a-zA-Z0-9_]"))
variable = Word(srange("[A-Z]"), srange("[a-zA-Z0-9_]"))
termino = literal | variable

# Tripleta base
tripleta = Group(termino + termino + termino)
tripleta.set_parse_action(lambda t: Tripleta(t[0][0], t[0][1], t[0][2]))

# --- Extensiones (Lógica Difusa y Restricciones) ---
numero_difuso = Combine(Literal("0.") + Word(srange("[0-9]")) | Literal("1"))
extension_difusa = numero_difuso.copy().set_parse_action(lambda t: float(t[0]))

operador = Literal("<=") | Literal(">=") | Literal("<") | Literal(">") | Literal("=")
entero = Word(srange("[0-9]")).set_parse_action(lambda t: int(t[0]))
restriccion = variable + operador + entero
restriccion.set_parse_action(lambda t: Restriccion(t[0], t[1], t[2]))

# Agrupamos las extensiones entre corchetes separados por punto y coma
extension_item = extension_difusa | restriccion
extension_grupo = Group(Suppress("[") + delimitedList(extension_item, delim=";") + Suppress("]"))

# --- Parseo de Hechos (Afirmaciones y Negaciones) ---
afirmacion = tripleta + Suppress(".") + Optional(extension_grupo, default=[])
def procesar_afirmacion(t):
    certeza = 1.0
    for ext in t[1]: # Busca si en los corchetes hay un número de lógica difusa
        if isinstance(ext, float): certeza = ext
    return Hecho(tripleta=t[0], certeza=certeza)
afirmacion.set_parse_action(procesar_afirmacion)

negacion = Keyword("no") + tripleta + Suppress(".")
negacion.set_parse_action(lambda t: Hecho(tripleta=t[1], negado=True))

# Cualquiera de las dos formas es un hecho válido
hecho_parser = afirmacion | negacion

# --- Parseo de Consultas ---
consulta_simple = tripleta + Suppress("?")
consulta_simple.set_parse_action(lambda t: Consulta(tripleta=t[0], razona_si=False))

consulta_razona = Suppress("razona si") + tripleta + Suppress("?")
consulta_razona.set_parse_action(lambda t: Consulta(tripleta=t[0], razona_si=True))

consulta_parser = consulta_razona | consulta_simple

# --- Parseo de Reglas ---
antecedentes_grupo = Group(delimitedList(tripleta))
reglas_parser = tripleta + Suppress("<-") + antecedentes_grupo + Suppress(".") + Optional(extension_grupo, default=[])

def procesar_regla(t):
    consecuente = t[0]
    antecedentes = list(t[1])
    certeza = 1.0
    restricciones = []
    
    # Clasificamos qué hay dentro de los corchetes finales
    for ext in t[2]:
        if isinstance(ext, float):
            certeza = ext
        elif isinstance(ext, Restriccion):
            restricciones.append(ext)
            
    return Regla(consecuente, antecedentes, certeza, restricciones)

reglas_parser.set_parse_action(procesar_regla)

# Para ignorar los comentarios en cualquier parte del archivo
hecho_parser.ignore(comentario)
reglas_parser.ignore(comentario)
consulta_parser.ignore(comentario)