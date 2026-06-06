"""
Tests funcionales del módulo sbc.engine.

Cubre las cinco tareas del caso de uso (Agencia de Detectives) más los
algoritmos auxiliares (unificación, sustitución, restricciones) y los
escenarios de robustez (bucles circulares, cadenas profundas, fronteras
matemáticas exactas, propagación de lógica difusa).

Ejecutar con: uv run python -m unittest discover test
"""

import os
import tempfile
import unittest
from pathlib import Path

from sbc.engine import (
    MotorInferencia,
    _resolver,
    es_variable,
    evaluar_restricciones,
    sustituir,
    unificar,
)
from sbc.memory import Memoria
from sbc.parser import Restriccion, Tripleta

KB_CLUEDO = Path(__file__).parent.parent / "kb" / "cluedo.txt"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _cargar_kb(contenido: str) -> tuple[Memoria, MotorInferencia]:
    """Crea una Memoria a partir de texto de KB en línea y devuelve su motor."""
    fd, ruta = tempfile.mkstemp(suffix=".txt")
    try:
        os.write(fd, contenido.encode("utf-8"))
        os.close(fd)
        memoria = Memoria()
        memoria.cargar_archivo(ruta)
    finally:
        os.unlink(ruta)
    return memoria, MotorInferencia(memoria)


def _buscar(memoria: Memoria, s: str, p: str, o: str):
    """Devuelve el Hecho (s p o) de la memoria o None si no existe."""
    objetivo = Tripleta(s, p, o)
    return next((h for h in memoria.hechos if h.tripleta == objetivo), None)


# ---------------------------------------------------------------------------
# 1. Tests de algoritmos auxiliares: unificación y resolución de variables
# ---------------------------------------------------------------------------


class TestEsVariable(unittest.TestCase):
    """Tests para la función es_variable()."""

    def test_literal_minuscula_no_es_variable(self):
        self.assertFalse(es_variable("coronel_mostaza"))

    def test_digito_inicial_no_es_variable(self):
        self.assertFalse(es_variable("007"))

    def test_mayuscula_inicial_es_variable(self):
        self.assertTrue(es_variable("X"))

    def test_variable_con_sufijo(self):
        self.assertTrue(es_variable("Hora"))

    def test_variable_larga(self):
        self.assertTrue(es_variable("PersonaSospechosa"))


class TestUnificacion(unittest.TestCase):
    """Tests para la función unificar()."""

    def test_literales_iguales_devuelve_sustitucion_vacia(self):
        sust = unificar(Tripleta("a", "b", "c"), Tripleta("a", "b", "c"), {})
        self.assertIsNotNone(sust)
        self.assertEqual(sust, {})

    def test_literales_distintos_devuelve_none(self):
        sust = unificar(Tripleta("a", "b", "c"), Tripleta("a", "b", "d"), {})
        self.assertIsNone(sust)

    def test_variable_libre_se_enlaza(self):
        sust = unificar(
            Tripleta("X", "es", "asesino"),
            Tripleta("coronel_mostaza", "es", "asesino"),
            {},
        )
        self.assertIsNotNone(sust)
        self.assertEqual(sust["X"], "coronel_mostaza")

    def test_variable_enlazada_coherente(self):
        """X ya ligada a 'a' debe unificarse con 'a' sin conflicto."""
        sust = unificar(Tripleta("X", "b", "c"), Tripleta("a", "b", "c"), {"X": "a"})
        self.assertIsNotNone(sust)

    def test_variable_enlazada_incoherente_devuelve_none(self):
        """X ligada a 'a' no puede unificarse con 'b'."""
        sust = unificar(Tripleta("X", "b", "c"), Tripleta("b", "b", "c"), {"X": "a"})
        self.assertIsNone(sust)

    def test_misma_variable_en_posiciones_distintas_coherente(self):
        """X=X: mismo literal en ambas posiciones."""
        sust = unificar(Tripleta("X", "es", "X"), Tripleta("a", "es", "a"), {})
        self.assertIsNotNone(sust)

    def test_misma_variable_en_posiciones_distintas_incoherente(self):
        sust = unificar(Tripleta("X", "es", "X"), Tripleta("a", "es", "b"), {})
        self.assertIsNone(sust)

    def test_multiples_variables_en_tripleta(self):
        sust = unificar(
            Tripleta("X", "esta_en", "Y"),
            Tripleta("coronel_mostaza", "esta_en", "biblioteca"),
            {},
        )
        self.assertEqual(sust["X"], "coronel_mostaza")
        self.assertEqual(sust["Y"], "biblioteca")


