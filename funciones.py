"""
Generacion de aleatoriedad para la simulacion Montecarlo.

Ubicacion en el TP: lo usa solo `monte_carlo.py` (clase `SimuladorLevantarse`).
Aqui centralizamos:
  - RND uniforme continuo en [a, b]  -> tiempos con distribucion uniforme.
  - Muestreo exponencial negativo     -> demora extra del enunciado (media configurable).

Nota: versiones anteriores del proyecto incluian otros metodos (normales, listas);
se eliminaron porque este TP no los usa (evita ruido al defender el codigo).
"""

from typing import Tuple

import numpy as np


class GeneradorAleatorio:
    """
    Fuente unica de numeros aleatorios para reproducir corridas con la misma semilla.

    La semilla se aplica a `numpy.random` en el constructor; todas las corridas
    del simulador que compartan `seed` obtienen la misma secuencia de RND.
    """

    def __init__(self, seed=0):
        self.seed = seed
        np.random.seed(self.seed)

    def generar_uniforme(self, a, b) -> float:
        """
        Devuelve un valor ~ U(a, b) usando np.random.rand() linealmente escalado.

        Se redondea a 4 decimales para mantener tablas legibles en la interfaz.
        """
        rnd = np.random.rand()
        return round(rnd * (b - a) + a, 4)

    def generar_uniforme_intervalo(self, a: float, b: float) -> Tuple[float, float]:
        """
        Igual que `generar_uniforme(a, b)` pero devuelve tambien el U(0,1) usado en la transformada.

        Returns:
            (rnd_01_redondeado, valor_en_intervalo) con la misma regla de redondeo que `generar_uniforme`.
        """
        rnd = np.random.rand()
        valor = round(rnd * (b - a) + a, 4)
        return round(rnd, 4), valor

    def generar_exponencial_negativa(self, media) -> float:
        """
        Tiempo ~ Exp(media) por transformada inversa: X = -media * ln(1 - U), U ~ U(0,1).

        `np.random.rand()` devuelve valores en [0, 1), asi que (1 - U) > 0 y el logaritmo
        esta definido. Media = valor esperado del tiempo de demora (en minutos en este TP).
        """
        _, num = self.generar_exponencial_negativa_intervalo(media)
        return num

    def generar_exponencial_negativa_intervalo(self, media: float) -> Tuple[float, float]:
        """
        Igual que `generar_exponencial_negativa` pero devuelve el U(0,1) de la transformada inversa.

        Returns:
            (rnd_01_redondeado, tiempo) con la misma regla de redondeo que `generar_exponencial_negativa`.
        """
        rnd = np.random.rand()
        lam = 1 / media
        num = -(1.0 / lam) * np.log(1 - rnd)
        return round(rnd, 4), round(num, 4)
