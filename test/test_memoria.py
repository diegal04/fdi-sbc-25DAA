"""
Tests funcionales del módulo sbc.memory.

Verifica la carga de archivos de conocimiento, la gestión de hechos
(afirmación, actualización, revocación) y la gestión de reglas.
"""

import os
import tempfile
import unittest
from pathlib import Path

from sbc.memory import Memoria
from sbc.parser import Hecho, Regla, Tripleta

# Ruta a los archivos de conocimiento del proyecto
KB_DIR = Path(__file__).parent.parent / "kb"
KB_MISTERIO = KB_DIR / "misterio.txt"


def _crear_kb_temporal(contenido: str) -> Path:
    """Crea un fichero .txt temporal con el contenido dado y devuelve su ruta."""
    fd, ruta = tempfile.mkstemp(suffix=".txt")
    try:
        os.write(fd, contenido.encode("utf-8"))
    finally:
        os.close(fd)
    return Path(ruta)


class TestMemoriaCargarArchivo(unittest.TestCase):
    """Tests para Memoria.cargar_archivo()."""

    def setUp(self):
        self.memoria = Memoria()

    def test_carga_archivo_existente_devuelve_true(self):
        if not KB_MISTERIO.exists():
            self.skipTest("kb/misterio.txt no disponible")
        resultado = self.memoria.cargar_archivo(KB_MISTERIO)
        self.assertTrue(resultado)

    def test_carga_archivo_existente_popula_hechos_y_reglas(self):
        if not KB_MISTERIO.exists():
            self.skipTest("kb/misterio.txt no disponible")
        self.memoria.cargar_archivo(KB_MISTERIO)
        self.assertGreater(len(self.memoria.hechos), 0)
        self.assertGreater(len(self.memoria.reglas), 0)

    def test_carga_misterio_conteo_exacto(self):
        """misterio.txt contiene exactamente 11 hechos y 5 reglas."""
        if not KB_MISTERIO.exists():
            self.skipTest("kb/misterio.txt no disponible")
        self.memoria.cargar_archivo(KB_MISTERIO)
        self.assertEqual(len(self.memoria.hechos), 11)
        self.assertEqual(len(self.memoria.reglas), 5)

    def test_carga_archivo_inexistente_devuelve_false(self):
        resultado = self.memoria.cargar_archivo("ruta/que/no/existe.txt")
        self.assertFalse(resultado)

    def test_carga_archivo_inexistente_no_modifica_memoria(self):
        self.memoria.cargar_archivo("no_existe.txt")
        self.assertEqual(len(self.memoria.hechos), 0)
        self.assertEqual(len(self.memoria.reglas), 0)

    def test_carga_archivo_con_sintaxis_erronea_devuelve_false(self):
        ruta = _crear_kb_temporal("esto no es sintaxis valida ???\n")
        try:
            resultado = self.memoria.cargar_archivo(ruta)
            self.assertFalse(resultado)
        finally:
            ruta.unlink()

    def test_carga_archivo_utf8(self):
        """El sistema lee correctamente ficheros con caracteres UTF-8 en comentarios."""
        contenido = "# Comentario con acentos: áéíóú\nvictima sufre contusion.\n"
        ruta = _crear_kb_temporal(contenido)
        try:
            resultado = self.memoria.cargar_archivo(ruta)
            self.assertTrue(resultado)
            self.assertEqual(len(self.memoria.hechos), 1)
        finally:
            ruta.unlink()

    def test_carga_archivo_con_comentario_al_final(self):
        """Bug fix: un comentario al final del archivo no debe romper parse_all=True."""
        contenido = "coronel_mostaza esta_en biblioteca.\n# comentario final sin salto\n"
        ruta = _crear_kb_temporal(contenido)
        try:
            resultado = self.memoria.cargar_archivo(ruta)
            self.assertTrue(resultado)
            self.assertEqual(len(self.memoria.hechos), 1)
        finally:
            ruta.unlink()

    def test_carga_archivo_solo_comentarios(self):
        """Un archivo con solo comentarios es válido sintácticamente (cero hechos)."""
        contenido = "# solo comentarios\n# sin declaraciones\n"
        ruta = _crear_kb_temporal(contenido)
        try:
            resultado = self.memoria.cargar_archivo(ruta)
            self.assertTrue(resultado)
            self.assertEqual(len(self.memoria.hechos), 0)
            self.assertEqual(len(self.memoria.reglas), 0)
        finally:
            ruta.unlink()

    def test_carga_multiples_archivos_acumula(self):
        """Cargar dos archivos debe acumular sus contenidos en la misma memoria."""
        kb1 = _crear_kb_temporal("a es b.\n")
        kb2 = _crear_kb_temporal("c es d.\n")
        try:
            self.memoria.cargar_archivo(kb1)
            self.memoria.cargar_archivo(kb2)
            self.assertEqual(len(self.memoria.hechos), 2)
        finally:
            kb1.unlink()
            kb2.unlink()