class TestResolutor(unittest.TestCase):
    """Tests para _resolver(): resolutor profundo de cadenas de sustituciones."""

    def test_termino_no_en_sust_devuelve_si_mismo(self):
        self.assertEqual(_resolver("X", {}), "X")

    def test_resolucion_directa(self):
        self.assertEqual(_resolver("X", {"X": "coronel_mostaza"}), "coronel_mostaza")

    def test_resolucion_en_cadena(self):
        """P -> X -> coronel_mostaza debe resolverse en un solo paso."""
        sust = {"P": "X", "X": "coronel_mostaza"}
        self.assertEqual(_resolver("P", sust), "coronel_mostaza")

    def test_resolucion_evita_ciclo_infinito(self):
        """Con un ciclo A->B->A, el resolutor debe terminar sin colgar."""
        sust = {"A": "B", "B": "A"}
        resultado = _resolver("A", sust)
        self.assertIn(resultado, ("A", "B"))


class TestSustituir(unittest.TestCase):
    """Tests para sustituir(): aplica sustituciones sobre una Tripleta."""

    def test_sustitucion_en_sujeto(self):
        t = sustituir(Tripleta("X", "es", "asesino"), {"X": "coronel_mostaza"})
        self.assertEqual(t.sujeto, "coronel_mostaza")
        self.assertEqual(t.objeto, "asesino")

    def test_sustitucion_en_todos_los_campos(self):
        t = sustituir(Tripleta("X", "P", "Y"), {"X": "a", "P": "b", "Y": "c"})
        self.assertEqual(t, Tripleta("a", "b", "c"))

    def test_sin_sustitucion_tripleta_inalterada(self):
        original = Tripleta("literal", "otro", "mas")
        t = sustituir(original, {})
        self.assertEqual(t, original)


# ---------------------------------------------------------------------------
# 2. Tests de restricciones aritméticas (Tarea 4)
# ---------------------------------------------------------------------------


class TestEvaluarRestricciones(unittest.TestCase):
    """Tests para evaluar_restricciones() con todos los operadores."""

    def _sust(self, variable: str, valor: int) -> dict:
        return {variable: str(valor)}

    # --- Operador < ---
    def test_menor_estricto_verdadero(self):
        self.assertTrue(
            evaluar_restricciones([Restriccion("E", "<", 25)], self._sust("E", 20))
        )

    def test_menor_estricto_en_limite_falso(self):
        """E < 25 es FALSO cuando E = 25 (frontera exacta)."""
        self.assertFalse(
            evaluar_restricciones([Restriccion("E", "<", 25)], self._sust("E", 25))
        )

    def test_menor_estricto_mayor_falso(self):
        self.assertFalse(
            evaluar_restricciones([Restriccion("E", "<", 25)], self._sust("E", 30))
        )

    # --- Operador <= ---
    def test_menor_igual_en_limite_verdadero(self):
        """E <= 25 es VERDADERO cuando E = 25 (frontera inclusiva)."""
        self.assertTrue(
            evaluar_restricciones([Restriccion("E", "<=", 25)], self._sust("E", 25))
        )

    def test_menor_igual_mayor_falso(self):
        self.assertFalse(
            evaluar_restricciones([Restriccion("E", "<=", 25)], self._sust("E", 26))
        )

    # --- Operador > ---
    def test_mayor_estricto_verdadero(self):
        self.assertTrue(
            evaluar_restricciones(
                [Restriccion("Hora", ">", 2200)], self._sust("Hora", 2330)
            )
        )

    def test_mayor_estricto_en_limite_falso(self):
        """Hora > 2200 es FALSO cuando Hora = 2200."""
        self.assertFalse(
            evaluar_restricciones(
                [Restriccion("Hora", ">", 2200)], self._sust("Hora", 2200)
            )
        )

    # --- Operador >= ---
    def test_mayor_igual_en_limite_verdadero(self):
        self.assertTrue(
            evaluar_restricciones([Restriccion("E", ">=", 25)], self._sust("E", 25))
        )

    # --- Operador = ---
    def test_igual_verdadero(self):
        self.assertTrue(
            evaluar_restricciones([Restriccion("E", "=", 25)], self._sust("E", 25))
        )

    def test_igual_falso(self):
        self.assertFalse(
            evaluar_restricciones([Restriccion("E", "=", 25)], self._sust("E", 26))
        )

    # --- Casos especiales ---
    def test_variable_no_resuelta_falla(self):
        """Si la variable no está en la sustitución, la restricción no se puede evaluar."""
        self.assertFalse(evaluar_restricciones([Restriccion("Hora", ">", 2200)], {}))

    def test_multiples_restricciones_todas_deben_cumplirse(self):
        """Varias restricciones actúan como conjunción (AND)."""
        restricciones = [Restriccion("E", ">", 18), Restriccion("E", "<", 65)]
        self.assertTrue(evaluar_restricciones(restricciones, self._sust("E", 30)))
        self.assertFalse(evaluar_restricciones(restricciones, self._sust("E", 70)))


