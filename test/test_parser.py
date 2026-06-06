"""
Tests funcionales del módulo sbc.parser.

Verifica que la gramática EBNF sea parseada correctamente por pyparsing para
todos los tipos de declaración: hechos, negaciones, reglas con extensiones
(lógica difusa + restricciones aritméticas) y consultas.
"""

import unittest

from pyparsing import ParseException

from sbc.parser import (
    Consulta,
    Hecho,
    Regla,
    Restriccion,
    Tripleta,
    consulta_parser,
    hecho_parser,
    reglas_parser,
)


class TestEstructurasDeDatos(unittest.TestCase):
    """Tests para las dataclasses Tripleta, Hecho, Regla y Restriccion."""

    def test_tripleta_igualdad_estructural(self):
        """Dos Tripletas con los mismos valores deben ser iguales (dataclass)."""
        t1 = Tripleta("coronel_mostaza", "esta_en", "biblioteca")
        t2 = Tripleta("coronel_mostaza", "esta_en", "biblioteca")
        self.assertEqual(t1, t2)

    def test_tripleta_desigualdad_por_objeto(self):
        t1 = Tripleta("a", "b", "c")
        t2 = Tripleta("a", "b", "d")
        self.assertNotEqual(t1, t2)

    def test_hecho_certeza_por_defecto_es_uno(self):
        h = Hecho(Tripleta("a", "b", "c"))
        self.assertAlmostEqual(h.certeza, 1.0)
        self.assertFalse(h.negado)

    def test_restriccion_campos(self):
        r = Restriccion("Hora", ">", 2200)
        self.assertEqual(r.variable, "Hora")
        self.assertEqual(r.operador, ">")
        self.assertEqual(r.valor, 2200)


class TestParserHechos(unittest.TestCase):
    """Tests de parseo de afirmaciones y negaciones (hechos)."""

    def _parsear(self, texto: str) -> Hecho:
        return hecho_parser.parse_string(texto, parse_all=True)[0]

    def test_afirmacion_simple(self):
        h = self._parsear("coronel_mostaza esta_en biblioteca.")
        self.assertIsInstance(h, Hecho)
        self.assertEqual(
            h.tripleta, Tripleta("coronel_mostaza", "esta_en", "biblioteca")
        )
        self.assertAlmostEqual(h.certeza, 1.0)
        self.assertFalse(h.negado)

    def test_afirmacion_con_certeza_difusa(self):
        """Un hecho con extensión [ 0.6 ] debe tener certeza 0.6."""
        h = self._parsear("candelabro tiene_sangre si. [ 0.6 ]")
        self.assertAlmostEqual(h.certeza, 0.6)

    def test_afirmacion_con_certeza_maxima(self):
        """La certeza 1.0 debe parsearse como 1.0."""
        h = self._parsear("hecho es valido. [ 1.0 ]")
        self.assertAlmostEqual(h.certeza, 1.0)

    def test_afirmacion_con_certeza_minima(self):
        """Certeza 0.1 debe conservarse como float."""
        h = self._parsear("pista es debil. [ 0.1 ]")
        self.assertAlmostEqual(h.certeza, 0.1)

    def test_afirmacion_con_variable_como_sujeto(self):
        """Las variables (mayúsculas) son términos válidos en una tripleta."""
        h = self._parsear("X tiene_motivo si.")
        self.assertEqual(h.tripleta.sujeto, "X")

    def test_negacion_simple(self):
        """La palabra clave 'no' produce un Hecho con negado=True."""
        h = self._parsear("no coronel_mostaza esta_en biblioteca.")
        self.assertIsInstance(h, Hecho)
        self.assertTrue(h.negado)
        self.assertEqual(h.tripleta.sujeto, "coronel_mostaza")

    def test_negacion_preserva_tripleta(self):
        h = self._parsear("no victima sufre contusion.")
        self.assertEqual(h.tripleta, Tripleta("victima", "sufre", "contusion"))

    def test_comentario_ignorado_en_misma_linea(self):
        """Los comentarios # deben ignorarse aunque aparezcan en la misma línea."""
        h = self._parsear("victima sufre contusion. # esto es un comentario")
        self.assertEqual(h.tripleta.sujeto, "victima")

    def test_error_sin_punto_final(self):
        """Una afirmación sin punto debe lanzar ParseException."""
        with self.assertRaises(ParseException):
            hecho_parser.parse_string(
                "coronel_mostaza esta_en biblioteca", parse_all=True
            )

    def test_error_solo_dos_terminos(self):
        """Una tripleta incompleta (dos términos) debe fallar."""
        with self.assertRaises(ParseException):
            hecho_parser.parse_string("coronel_mostaza esta_en.", parse_all=True)

    def test_error_certeza_fuera_de_rango(self):
        """Una certeza mayor que 1 no es un float difuso válido (ej: 1.5)."""
        with self.assertRaises(ParseException):
            hecho_parser.parse_string("hecho es valido. [ 1.5 ]", parse_all=True)


