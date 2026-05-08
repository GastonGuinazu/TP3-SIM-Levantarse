"""
QA automatizado — motor Montecarlo, validaciones (sin depender de PyQt5).

Ejecutar desde la carpeta del proyecto:
  py -3.11 -m unittest discover -s tests -v

Nota: en Windows conviene Python 3.11/3.12 para wheels de NumPy/PyQt5; 3.13 puede fallar al instalar.

Cobertura tipo revision profesional:
  - Entradas invalidas (0, negativos, sumas incorrectas, rangos).
  - Escenarios deterministas (probabilidades 0/1, uniformes degenerados).
  - Invariantes (promedio, filas devueltas, reproducibilidad por semilla).
"""

from __future__ import annotations

import unittest
from unittest.mock import patch

from funciones import GeneradorAleatorio
from monte_carlo import ParametrosSimulacion, SimuladorLevantarse, validar_parametros_entrada


def _p(**kwargs) -> ParametrosSimulacion:
    """Parametros por defecto sanos; override con kwargs."""
    base = dict(
        dias=100,
        fila_desde=1,
        umbral_tarde=45.0,
        seed=42,
        pausa_min=5.0,
        pausa_max=7.0,
        actividad_min=5.0,
        actividad_max=10.0,
        prob_demora_extra=0.25,
        media_demora_extra=8.0,
    )
    base.update(kwargs)
    return ParametrosSimulacion(**base)


class TestValidacionParametros(unittest.TestCase):
    """Misma logica que la UI: `validar_parametros_entrada` en `monte_carlo.py`."""

    def assert_invalid(self, p: ParametrosSimulacion, substring: str = ""):
        err = validar_parametros_entrada(p)
        self.assertNotEqual(err, "", f"Se esperaba error para {p}")
        if substring:
            self.assertIn(substring, err)

    def assert_valid(self, p: ParametrosSimulacion):
        self.assertEqual(validar_parametros_entrada(p), "")

    def test_n_cero_o_negativo(self):
        self.assert_invalid(_p(dias=0), "N debe")
        self.assert_invalid(_p(dias=-1), "N debe")

    def test_fila_i_cero_o_negativa(self):
        self.assert_invalid(_p(fila_desde=0), "fila i")
        self.assert_invalid(_p(fila_desde=-5), "fila i")

    def test_fila_i_mayor_que_n(self):
        self.assert_invalid(_p(dias=10, fila_desde=11), "no puede ser mayor que N")

    def test_rangos_uniformes_invertidos(self):
        self.assert_invalid(_p(pausa_min=8, pausa_max=5), "Pausa")
        self.assert_invalid(_p(actividad_min=10, actividad_max=5), "Actividad")

    def test_media_exponencial_no_positiva(self):
        self.assert_invalid(_p(media_demora_extra=0), "demora extra")
        self.assert_invalid(_p(media_demora_extra=-1), "demora extra")

    def test_probabilidades_fuera_de_0_1(self):
        self.assert_invalid(_p(prob_demora_extra=2.0), "Demora extra")

    def test_entrada_minima_valida(self):
        self.assert_valid(_p(dias=1, fila_desde=1))


class TestEscenarioDeterminista(unittest.TestCase):
    """
    Con solo estrategia suave, sin pausa, sin extra y uniformes degenerados (min==max),
    cada dia tiene el mismo tiempo total predecible.
    """

    def test_tiempo_total_constante_sin_aleatoriedad_efectiva(self):
        p = _p(
            dias=50,
            fila_desde=1,
            seed=999,
            prob_demora_extra=0.0,
            pausa_min=5.0,
            pausa_max=7.0,
            actividad_min=5.0,
            actividad_max=5.0,
            media_demora_extra=8.0,
            umbral_tarde=1000.0,
        )
        _iv = [0]

        def _mock_intervalo(self, a, b):
            """Por dia: 1ª llamada despertar base (10); siguentes 3 actividades (5 cada una)."""
            _iv[0] += 1
            if (_iv[0] - 1) % 4 == 0:
                return (0.5, 10.0)
            return (0.5, 5.0)

        with patch.multiple(
            "monte_carlo",
            PROB_ESTRATEGIA_SUAVE=1.0,
            PROB_ESTRATEGIA_INSISTENTE=0.0,
            PROB_ESTRATEGIA_LUZ=0.0,
            PROB_PAUSA_INTERMEDIA=0.0,
        ), patch.object(
            GeneradorAleatorio,
            "generar_uniforme_intervalo",
            _mock_intervalo,
        ):
            out = SimuladorLevantarse(p).simular()
        ind = out["indicadores"]
        esperado = 10.0 + 3 * 5.0
        self.assertAlmostEqual(ind["tiempo_promedio"], esperado, places=6)
        self.assertAlmostEqual(ind["tiempo_maximo"], esperado, places=6)
        self.assertAlmostEqual(ind["tiempo_minimo"], esperado, places=6)
        self.assertEqual(ind["cantidad_sin_pausa_y_sin_extra"], 50)
        self.assertEqual(ind["porcentaje_pausa_y_extra"], 0.0)
        self.assertEqual(ind["porcentaje_rechazo"], 0.0)

    def test_demora_extra_siempre_activa_flags(self):
        """P(extra)=1: cada dia marca hubo_extra=Si (tiempo exponencial puede ser 0 si RND~1)."""
        p = _p(
            dias=5,
            seed=1,
            prob_demora_extra=1.0,
            actividad_min=0.0,
            actividad_max=0.0,
            media_demora_extra=1.0,
        )
        with patch.multiple(
            "monte_carlo",
            PROB_ESTRATEGIA_SUAVE=1.0,
            PROB_ESTRATEGIA_INSISTENTE=0.0,
            PROB_ESTRATEGIA_LUZ=0.0,
            PROB_PAUSA_INTERMEDIA=0.0,
        ), patch.object(
            GeneradorAleatorio,
            "generar_uniforme_intervalo",
            return_value=(0.0, 0.0),
        ):
            out = SimuladorLevantarse(p).simular()
        for fila in out["filas"]:
            self.assertEqual(fila["hubo_extra"], "Si")
            self.assertGreaterEqual(fila["t_extra"], 0.0)