# ---------------------------------------------------------------------------
# 3. Tests de encadenamiento hacia adelante sobre kb/cluedo.txt (Tareas 1-5)
# ---------------------------------------------------------------------------


@unittest.skipUnless(KB_CLUEDO.exists(), "kb/cluedo.txt no disponible")
class TestEncadenamientoAdelante(unittest.TestCase):
    """
    Tests funcionales del encadenamiento hacia adelante usando kb/cluedo.txt.

    Cada test verifica uno de los cinco requisitos del enunciado:
      - Tarea 1: Identificación del arma homicida (candelabro).
      - Tarea 2: Verificación de oportunidad (ubicación en la escena).
      - Tarea 3: Inferencia final del culpable.
      - Tarea 4: Descarte por restricciones aritméticas de tiempo.
      - Tarea 5: Propagación de incertidumbre (lógica difusa).
    """

    @classmethod
    def setUpClass(cls):
        cls.memoria = Memoria()
        cls.memoria.cargar_archivo(KB_CLUEDO)
        cls.motor = MotorInferencia(cls.memoria)
        cls.descubiertos = cls.motor.encadenamiento_hacia_adelante()

    def test_motor_deduce_nuevos_hechos(self):
        """El motor debe descubrir al menos un hecho nuevo a partir de la KB."""
        self.assertGreater(self.descubiertos, 0)

    # --- Tarea 1 ---
    def test_tarea1_candelabro_es_arma_homicida(self):
        """Tarea 1: el candelabro debe ser deducido como es_arma_homicida crimen."""
        h = _buscar(self.memoria, "candelabro", "es_arma_homicida", "crimen")
        self.assertIsNotNone(h, "candelabro debe deducirse como arma homicida")

    # --- Tarea 5 (certeza del arma) ---
    def test_tarea5_certeza_arma_homicida(self):
        """
        Tarea 5: certeza del arma homicida.
        es_arma_vinculante = min(0.85, 0.90) * 0.95 = 0.81
        coincide_herida   = min(0.90, 1.00) * 1.00 = 0.90
        es_arma_homicida  = min(0.90, 0.81) * 0.95 = 0.7695 ≈ 0.77
        """
        h = _buscar(self.memoria, "candelabro", "es_arma_homicida", "crimen")
        self.assertIsNotNone(h)
        self.assertAlmostEqual(h.certeza, 0.77, places=2)

    # --- Tarea 4 ---
    def test_tarea4_coronel_sin_coartada(self):
        """Tarea 4: coronel_mostaza estaba en la escena → no_tiene_coartada."""
        h = _buscar(self.memoria, "coronel_mostaza", "no_tiene_coartada", "crimen")
        self.assertIsNotNone(h, "coronel_mostaza debe no tener coartada")

    def test_tarea4_doctor_con_coartada(self):
        """Tarea 4: doctor_orquideo sale a las 2130 < 2215 → tiene_coartada."""
        h = _buscar(self.memoria, "doctor_orquideo", "tiene_coartada", "crimen")
        self.assertIsNotNone(h, "doctor_orquideo debe tener coartada (sale a las 2130)")

    def test_tarea4_reverendo_con_coartada(self):
        """Tarea 4: reverendo_verde sale a las 2200 < 2215 → tiene_coartada."""
        h = _buscar(self.memoria, "reverendo_verde", "tiene_coartada", "crimen")
        self.assertIsNotNone(h, "reverendo_verde debe tener coartada (sale a las 2200)")

    def test_tarea4_inocentes_descartados(self):
        """Tarea 4: doctor y reverendo son descartados y declarados inocentes."""
        self.assertIsNotNone(_buscar(self.memoria, "doctor_orquideo", "es_inocente", "crimen"))
        self.assertIsNotNone(_buscar(self.memoria, "reverendo_verde", "es_inocente", "crimen"))

    # --- Tarea 2 ---
    def test_tarea2_coronel_es_sospechoso(self):
        """Tarea 2: coronel_mostaza está en la biblioteca → es_sospechoso crimen."""
        h = _buscar(self.memoria, "coronel_mostaza", "es_sospechoso", "crimen")
        self.assertIsNotNone(h, "coronel_mostaza debe ser deducido como sospechoso")

    def test_tarea2_coronel_es_sospechoso_fuerte(self):
        """Tarea 2: coronel_mostaza vinculado + sin coartada + sospechoso → es_sospechoso_fuerte."""
        h = _buscar(self.memoria, "coronel_mostaza", "es_sospechoso_fuerte", "crimen")
        self.assertIsNotNone(h, "coronel_mostaza debe ser deducido como sospechoso fuerte")

    # --- Tarea 3 ---
    def test_tarea3_culpable_deducido(self):
        """Tarea 3: coronel_mostaza es_sospechoso_fuerte + confirmado → es_culpable."""
        h = _buscar(self.memoria, "coronel_mostaza", "es_culpable", "crimen")
        self.assertIsNotNone(h, "coronel_mostaza debe ser deducido como culpable")

    def test_tarea3_inocentes_no_son_culpables(self):
        """Tarea 3: los sospechosos con coartada NO deben ser deducidos como culpables."""
        self.assertIsNone(_buscar(self.memoria, "doctor_orquideo", "es_culpable", "crimen"))
        self.assertIsNone(_buscar(self.memoria, "reverendo_verde", "es_culpable", "crimen"))

    def test_tarea5_certeza_culpable(self):
        """
        Tarea 5: certeza de coronel_mostaza como culpable.
        es_sospechoso     ≈ 0.54  (via tiene_capacidad_violenta)
        vinculado         ≈ 0.693 (huellas 0.88 * arma 0.7695 * 0.90)
        es_sospechoso_fuerte = min(0.54, 0.693, 1.0) * 0.90 ≈ 0.486
        es_culpable       = min(0.486, 0.90) * 0.95 ≈ 0.462
        """
        h = _buscar(self.memoria, "coronel_mostaza", "es_culpable", "crimen")
        self.assertIsNotNone(h)
        self.assertAlmostEqual(h.certeza, 0.46, places=2)

    # --- Idempotencia ---
    def test_encadenamiento_es_idempotente(self):
        """Ejecutar el motor una segunda vez no debe producir nuevos hechos."""
        segunda_pasada = self.motor.encadenamiento_hacia_adelante()
        self.assertEqual(segunda_pasada, 0)