class TestParserReglas(unittest.TestCase):
    """Tests de parseo de reglas de deducción con extensiones."""

    def _parsear(self, texto: str) -> Regla:
        return reglas_parser.parse_string(texto, parse_all=True)[0]

    def test_regla_simple_un_antecedente(self):
        r = self._parsear("X es sospechoso <- X es_tipo persona.")
        self.assertIsInstance(r, Regla)
        self.assertEqual(r.consecuente, Tripleta("X", "es", "sospechoso"))
        self.assertEqual(len(r.antecedentes), 1)
        self.assertAlmostEqual(r.certeza, 1.0)
        self.assertEqual(r.restricciones, [])

    def test_regla_multiples_antecedentes(self):
        """El separador de antecedentes es la coma."""
        r = self._parsear("P es asesino <- P es sospechoso, P tiene_coartada no.")
        self.assertEqual(len(r.antecedentes), 2)
        self.assertEqual(r.antecedentes[0], Tripleta("P", "es", "sospechoso"))
        self.assertEqual(r.antecedentes[1], Tripleta("P", "tiene_coartada", "no"))

    def test_regla_con_certeza_difusa(self):
        r = self._parsear("X es arma_homicida <- victima sufre contusion. [ 0.9 ]")
        self.assertAlmostEqual(r.certeza, 0.9)

    def test_regla_con_restriccion_mayor_que(self):
        """Una restricción [Hora > 2200] debe producir una Restriccion correcta."""
        r = self._parsear("P tiene_coartada no <- P llega_a_casa Hora. [ Hora > 2200 ]")
        self.assertEqual(len(r.restricciones), 1)
        res = r.restricciones[0]
        self.assertIsInstance(res, Restriccion)
        self.assertEqual(res.variable, "Hora")
        self.assertEqual(res.operador, ">")
        self.assertEqual(res.valor, 2200)

    def test_regla_con_restriccion_menor_igual(self):
        r = self._parsear(
            "P tiene_coartada si <- P llega_a_casa Hora. [ Hora <= 2200 ]"
        )
        self.assertEqual(r.restricciones[0].operador, "<=")

    def test_regla_con_restriccion_igual(self):
        r = self._parsear("X es exacto <- X edad E. [ E = 25 ]")
        res = r.restricciones[0]
        self.assertEqual(res.operador, "=")
        self.assertEqual(res.valor, 25)

    def test_regla_con_extension_mixta_difusa_y_restriccion(self):
        """Una regla puede tener certeza difusa Y restricciones separadas por ';'."""
        r = self._parsear(
            "P es sospechoso <- P llega_a_casa Hora. [ 0.8; Hora > 2200 ]"
        )
        self.assertAlmostEqual(r.certeza, 0.8)
        self.assertEqual(len(r.restricciones), 1)
        self.assertEqual(r.restricciones[0].variable, "Hora")

    def test_regla_con_restriccion_variable_a_variable(self):
        """Una restricción puede comparar dos variables: VX >= VY."""
        r = self._parsear("X e_mayor Y <- X e_vale VX , Y e_vale VY . [ VX >= VY ]")
        self.assertEqual(len(r.restricciones), 1)
        res = r.restricciones[0]
        self.assertEqual(res.variable, "VX")
        self.assertEqual(res.operador, ">=")
        self.assertEqual(res.valor, "VY")  # Debe ser una string (variable)
        self.assertIsInstance(res.valor, str)

    def test_regla_cuatro_antecedentes(self):
        """Regla con 4 antecedentes (como la regla de sospechoso en misterio.txt)."""
        r = self._parsear(
            "P es sospechoso <- P es_tipo persona, P esta_en H, "
            "A esta_en H, A es arma_homicida. [ 0.9 ]"
        )
        self.assertEqual(len(r.antecedentes), 4)
        self.assertAlmostEqual(r.certeza, 0.9)

    def test_error_regla_sin_punto_final(self):
        with self.assertRaises(ParseException):
            reglas_parser.parse_string(
                "X es sospechoso <- X es_tipo persona", parse_all=True
            )

    def test_error_regla_sin_antecedentes(self):
        """Una regla necesita al menos un antecedente tras '<-'."""
        with self.assertRaises(ParseException):
            reglas_parser.parse_string("X es sospechoso <-.", parse_all=True)


