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
KB_CLUEDO = KB_DIR / "cluedo.txt"


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
        if not KB_CLUEDO.exists():
            self.skipTest("kb/cluedo.txt no disponible")
        resultado = self.memoria.cargar_archivo(KB_CLUEDO)
        self.assertTrue(resultado)

    def test_carga_archivo_existente_popula_hechos_y_reglas(self):
        if not KB_CLUEDO.exists():
            self.skipTest("kb/cluedo.txt no disponible")
        self.memoria.cargar_archivo(KB_CLUEDO)
        self.assertGreater(len(self.memoria.hechos), 0)
        self.assertGreater(len(self.memoria.reglas), 0)

    def test_carga_cluedo_conteo_exacto(self):
        """cluedo.txt contiene exactamente 100 hechos y 46 reglas."""
        if not KB_CLUEDO.exists():
            self.skipTest("kb/cluedo.txt no disponible")
        self.memoria.cargar_archivo(KB_CLUEDO)
        self.assertEqual(len(self.memoria.hechos), 100)
        self.assertEqual(len(self.memoria.reglas), 46)

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
        contenido = (
            "coronel_mostaza esta_en biblioteca.\n# comentario final sin salto\n"
        )
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
        if not KB_CLUEDO.exists():
            self.skipTest("kb/cluedo.txt no disponible")
        memoria.cargar_archivo(KB_CLUEDO)
        memoria.limpiar()
        self.assertEqual(len(memoria.hechos), 0)
        self.assertEqual(len(memoria.reglas), 0)

    def test_limpiar_memoria_vacia_no_falla(self):
        memoria = Memoria()
        memoria.limpiar()
        self.assertEqual(len(memoria.hechos), 0)


class TestMemoriaCargarDirectorio(unittest.TestCase):
    """Tests para Memoria.cargar_archivo() cuando se le pasa una carpeta."""

    def setUp(self):
        self.memoria = Memoria()
        # Directorio temporal que se crea/destruye por test
        self.tmpdir = tempfile.mkdtemp()
        self.dir_path = Path(self.tmpdir)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _escribir_txt(self, nombre: str, contenido: str) -> Path:
        ruta = self.dir_path / nombre
        ruta.write_text(contenido, encoding="utf-8")
        return ruta

    def test_carga_directorio_combina_todos_txt(self):
        """Todos los .txt de la carpeta se concatenan y se cargan juntos."""
        self._escribir_txt("a.txt", "hecho_a es_tipo fact.\n")
        self._escribir_txt("b.txt", "hecho_b es_tipo fact.\n")
        resultado = self.memoria.cargar_archivo(self.dir_path)
        self.assertTrue(resultado)
        self.assertEqual(len(self.memoria.hechos), 2)

    def test_carga_directorio_devuelve_true(self):
        """cargar_archivo devuelve True cuando la carpeta contiene .txt válidos."""
        self._escribir_txt("solo.txt", "victima sufre contusion.\n")
        resultado = self.memoria.cargar_archivo(self.dir_path)
        self.assertTrue(resultado)

    def test_carga_directorio_un_solo_txt(self):
        """Un directorio con un único .txt se comporta como cargar_archivo sobre ese fichero."""
        self._escribir_txt("unico.txt", "sospechoso tiene_coartada si.\n")
        self.memoria.cargar_archivo(self.dir_path)
        self.assertEqual(len(self.memoria.hechos), 1)

    def test_carga_directorio_ignora_no_txt(self):
        """Los archivos que no sean .txt (p.ej. .md, .csv) deben ser ignorados."""
        self._escribir_txt("valido.txt", "pista_a apunta_a sospechoso.\n")
        (self.dir_path / "ignorado.md").write_text("# esto no es KB\n", encoding="utf-8")
        (self.dir_path / "ignorado.csv").write_text("col1,col2\n", encoding="utf-8")
        resultado = self.memoria.cargar_archivo(self.dir_path)
        self.assertTrue(resultado)
        self.assertEqual(len(self.memoria.hechos), 1)

    def test_carga_directorio_vacio_devuelve_false(self):
        """Un directorio sin ningún .txt debe devolver False."""
        resultado = self.memoria.cargar_archivo(self.dir_path)
        self.assertFalse(resultado)

    def test_carga_directorio_vacio_no_modifica_memoria(self):
        """Un directorio vacío no debe alterar la memoria."""
        resultado = self.memoria.cargar_archivo(self.dir_path)
        self.assertFalse(resultado)
        self.assertEqual(len(self.memoria.hechos), 0)
        self.assertEqual(len(self.memoria.reglas), 0)

    def test_carga_directorio_orden_alfabetico(self):
        """Los archivos se procesan en orden alfabético (determinista).

        Ambos ficheros definen el mismo hecho con distinta certeza.
        En orden a < z: primero certeza 0.3 (a.txt), luego 0.9 (z.txt)
        → la certeza final es 0.9.
        Si el orden fuera inverso (z antes que a), la certeza final sería 0.3.
        """
        self._escribir_txt("a.txt", "objeto tiene_atributo valor. [ 0.3 ]\n")
        self._escribir_txt("z.txt", "objeto tiene_atributo valor. [ 0.9 ]\n")
        self.memoria.cargar_archivo(self.dir_path)
        self.assertEqual(len(self.memoria.hechos), 1)
        self.assertAlmostEqual(self.memoria.hechos[0].certeza, 0.9)

    def test_carga_directorio_con_sintaxis_erronea_devuelve_false(self):
        """Si algún .txt del directorio tiene error sintáctico, toda la carga falla."""
        self._escribir_txt("bueno.txt", "hecho_ok es_tipo fact.\n")
        self._escribir_txt("malo.txt", "esto no es sintaxis valida ???\n")
        resultado = self.memoria.cargar_archivo(self.dir_path)
        self.assertFalse(resultado)

    def test_carga_directorio_inexistente_devuelve_false(self):
        """Una ruta a un directorio que no existe devuelve False."""
        resultado = self.memoria.cargar_archivo(self.dir_path / "no_existe")
        self.assertFalse(resultado)

    def test_carga_directorio_acumula_con_carga_previa(self):
        """Cargar un directorio sobre una memoria ya poblada acumula, no reemplaza."""
        self.memoria.cargar_archivo(_crear_kb_temporal("hecho_previo es_tipo base.\n"))
        self._escribir_txt("nuevo.txt", "hecho_nuevo es_tipo extra.\n")
        self.memoria.cargar_archivo(self.dir_path)
        self.assertEqual(len(self.memoria.hechos), 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