# ---------------------------------------------------------------------------
# 4. Tests de encadenamiento hacia atrás sobre kb/cluedo.txt (razona si)
# ---------------------------------------------------------------------------


@unittest.skipUnless(KB_CLUEDO.exists(), "kb/cluedo.txt no disponible")
class TestEncadenamientoAtras(unittest.TestCase):
    """
    Tests funcionales del encadenamiento hacia atrás con kb/cluedo.txt.

    El encadenamiento hacia atrás es independiente del hacia adelante:
    razona desde el objetivo hasta los hechos base sin precomputar nada.
    """

    @classmethod
    def setUpClass(cls):
        cls.memoria = Memoria()
        cls.memoria.cargar_archivo(KB_CLUEDO)
        cls.motor = MotorInferencia(cls.memoria)

    def test_hipotesis_culpable_confirmada(self):
        """razona si coronel_mostaza es_culpable crimen? → debe devolver al menos un resultado."""
        resultados = list(
            self.motor.encadenamiento_hacia_atras(
                Tripleta("coronel_mostaza", "es_culpable", "crimen")
            )
        )
        self.assertGreater(len(resultados), 0)

    def test_hipotesis_inocente_denegada(self):
        """razona si doctor_orquideo es_culpable crimen? → no puede (sale antes del crimen)."""
        resultados = list(
            self.motor.encadenamiento_hacia_atras(
                Tripleta("doctor_orquideo", "es_culpable", "crimen")
            )
        )
        self.assertEqual(len(resultados), 0)

    def test_consulta_variable_quien_es_culpable(self):
        """razona si X es_culpable crimen? → X debe incluir a coronel_mostaza."""
        resultados = list(
            self.motor.encadenamiento_hacia_atras(Tripleta("X", "es_culpable", "crimen"))
        )
        self.assertGreater(len(resultados), 0)
        valores_x = {sust.get("X") for sust, _ in resultados if "X" in sust}
        self.assertIn("coronel_mostaza", valores_x)

    def test_consulta_variable_sin_resultados(self):
        """razona si X es fantasma? → predicado inexistente, sin resultados."""
        resultados = list(
            self.motor.encadenamiento_hacia_atras(Tripleta("X", "es", "fantasma"))
        )
        self.assertEqual(len(resultados), 0)

    def test_arma_homicida_confirmada_backward(self):
        """razona si candelabro es_arma_homicida crimen? → debe derivarse por reglas."""
        resultados = list(
            self.motor.encadenamiento_hacia_atras(
                Tripleta("candelabro", "es_arma_homicida", "crimen")
            )
        )
        self.assertGreater(len(resultados), 0)
        certeza_max = max(c for _, c in resultados)
        self.assertGreater(certeza_max, 0.5)

    def test_hecho_base_se_confirma_directamente(self):
        """Un hecho que ya está en memoria base se confirma sin recurrir a reglas."""
        resultados = list(
            self.motor.encadenamiento_hacia_atras(
                Tripleta("coronel_mostaza", "ubicacion_crimen", "biblioteca")
            )
        )
        self.assertGreater(len(resultados), 0)
        certeza = resultados[0][1]
        self.assertAlmostEqual(certeza, 1.0)

    def test_hecho_base_falso_se_deniega(self):
        """Un hecho que no existe en memoria ni es deducible debe devolver vacío."""
        resultados = list(
            self.motor.encadenamiento_hacia_atras(
                Tripleta("coronel_mostaza", "ubicacion_crimen", "cocina")
            )
        )
        self.assertEqual(len(resultados), 0)