class TestInvariantesFilasYVentana(unittest.TestCase):
    def test_n300_i1_incluye_salto_a_fila_n(self):
        p = _p(dias=300, fila_desde=1, seed=42)
        filas = SimuladorLevantarse(p).simular()["filas"]
        dias_mostrados = [f["dia"] for f in filas]
        self.assertEqual(dias_mostrados[-1], 300)
        self.assertEqual(dias_mostrados[0], 1)
        self.assertEqual(len(filas), 201)
        self.assertNotIn(250, dias_mostrados)

    def test_n_menor_que_201_solo_rango_sin_duplicar_n(self):
        p = _p(dias=100, fila_desde=1, seed=0)
        filas = SimuladorLevantarse(p).simular()["filas"]
        self.assertEqual(len(filas), 100)
        self.assertEqual(filas[-1]["dia"], 100)

    def test_cantidad_filas_ventana_intermedia(self):
        p = _p(dias=500, fila_desde=250, seed=0)
        filas = SimuladorLevantarse(p).simular()["filas"]
        # Dias 250..449 (200 filas) + fila N=500 porque 500 > 449.
        self.assertEqual(len(filas), 201)
        self.assertEqual(filas[0]["dia"], 250)
        self.assertEqual(filas[-2]["dia"], 449)
        self.assertEqual(filas[-1]["dia"], 500)


class TestReproducibilidad(unittest.TestCase):
    def test_misma_semilla_mismos_indicadores(self):
        p = _p(dias=2000, seed=12345)
        a = SimuladorLevantarse(p).simular()["indicadores"]
        b = SimuladorLevantarse(p).simular()["indicadores"]
        self.assertEqual(a, b)

    def test_generador_reiniciado_misma_primera_muestra(self):
        """Cada `GeneradorAleatorio(seed)` fija `np.random.seed`; la 1ª U(0,1) debe repetirse tras re-instanciar."""
        x0 = GeneradorAleatorio(seed=7).generar_uniforme(0, 1)
        y0 = GeneradorAleatorio(seed=7).generar_uniforme(0, 1)
        self.assertEqual(x0, y0)


class TestGranEscalaSanity(unittest.TestCase):
    def test_n_100000_no_explota_y_claves_completas(self):
        p = _p(dias=100_000, fila_desde=1, seed=42)
        out = SimuladorLevantarse(p).simular()
        ind = out["indicadores"]
        for key in (
            "tiempo_promedio",
            "porcentaje_pausa_y_extra",
            "cantidad_sin_pausa_y_sin_extra",
            "tiempo_maximo",
            "tiempo_minimo",
            "porcentaje_rechazo",
            "porcentaje_supera_umbral",
            "promedio_demora_extra_si_ocurre",
        ):
            self.assertIn(key, ind)
        self.assertGreater(ind["tiempo_maximo"], ind["tiempo_minimo"])
        self.assertGreaterEqual(ind["tiempo_promedio"], ind["tiempo_minimo"])
        self.assertLessEqual(ind["tiempo_promedio"], ind["tiempo_maximo"])
        self.assertEqual(len(out["filas"]), 201)


class TestCoherenciaIndicadoresVsFilas(unittest.TestCase):
    """Comprueba que los acumulados de la ultima fila visible coinciden con indicadores globales."""

    def test_ultima_fila_acumulados_igual_a_indicadores(self):
        p = _p(dias=80, fila_desde=1, seed=11, umbral_tarde=40.0)
        out = SimuladorLevantarse(p).simular()
        filas = out["filas"]
        ind = out["indicadores"]
        ultima = filas[-1]
        self.assertEqual(ultima["dia"], 80)
        self.assertAlmostEqual(ultima["tiempo_promedio_acum"], ind["tiempo_promedio"], places=5)
        self.assertAlmostEqual(ultima["porc_pausa_y_extra_acum"], ind["porcentaje_pausa_y_extra"], places=5)
        self.assertEqual(ultima["cant_sin_pausa_y_sin_extra_acum"], ind["cantidad_sin_pausa_y_sin_extra"])
        self.assertAlmostEqual(ultima["tiempo_max_acum"], ind["tiempo_maximo"], places=5)
        self.assertAlmostEqual(ultima["tiempo_min_acum"], ind["tiempo_minimo"], places=5)


if __name__ == "__main__":
    unittest.main()
