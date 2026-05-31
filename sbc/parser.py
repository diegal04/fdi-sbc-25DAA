from dataclasses import dataclass
from typing import List
from pyparsing import Word, srange, Group, Suppress, Optional, delimitedList, Keyword, Combine

# ==========================================
# 1. ESTRUCTURAS DE DATOS (Dataclasses)
# ==========================================
# Las dataclasses son recomendadas en las normas. 
# Nos sirven para guardar la información ya procesada de forma limpia.

@dataclass
class Tripleta:
    sujeto: str
    predicado: str
    objeto: str

@dataclass
class Hecho:
    tripleta: Tripleta
    certeza: float = 1.0  # Aquí guardaremos el valor de la Tarea 8 (Lógica Difusa)
    negado: bool = False  # Para hechos que empiezan por "no"

@dataclass
class Regla:
    consecuente: Tripleta
    antecedentes: List[Tripleta]
    certeza: float = 1.0  # Para reglas difusas

# ==========================================
# 2. GRAMÁTICA PYPARSING (Traducción EBNF)
# ==========================================

# Definimos qué es un literal (minúsculas) y una variable (Empieza por mayúscula)
literal = Word(srange("[a-z]"), srange("[a-zA-Z0-9_]"))
variable = Word(srange("[A-Z]"), srange("[a-zA-Z0-9_]"))
termino = literal | variable

# Una tripleta son tres términos seguidos. 
# set_parse_action convierte el resultado del texto directamente en nuestra Dataclass 'Tripleta'
tripleta = Group(termino + termino + termino)
tripleta.set_parse_action(lambda t: Tripleta(t[0][0], t[0][1], t[0][2]))

# --- Extensión: Lógica Difusa ---
# Busca números como "0.85" o "1".
numero_difuso = Combine(Keyword("0.") + Word(srange("[0-9]")) | Keyword("1"))
extension_difusa = Suppress("[") + numero_difuso + Suppress("]")
extension_difusa.set_parse_action(lambda t: float(t[0]))

# --- Parseo de Hechos (Afirmaciones) ---
# Sintaxis: tripleta . [ extension ]
afirmacion = tripleta + Suppress(".") + Optional(extension_difusa, default=1.0)
afirmacion.set_parse_action(lambda t: Hecho(tripleta=t[0], certeza=t[1]))

# --- Parseo de Reglas ---
# Sintaxis: tripleta <- tripleta , tripleta . [ extension ]
reglas_texto = tripleta + Suppress("<-") + delimitedList(tripleta) + Suppress(".") + Optional(extension_difusa, default=1.0)

def procesar_regla(t):
    # El primer elemento es el consecuente, el último la certeza, lo del medio son los antecedentes
    consecuente = t[0]
    certeza = t[-1]
    antecedentes = list(t[1:-1])
    return Regla(consecuente=consecuente, antecedentes=antecedentes, certeza=certeza)

reglas_texto.set_parse_action(procesar_regla)