# ---------------------------------------------------------------------------
# 5. Tests de consultas directas (sin encadenamiento)
# ---------------------------------------------------------------------------


@unittest.skipUnless(KB_CLUEDO.exists(), "kb/cluedo.txt no disponible")
class TestConsultarHechos(unittest.TestCase):
    """Tests para MotorInferencia.consultar_hechos() (búsqueda directa en memoria)."""

    @classmethod
    def setUpClass(cls):
        cls.memoria = Memoria()
        cls.memoria.cargar_archivo(KB_CLUEDO)
        cls.motor = MotorInferencia(cls.memoria)

    def test_hecho_existente_encontrado(self):
        resultados = self.motor.consultar_hechos(
            Tripleta("coronel_mostaza", "ubicacion_crimen", "biblioteca")
        )
        self.assertGreater(len(resultados), 0)

    def test_certeza_hecho_base_es_uno(self):
        resultados = self.motor.consultar_hechos(
            Tripleta("coronel_mostaza", "ubicacion_crimen", "biblioteca")
        )
        self.assertAlmostEqual(resultados[0][1], 1.0)

    def test_hecho_inexistente_devuelve_lista_vacia(self):
        resultados = self.motor.consultar_hechos(
            Tripleta("coronel_mostaza", "ubicacion_crimen", "cocina")
        )
        self.assertEqual(len(resultados), 0)

    def test_consulta_con_variable_devuelve_bindings(self):
        """X esta_en biblioteca? → X debe enlazarse a candelabro y cuerda."""
        resultados = self.motor.consultar_hechos(Tripleta("X", "esta_en", "biblioteca"))
        valores = {sust["X"] for sust, _ in resultados}
        self.assertIn("candelabro", valores)
        self.assertIn("cuerda", valores)

    def test_consulta_con_certeza_difusa_correcta(self):
        """El hecho 'candelabro tiene_sangre si' tiene certeza 0.85."""
        resultados = self.motor.consultar_hechos(
            Tripleta("candelabro", "tiene_sangre", "si")
        )
        self.assertGreater(len(resultados), 0)
        self.assertAlmostEqual(resultados[0][1], 0.85)

    def test_consulta_todos_los_sospechosos(self):
        """X es_tipo persona? → deben encontrarse los 6 sospechosos del caso."""
        resultados = self.motor.consultar_hechos(Tripleta("X", "es_tipo", "persona"))
        valores = {sust["X"] for sust, _ in resultados}
        self.assertEqual(len(valores), 6)
        self.assertIn("coronel_mostaza", valores)
        self.assertIn("profesora_ciruelo", valores)


# ---------------------------------------------------------------------------
# 6. Tests de robustez: bucles, cadenas profundas y fronteras matemáticas
# ---------------------------------------------------------------------------


class TestRobustezBucleCircular(unittest.TestCase):
    """
    Verifica que el motor no entra en bucle infinito con reglas circulares.
    El control de profundidad (nivel > 15) debe garantizar la terminación.
    """

    KB_BUCLE = """
gallina crea huevo.
X crea huevo <- X crea gallina.
X crea gallina <- X crea huevo.
"""

    def test_forward_chaining_termina_con_reglas_circulares(self):
        memoria, motor = _cargar_kb(self.KB_BUCLE)
        try:
            motor.encadenamiento_hacia_adelante()
        except RecursionError:
            self.fail("El encadenamiento hacia adelante entró en recursión infinita")

    def test_backward_chaining_termina_con_reglas_circulares(self):
        memoria, motor = _cargar_kb(self.KB_BUCLE)
        try:
            resultados = list(
                motor.encadenamiento_hacia_atras(Tripleta("gallina", "crea", "huevo"))
            )
            # El hecho base 'gallina crea huevo' debe encontrarse directamente
            self.assertGreater(len(resultados), 0)
        except RecursionError:
            self.fail("El encadenamiento hacia atrás entró en recursión infinita")