class TestMemoriaAgregarHecho(unittest.TestCase):
    """Tests para Memoria.agregar_hecho(): afirmaciones, actualizaciones y revocaciones."""

    def setUp(self):
        self.memoria = Memoria()

    def _hecho(self, s: str, p: str, o: str, certeza: float = 1.0) -> Hecho:
        return Hecho(Tripleta(s, p, o), certeza=certeza)

    def test_agregar_hecho_nuevo_devuelve_true(self):
        resultado = self.memoria.agregar_hecho(self._hecho("a", "b", "c"))
        self.assertTrue(resultado)

    def test_agregar_hecho_nuevo_incrementa_contador(self):
        self.memoria.agregar_hecho(self._hecho("a", "b", "c"))
        self.assertEqual(len(self.memoria.hechos), 1)

    def test_agregar_hecho_duplicado_no_duplica_lista(self):
        """Añadir un hecho idéntico dos veces no genera duplicados en memoria."""
        h = self._hecho("a", "b", "c")
        self.memoria.agregar_hecho(h)
        self.memoria.agregar_hecho(h)
        self.assertEqual(len(self.memoria.hechos), 1)

    def test_agregar_hecho_duplicado_devuelve_true(self):
        """Añadir un duplicado debe devolver True (el hecho ya existe = éxito)."""
        h = self._hecho("a", "b", "c")
        self.memoria.agregar_hecho(h)
        resultado = self.memoria.agregar_hecho(h)
        self.assertTrue(resultado)

    def test_agregar_hecho_actualiza_certeza_mayor(self):
        """Si el mismo hecho llega con mayor certeza, esta se actualiza."""
        self.memoria.agregar_hecho(self._hecho("a", "b", "c", certeza=0.4))
        self.memoria.agregar_hecho(self._hecho("a", "b", "c", certeza=0.9))
        self.assertEqual(len(self.memoria.hechos), 1)
        self.assertAlmostEqual(self.memoria.hechos[0].certeza, 0.9)

    def test_agregar_hecho_sobreescribe_certeza(self):
        """Memoria.agregar_hecho siempre sobreescribe la certeza con el nuevo valor.
        La protección 'solo actualiza si es mayor' es responsabilidad del motor."""
        self.memoria.agregar_hecho(self._hecho("a", "b", "c", certeza=0.9))
        self.memoria.agregar_hecho(self._hecho("a", "b", "c", certeza=0.3))
        self.assertAlmostEqual(self.memoria.hechos[0].certeza, 0.3)

    def test_revocar_hecho_existente_devuelve_true(self):
        self.memoria.agregar_hecho(self._hecho("a", "b", "c"))
        negacion = Hecho(Tripleta("a", "b", "c"), negado=True)
        resultado = self.memoria.agregar_hecho(negacion)
        self.assertTrue(resultado)

    def test_revocar_hecho_existente_elimina_de_memoria(self):
        self.memoria.agregar_hecho(self._hecho("a", "b", "c"))
        self.memoria.agregar_hecho(Hecho(Tripleta("a", "b", "c"), negado=True))
        self.assertEqual(len(self.memoria.hechos), 0)

    def test_revocar_hecho_inexistente_devuelve_false(self):
        negacion = Hecho(Tripleta("x", "y", "z"), negado=True)
        resultado = self.memoria.agregar_hecho(negacion)
        self.assertFalse(resultado)

    def test_revocar_hecho_inexistente_no_modifica_memoria(self):
        self.memoria.agregar_hecho(self._hecho("a", "b", "c"))
        self.memoria.agregar_hecho(Hecho(Tripleta("x", "y", "z"), negado=True))
        self.assertEqual(len(self.memoria.hechos), 1)

    def test_revocar_solo_el_hecho_correcto(self):
        """La revocación debe eliminar solo el hecho coincidente, no otros."""
        self.memoria.agregar_hecho(self._hecho("a", "b", "c"))
        self.memoria.agregar_hecho(self._hecho("d", "e", "f"))
        self.memoria.agregar_hecho(Hecho(Tripleta("a", "b", "c"), negado=True))
        self.assertEqual(len(self.memoria.hechos), 1)
        self.assertEqual(self.memoria.hechos[0].tripleta, Tripleta("d", "e", "f"))


class TestMemoriaAgregarRegla(unittest.TestCase):
    """Tests para Memoria.agregar_regla(): deduplicación."""

    def setUp(self):
        self.memoria = Memoria()

    def _regla(self) -> Regla:
        return Regla(
            consecuente=Tripleta("X", "es", "sospechoso"),
            antecedentes=[Tripleta("X", "es_tipo", "persona")],
        )

    def test_agregar_regla_nueva(self):
        self.memoria.agregar_regla(self._regla())
        self.assertEqual(len(self.memoria.reglas), 1)

    def test_agregar_regla_duplicada_no_duplica(self):
        """Añadir la misma regla dos veces no debe duplicarla en memoria."""
        r = self._regla()
        self.memoria.agregar_regla(r)
        self.memoria.agregar_regla(r)
        self.assertEqual(len(self.memoria.reglas), 1)

    def test_reglas_con_distinto_consecuente_se_acumulan(self):
        r1 = Regla(
            consecuente=Tripleta("X", "es", "sospechoso"),
            antecedentes=[Tripleta("X", "es_tipo", "persona")],
        )
        r2 = Regla(
            consecuente=Tripleta("X", "es", "asesino"),
            antecedentes=[Tripleta("X", "es", "sospechoso")],
        )
        self.memoria.agregar_regla(r1)
        self.memoria.agregar_regla(r2)
        self.assertEqual(len(self.memoria.reglas), 2)


class TestMemoriaLimpiar(unittest.TestCase):
    """Tests para Memoria.limpiar()."""

    def test_limpiar_borra_hechos_y_reglas(self):
        memoria = Memoria()
        if not KB_MISTERIO.exists():
            self.skipTest("kb/misterio.txt no disponible")
        memoria.cargar_archivo(KB_MISTERIO)
        memoria.limpiar()
        self.assertEqual(len(memoria.hechos), 0)
        self.assertEqual(len(memoria.reglas), 0)

    def test_limpiar_memoria_vacia_no_falla(self):
        memoria = Memoria()
        memoria.limpiar()
        self.assertEqual(len(memoria.hechos), 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