class TestParserConsultas(unittest.TestCase):
    """Tests de parseo de consultas simples (?) y de razonamiento (razona si ?)."""

    def test_consulta_simple_verdadero_falso(self):
        """Una consulta con '?' produce razona_si=False (búsqueda directa en memoria)."""
        c = consulta_parser.parse_string(
            "coronel_mostaza esta_en biblioteca?", parse_all=True
        )[0]
        self.assertIsInstance(c, Consulta)
        self.assertFalse(c.razona_si)
        self.assertEqual(
            c.tripleta, Tripleta("coronel_mostaza", "esta_en", "biblioteca")
        )

    def test_consulta_con_variable(self):
        """Una consulta puede contener variables: X esta_en ?"""
        c = consulta_parser.parse_string("X esta_en biblioteca?", parse_all=True)[0]
        self.assertEqual(c.tripleta.sujeto, "X")

    def test_consulta_razona_si(self):
        """'razona si' activa el encadenamiento hacia atrás."""
        c = consulta_parser.parse_string("razona si X es asesino?", parse_all=True)[0]
        self.assertIsInstance(c, Consulta)
        self.assertTrue(c.razona_si)
        self.assertEqual(c.tripleta.sujeto, "X")
        self.assertEqual(c.tripleta.predicado, "es")

    def test_consulta_razona_si_sin_variable(self):
        c = consulta_parser.parse_string(
            "razona si coronel_mostaza es asesino?", parse_all=True
        )[0]
        self.assertTrue(c.razona_si)
        self.assertEqual(c.tripleta.sujeto, "coronel_mostaza")

    def test_error_consulta_sin_interrogacion(self):
        with self.assertRaises(ParseException):
            consulta_parser.parse_string(
                "coronel_mostaza esta_en biblioteca", parse_all=True
            )


class TestParserPrecedencia(unittest.TestCase):
    """Tests del parseo de la extensión de precedencia (digito digito digito)."""

    def _parsear(self, texto: str) -> Regla:
        return reglas_parser.parse_string(texto, parse_all=True)[0]

    def test_regla_con_precedencia_entera(self):
        """Una regla con [100] debe tener precedencia 100."""
        r = self._parsear("X es sospechoso <- X es_tipo persona. [ 100 ]")
        self.assertEqual(r.precedencia, 100)

    def test_regla_con_precedencia_con_cero_inicial(self):
        """Precedencia '050' debe parsearse como entero 50."""
        r = self._parsear("X es sospechoso <- X es_tipo persona. [ 050 ]")
        self.assertEqual(r.precedencia, 50)

    def test_regla_con_precedencia_maxima(self):
        """Precedencia '999' es el valor máximo permitido por la gramática."""
        r = self._parsear("X es sospechoso <- X es_tipo persona. [ 999 ]")
        self.assertEqual(r.precedencia, 999)

    def test_regla_con_precedencia_minima(self):
        """Precedencia '000' debe parsearse como entero 0."""
        r = self._parsear("X es sospechoso <- X es_tipo persona. [ 000 ]")
        self.assertEqual(r.precedencia, 0)

    def test_regla_sin_precedencia_tiene_defecto_cero(self):
        """Una regla sin extensión de precedencia debe tener precedencia = 0."""
        r = self._parsear("X es sospechoso <- X es_tipo persona.")
        self.assertEqual(r.precedencia, 0)

    def test_precedencia_no_confunde_certeza_difusa(self):
        """'[ 1.0 ]' (certeza) no debe interpretarse como precedencia."""
        r = self._parsear("X es sospechoso <- X es_tipo persona. [ 1.0 ]")
        self.assertAlmostEqual(r.certeza, 1.0)
        self.assertEqual(r.precedencia, 0)  # No hay precedencia

    def test_certeza_difusa_no_confunde_precedencia(self):
        """'[ 0.9 ]' (certeza difusa) no debe interpretarse como precedencia."""
        r = self._parsear("X es sospechoso <- X es_tipo persona. [ 0.9 ]")
        self.assertAlmostEqual(r.certeza, 0.9)
        self.assertEqual(r.precedencia, 0)

    def test_extension_mixta_precedencia_y_certeza(self):
        """Una regla puede tener certeza difusa Y precedencia separadas por ';'."""
        r = self._parsear("P es asesino <- P es sospechoso. [ 0.8; 090 ]")
        self.assertAlmostEqual(r.certeza, 0.8)
        self.assertEqual(r.precedencia, 90)

    def test_extension_mixta_precedencia_y_restriccion(self):
        """Una regla puede tener precedencia Y restricción aritmética en el mismo bloque."""
        r = self._parsear(
            "P tiene_coartada no <- P llega_casa Hora. [ 100; Hora > 2200 ]"
        )
        self.assertEqual(r.precedencia, 100)
        self.assertEqual(len(r.restricciones), 1)
        self.assertEqual(r.restricciones[0].operador, ">")

    def test_extension_triple_precedencia_certeza_restriccion(self):
        """Una regla puede combinar las tres extensiones a la vez."""
        r = self._parsear(
            "P es culpable <- P llega_casa Hora. [ 0.9; 075; Hora > 2200 ]"
        )
        self.assertAlmostEqual(r.certeza, 0.9)
        self.assertEqual(r.precedencia, 75)
        self.assertEqual(len(r.restricciones), 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