class TestRobustezCadenaProfunda(unittest.TestCase):
    """Verifica que el motor resuelve cadenas de reglas encadenadas (multi-salto)."""

    KB_CADENA = """
eslabon_3 conecta_con fin.
eslabon_2 conecta_con eslabon_3.
eslabon_1 conecta_con eslabon_2.
X llega_a fin <- X conecta_con fin.
X llega_a fin <- X conecta_con Y, Y llega_a fin.
"""

    def test_cadena_tres_eslabones_forward(self):
        """eslabon_1 debe llegar a fin tras 3 aplicaciones de la regla transitiva."""
        memoria, motor = _cargar_kb(self.KB_CADENA)
        motor.encadenamiento_hacia_adelante()
        h = _buscar(memoria, "eslabon_1", "llega_a", "fin")
        self.assertIsNotNone(
            h, "eslabon_1 debe alcanzar 'fin' por encadenamiento hacia adelante"
        )

    def test_cadena_tres_eslabones_backward(self):
        """El encadenamiento hacia atrás debe resolver la cadena de 3 saltos."""
        memoria, motor = _cargar_kb(self.KB_CADENA)
        resultados = list(
            motor.encadenamiento_hacia_atras(Tripleta("eslabon_1", "llega_a", "fin"))
        )
        self.assertGreater(len(resultados), 0)

    def test_eslabon_directo_llega_a_fin(self):
        """eslabon_3 está directamente conectado a fin."""
        memoria, motor = _cargar_kb(self.KB_CADENA)
        motor.encadenamiento_hacia_adelante()
        h = _buscar(memoria, "eslabon_3", "llega_a", "fin")
        self.assertIsNotNone(h)


class TestFronterasMatemáticas(unittest.TestCase):
    """
    Tests de los casos límite exactos de las restricciones aritméticas (Tarea 4).
    Verifica que los operadores <, <=, >, >=, = son precisos en las fronteras.
    """

    KB_EDADES = """
sujeto_a edad 20.
sujeto_b edad 25.
sujeto_c edad 30.
X es grupo_menor  <- X edad E. [ E < 25 ]
X es grupo_exacto <- X edad E. [ E = 25 ]
X es grupo_mayor  <- X edad E. [ E > 25 ]
X es grupo_menori <- X edad E. [ E <= 25 ]
X es grupo_mayori <- X edad E. [ E >= 25 ]
"""

    @classmethod
    def setUpClass(cls):
        cls.memoria, cls.motor = _cargar_kb(cls.KB_EDADES)
        cls.motor.encadenamiento_hacia_adelante()

    def test_20_es_grupo_menor(self):
        self.assertIsNotNone(_buscar(self.memoria, "sujeto_a", "es", "grupo_menor"))

    def test_25_no_es_grupo_menor(self):
        """25 < 25 es FALSO: sujeto_b no debe pertenecer a grupo_menor."""
        self.assertIsNone(_buscar(self.memoria, "sujeto_b", "es", "grupo_menor"))

    def test_25_es_grupo_exacto(self):
        self.assertIsNotNone(_buscar(self.memoria, "sujeto_b", "es", "grupo_exacto"))

    def test_20_no_es_grupo_exacto(self):
        self.assertIsNone(_buscar(self.memoria, "sujeto_a", "es", "grupo_exacto"))

    def test_30_es_grupo_mayor(self):
        self.assertIsNotNone(_buscar(self.memoria, "sujeto_c", "es", "grupo_mayor"))

    def test_25_no_es_grupo_mayor(self):
        """25 > 25 es FALSO: sujeto_b no debe pertenecer a grupo_mayor."""
        self.assertIsNone(_buscar(self.memoria, "sujeto_b", "es", "grupo_mayor"))

    def test_25_es_grupo_menori(self):
        """25 <= 25 es VERDADERO: sujeto_b sí pertenece al grupo con <=."""
        self.assertIsNotNone(_buscar(self.memoria, "sujeto_b", "es", "grupo_menori"))

    def test_25_es_grupo_mayori(self):
        """25 >= 25 es VERDADERO: sujeto_b sí pertenece al grupo con >=."""
        self.assertIsNotNone(_buscar(self.memoria, "sujeto_b", "es", "grupo_mayori"))

    def test_20_no_es_grupo_mayori(self):
        """20 >= 25 es FALSO."""
        self.assertIsNone(_buscar(self.memoria, "sujeto_a", "es", "grupo_mayori"))


# ---------------------------------------------------------------------------
# 7. Tests de lógica difusa (Tarea 5): T-norma mínimo y multiplicación
# ---------------------------------------------------------------------------


class TestLogicaDifusa(unittest.TestCase):
    """
    Tests de propagación de incertidumbre (lógica difusa).

    El sistema implementa:
      - T-norma del mínimo para los antecedentes de una regla.
      - Multiplicación de la certeza de la regla sobre el resultado del mínimo.
    """

    def test_t_norma_minimo_dos_antecedentes(self):
        """
        Dos antecedentes con certezas 0.8 y 0.6: min(0.8, 0.6) = 0.6.
        Multiplicado por certeza de regla 0.9 → 0.54.
        """
        kb = "a_x es p. [ 0.8 ]\nb_y es q. [ 0.6 ]\nc_z es r <- a_x es p, b_y es q. [ 0.9 ]\n"
        memoria, motor = _cargar_kb(kb)
        motor.encadenamiento_hacia_adelante()
        h = _buscar(memoria, "c_z", "es", "r")
        self.assertIsNotNone(h)
        self.assertAlmostEqual(h.certeza, 0.54, places=5)

    def test_multiplicacion_certeza_regla(self):
        """
        Un antecedente con certeza 0.7 y una regla con certeza 0.5:
        certeza_final = 0.7 × 0.5 = 0.35.
        """
        kb = "hecho1 es p. [ 0.7 ]\nresultado es q <- hecho1 es p. [ 0.5 ]\n"
        memoria, motor = _cargar_kb(kb)
        motor.encadenamiento_hacia_adelante()
        h = _buscar(memoria, "resultado", "es", "q")
        self.assertIsNotNone(h)
        self.assertAlmostEqual(h.certeza, 0.35, places=5)

    def test_certeza_uno_no_degrada(self):
        """Con todos los hechos y regla a certeza 1.0, el resultado debe ser 1.0."""
        kb = "hecho es p.\nresultado es q <- hecho es p. [ 1.0 ]\n"
        memoria, motor = _cargar_kb(kb)
        motor.encadenamiento_hacia_adelante()
        h = _buscar(memoria, "resultado", "es", "q")
        self.assertIsNotNone(h)
        self.assertAlmostEqual(h.certeza, 1.0, places=5)

    def test_certeza_minima_impone_cota(self):
        """
        Tres antecedentes [1.0, 0.3, 1.0] con regla 1.0 → resultado = 0.3.
        El mínimo (0.3) es quien limita la certeza total.
        """
        kb = (
            "a1 es p.\n"
            "a2 es q. [ 0.3 ]\n"
            "a3 es r.\n"
            "resultado es z <- a1 es p, a2 es q, a3 es r. [ 1.0 ]\n"
        )
        memoria, motor = _cargar_kb(kb)
        motor.encadenamiento_hacia_adelante()
        h = _buscar(memoria, "resultado", "es", "z")
        self.assertIsNotNone(h)
        self.assertAlmostEqual(h.certeza, 0.3, places=5)

    def test_motor_no_degrada_certeza_existente(self):
        """
        El motor de encadenamiento hacia adelante NO debe reducir la certeza
        de un hecho ya conocido aunque encuentre un camino con certeza menor.
        """
        # Hecho deducido con 0.9 en la primera pasada
        kb = (
            "base es p. [ 0.9 ]\n"
            "base2 es p. [ 0.3 ]\n"
            "resultado es q <- base es p. [ 1.0 ]\n"
            "resultado es q <- base2 es p. [ 1.0 ]\n"
        )
        memoria, motor = _cargar_kb(kb)
        motor.encadenamiento_hacia_adelante()
        h = _buscar(memoria, "resultado", "es", "q")
        self.assertIsNotNone(h)
        # El motor debe conservar la certeza máxima (0.9), no degradarla a 0.3
        self.assertAlmostEqual(h.certeza, 0.9, places=5)

    def test_certeza_forward_backward_coherentes(self):
        """
        La certeza calculada por forward y backward chaining deben coincidir.
        """
        kb = "base es hecho. [ 0.7 ]\nresult es deducido <- base es hecho. [ 0.8 ]\n"
        memoria, motor = _cargar_kb(kb)

        # Forward
        motor.encadenamiento_hacia_adelante()
        h_forward = _buscar(memoria, "result", "es", "deducido")
        self.assertIsNotNone(h_forward)
        certeza_forward = h_forward.certeza

        # Backward (sobre la misma memoria que ya tiene los hechos base)
        resultados_back = list(
            motor.encadenamiento_hacia_atras(Tripleta("result", "es", "deducido"))
        )
        self.assertGreater(len(resultados_back), 0)
        certeza_backward = max(c for _, c in resultados_back)

        self.assertAlmostEqual(certeza_forward, certeza_backward, places=5)


class TestPrecedenciaReglas(unittest.TestCase):
    """
    Tests funcionales de la Precedencia de Reglas.

    Verifica que el motor evalúa las reglas de mayor precedencia antes que las
    de menor precedencia, tanto en forward chaining (orden de deducción) como
    en backward chaining (orden de resultados devueltos).
    """

    def test_memoria_ordena_reglas_por_precedencia_descendente(self):
        """
        Tras cargar reglas con distintas precedencias, self.reglas debe estar
        ordenada de mayor a menor precedencia.
        """
        kb = (
            "base es p.\n"
            "res_baja es q <- base es p.\n"  # precedencia = 0 (defecto)
            "res_alta es q <- base es p. [ 090 ]\n"  # precedencia = 90
            "res_media es q <- base es p. [ 050 ]\n"  # precedencia = 50
        )
        memoria, _ = _cargar_kb(kb)
        precedencias = [r.precedencia for r in memoria.reglas]
        self.assertEqual(precedencias, sorted(precedencias, reverse=True))

    def test_regla_alta_precedencia_se_evalua_primero_backward(self):
        """
        Con dos reglas que prueban 'P es resultado', la de mayor precedencia
        debe devolver su solución PRIMERO en backward chaining.

        Las reglas deben tener variables en el consecuente para que la
        unificación funcione contra la consulta 'X es resultado'.
        """
        kb = (
            # Dos fuentes: tipo_a y tipo_b
            "candidato_a es tipo_a.\n"
            "candidato_b es tipo_b.\n"
            # Regla de baja prioridad: resuelve vía tipo_b
            "P es resultado <- P es tipo_b.\n"
            # Regla de alta prioridad: resuelve vía tipo_a (debe ir primera)
            "P es resultado <- P es tipo_a. [ 090 ]\n"
        )
        memoria, motor = _cargar_kb(kb)
        resultados = list(
            motor.encadenamiento_hacia_atras(Tripleta("X", "es", "resultado"))
        )
        self.assertGreater(len(resultados), 0)
        # La regla de prec=90 debe dar su resultado antes que la de prec=0
        # La regla [090] usa tipo_a → candidato_a debe ser el primer X
        primer_x = resultados[0][0].get("X")
        self.assertEqual(primer_x, "candidato_a")

    def test_todas_las_reglas_se_evaluan_independientemente_de_precedencia(self):
        """
        La precedencia define el ORDEN de evaluación, no excluye reglas.
        Todas las reglas aplicables deben producir resultados eventualmente.
        """
        kb = (
            "base_a es hecho.\n"
            "base_b es hecho.\n"
            "opcion_a es valida <- base_a es hecho.\n"
            "opcion_b es valida <- base_b es hecho. [ 099 ]\n"
        )
        memoria, motor = _cargar_kb(kb)
        motor.encadenamiento_hacia_adelante()
        # Ambas opciones deben deducirse
        self.assertIsNotNone(_buscar(memoria, "opcion_a", "es", "valida"))
        self.assertIsNotNone(_buscar(memoria, "opcion_b", "es", "valida"))

    def test_precedencia_alta_deduce_primero_en_forward(self):
        """
        En forward chaining, la regla de mayor precedencia debe deducir su
        conclusión antes que la de menor precedencia (orden en hechos derivados).
        """
        kb = (
            "base_baja es p.\n"
            "base_alta es p.\n"
            "concl_baja es derivado <- base_baja es p.\n"
            "concl_alta es derivado <- base_alta es p. [ 080 ]\n"
        )
        memoria, motor = _cargar_kb(kb)
        motor.encadenamiento_hacia_adelante()
        hechos_derivados = [
            h.tripleta.sujeto
            for h in memoria.hechos
            if h.tripleta.predicado == "es" and h.tripleta.objeto == "derivado"
        ]
        # concl_alta debe aparecer antes que concl_baja
        self.assertIn("concl_alta", hechos_derivados)
        self.assertIn("concl_baja", hechos_derivados)
        self.assertLess(
            hechos_derivados.index("concl_alta"),
            hechos_derivados.index("concl_baja"),
        )

    def test_reglas_sin_precedencia_tienen_valor_cero(self):
        """Las reglas sin bloque de extensión tienen precedencia = 0."""
        kb = "base es p.\nresultado es q <- base es p.\n"
        memoria, _ = _cargar_kb(kb)
        self.assertEqual(memoria.reglas[0].precedencia, 0)

    def test_precedencia_no_afecta_certeza_ni_restricciones(self):
        """
        Añadir una precedencia a una regla no debe alterar su certeza ni
        sus restricciones aritméticas.
        """
        kb = "base llega Hora.\nresultado es q <- base llega Hora. [ 0.7; 050; Hora > 10 ]\n"
        memoria, _ = _cargar_kb(kb)
        r = memoria.reglas[0]
        self.assertEqual(r.precedencia, 50)
        self.assertAlmostEqual(r.certeza, 0.7)
        self.assertEqual(len(r.restricciones), 1)
        self.assertEqual(r.restricciones[0].operador, ">")


if __name__ == "__main__":
    unittest.main(verbosity=2)
