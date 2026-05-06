"""
Motor de simulacion Montecarlo — caso LEVANTARSE (TP3).

Responsabilidades de este archivo (para ubicarlo en la defensa oral):
  - `ParametrosSimulacion`: todos los valores que el usuario puede cargar desde la UI.
  - `SimuladorLevantarse`: un dia = una iteracion; se calculan tiempos, RND, flags y acumuladores.
  - Salida: diccionario con `filas` (vector de estado parcial), `indicadores` (preguntas 1–6)
    y `estrategias` (tabla de probabilidad acumulada para mostrar en pantalla).

Memoria / enunciado:
  - Se simulan N dias completos, pero solo se guardan en lista las filas a mostrar:
    200 filas desde la fila i y, si no esta incluida, la fila N (total maximo: 201).
  - Los promedios y conteos del final usan los N dias completos aunque la grilla muestre un subconjunto.

Demora extra (enunciado):
  - En el PDF es la demora por imprevisto / juguete perdido: 25% de los dias, tiempo exponencial.
  - En codigo: `prob_demora_extra` + `media_demora_extra`; ver README seccion dedicada.
"""

from dataclasses import dataclass
from typing import Dict, List, Tuple

from funciones import GeneradorAleatorio


@dataclass
class ParametrosSimulacion:
    """
    Entradas del modelo. Campos agrupados por tema del enunciado:

    Simulacion general:
      dias, fila_desde (i del vector), umbral_tarde (minutos; variable extra del grupo), seed.

    Estrategia de despertar (30% / 50% / 20% por defecto):
      prob_suave, prob_insistente, prob_luz  (deben sumar 1).

    Pausa intermedia (70% por defecto; si ocurre, U entre pausa_min y pausa_max):
      prob_pausa, pausa_min, pausa_max.

    Reaccion lenta solo si la estrategia no es suave (35% por defecto; +75% al tiempo base):
      prob_rechazo, incremento_rechazo.

    Tiempos base:
      despertar: U(despertar_min, despertar_max) minutos por defecto [5,10].
      actividades (vestir / desayuno / higiene): U(actividad_min, actividad_max) por defecto [5,10].

    Demora tipo juguete perdido / imprevisto (25% por defecto; Exp(media) minutos, media 8):
      prob_demora_extra, media_demora_extra.
    """

    dias: int
    fila_desde: int
    umbral_tarde: float
    seed: int = 42

    prob_suave: float = 0.30
    prob_insistente: float = 0.50
    prob_luz: float = 0.20

    prob_pausa: float = 0.70
    pausa_min: float = 5.0
    pausa_max: float = 7.0

    prob_rechazo: float = 0.35
    incremento_rechazo: float = 0.75

    despertar_min: float = 5.0
    despertar_max: float = 10.0

    actividad_min: float = 5.0
    actividad_max: float = 10.0

    prob_demora_extra: float = 0.25
    media_demora_extra: float = 8.0


def validar_parametros_entrada(p: ParametrosSimulacion) -> str:
    """
    Valida `ParametrosSimulacion` antes de simular.

    Returns:
        Cadena vacia si todo es consistente; si no, mensaje listo para mostrar en QMessageBox.
    """
    if p.dias <= 0:
        return "N debe ser mayor a 0."
    if p.fila_desde <= 0:
        return "La fila i debe ser mayor a 0."
    if p.fila_desde > p.dias:
        return "La fila i no puede ser mayor que N."
    if abs((p.prob_suave + p.prob_insistente + p.prob_luz) - 1.0) > 1e-6:
        return "La suma de probabilidades de estrategia debe ser 1."
    if p.despertar_min > p.despertar_max:
        return "Despertar minimo no puede ser mayor al maximo."
    if p.pausa_min > p.pausa_max:
        return "Pausa minima no puede ser mayor a la maxima."
    if p.actividad_min > p.actividad_max:
        return "Actividad minima no puede ser mayor a la maxima."
    if p.media_demora_extra <= 0:
        return "La media de demora extra debe ser mayor a 0."
    for nombre, prob in (
        ("P(Pausa intermedia)", p.prob_pausa),
        ("P(Reaccion lenta en 2/3)", p.prob_rechazo),
        ("P(Demora extra)", p.prob_demora_extra),
    ):
        if not 0.0 <= prob <= 1.0:
            return f"{nombre} debe estar entre 0 y 1."
    return ""


class SimuladorLevantarse:
    """Recorre N dias, acumula estadisticas y arma el vector de estado a graficar."""

    # Enunciado acordado: 200 filas de detalle + fila N si no quedo dentro del detalle.
    FILAS_DETALLE = 200

    def __init__(self, parametros: ParametrosSimulacion):
        self.parametros = parametros
        self._generador = GeneradorAleatorio(seed=parametros.seed)
        self._estrategias = self._crear_distribucion_estrategias()

    def _crear_distribucion_estrategias(self) -> List[dict]:
        """Tabla P acumulada + rangos de RND para muestrear la estrategia del dia (metodo Montecarlo)."""
        p = self.parametros
        estrategias = [
            ("Suave", p.prob_suave),
            ("Insistente", p.prob_insistente),
            ("Luz encendida", p.prob_luz),
        ]

        acumulada = 0.0
        distribucion = []
        for nombre, prob in estrategias:
            desde = acumulada
            acumulada += prob
            distribucion.append(
                {
                    "estrategia": nombre,
                    "probabilidad": prob,
                    "acumulada": acumulada,
                    "rnd_desde": desde,
                    "rnd_hasta": acumulada,
                }
            )
        return distribucion

    def get_distribucion_estrategias(self) -> List[dict]:
        return self._estrategias

    def _muestrear_estrategia(self) -> Tuple[str, float]:
        """Un RND U(0,1) y la primera fila cuya acumulada lo cubre."""
        rnd = self._generador.generar_uniforme(0, 1)
        for fila in self._estrategias:
            if rnd <= fila["acumulada"]:
                return fila["estrategia"], rnd
        return self._estrategias[-1]["estrategia"], rnd

    def _u(self, minimo: float, maximo: float) -> float:
        return self._generador.generar_uniforme(minimo, maximo)

    def _exp(self, media: float) -> float:
        return self._generador.generar_exponencial_negativa(media)

    def simular(self) -> Dict[str, object]:
        """
        Bucle principal: por cada dia se calcula una fila del vector de estado conceptual.

        Orden logico del dia (coincide con columnas de la grilla):
          1) Estrategia y tiempo de despertar (con posible incremento por reaccion lenta).
          2) Pausa intermedia opcional.
          3) Tres actividades en U.
          4) Demora extra opcional (juguete / imprevisto) con exponencial.
          5) Tiempo total del dia y actualizacion de todos los acumuladores.
        """
        p = self.parametros
        desde = p.fila_desde
        hasta = min(p.dias, desde + self.FILAS_DETALLE - 1)

        filas_mostradas: List[dict] = []
        # --- Acumuladores globales (se usan en indicadores finales y en columnas acumuladas) ---
        tiempo_total_acum = 0.0
        cont_pausa_y_extra = 0
        cont_sin_pausa_y_sin_extra = 0
        cont_rechazo = 0
        cont_supera_umbral = 0
        cont_demora_extra = 0
        tiempo_demora_extra_acum = 0.0
        tiempo_max = float("-inf")
        tiempo_min = float("inf")

        for dia in range(1, p.dias + 1):
            # --- 1) Despertar ---
            estrategia, rnd_estrategia = self._muestrear_estrategia()

            t_despertar_base = self._u(p.despertar_min, p.despertar_max)
            rnd_rechazo = None
            hubo_rechazo = False

            if estrategia != "Suave":
                rnd_rechazo = self._u(0, 1)
                hubo_rechazo = rnd_rechazo <= p.prob_rechazo
            if hubo_rechazo:
                t_despertar = t_despertar_base * (1 + p.incremento_rechazo)
                cont_rechazo += 1
            else:
                t_despertar = t_despertar_base

            # --- 2) Pausa intermedia ---
            rnd_pausa = self._u(0, 1)
            hubo_pausa = rnd_pausa <= p.prob_pausa
            t_pausa = self._u(p.pausa_min, p.pausa_max) if hubo_pausa else 0.0

            # --- 3) Rutina: vestirse, desayunar, higiene ---
            t_vestirse = self._u(p.actividad_min, p.actividad_max)
            t_desayuno = self._u(p.actividad_min, p.actividad_max)
            t_higiene = self._u(p.actividad_min, p.actividad_max)

            # --- 4) Demora extra = imprevisto / juguete perdido (PDF: 25%, Exp(media=8)) ---
            rnd_extra = self._u(0, 1)
            hubo_extra = rnd_extra <= p.prob_demora_extra
            t_extra = self._exp(p.media_demora_extra) if hubo_extra else 0.0

            if hubo_extra:
                cont_demora_extra += 1
                tiempo_demora_extra_acum += t_extra

            # --- 5) Totales del dia y respuestas a preguntas 2 y 3 del enunciado ---
            tiempo_total = t_despertar + t_pausa + t_vestirse + t_desayuno + t_higiene + t_extra
            tiempo_total_acum += tiempo_total

            if hubo_pausa and hubo_extra:
                cont_pausa_y_extra += 1
            if not hubo_pausa and not hubo_extra:
                cont_sin_pausa_y_sin_extra += 1
            if tiempo_total > p.umbral_tarde:
                cont_supera_umbral += 1

            tiempo_max = max(tiempo_max, tiempo_total)
            tiempo_min = min(tiempo_min, tiempo_total)

            promedio_extra_acum = (
                tiempo_demora_extra_acum / cont_demora_extra if cont_demora_extra else 0.0
            )

            # Diccionario de una fila: todo lo que la catedra suele pedir ver en el vector de estado.
            fila = {
                "dia": dia,
                "rnd_estrategia": rnd_estrategia,
                "estrategia": estrategia,
                "t_despertar_base": t_despertar_base,
                "rnd_rechazo": rnd_rechazo,
                "hubo_rechazo": "Si" if hubo_rechazo else "No",
                "t_despertar": t_despertar,
                "rnd_pausa": rnd_pausa,
                "hubo_pausa": "Si" if hubo_pausa else "No",
                "t_pausa": t_pausa,
                "t_vestirse": t_vestirse,
                "t_desayuno": t_desayuno,
                "t_higiene": t_higiene,
                "rnd_extra": rnd_extra,
                "hubo_extra": "Si" if hubo_extra else "No",
                "t_extra": t_extra,
                "tiempo_total": tiempo_total,
                "tiempo_total_acum": tiempo_total_acum,
                "tiempo_promedio_acum": tiempo_total_acum / dia,
                "tiempo_max_acum": tiempo_max,
                "tiempo_min_acum": tiempo_min,
                "porc_pausa_y_extra_acum": (cont_pausa_y_extra / dia) * 100,
                "cant_sin_pausa_y_sin_extra_acum": cont_sin_pausa_y_sin_extra,
                "porc_rechazo_acum": (cont_rechazo / dia) * 100,
                "porc_supera_umbral_acum": (cont_supera_umbral / dia) * 100,
                "cant_demora_extra_acum": cont_demora_extra,
                "tiempo_demora_extra_acum": tiempo_demora_extra_acum,
                "promedio_demora_extra_acum": promedio_extra_acum,
            }

            # Guardar 200 filas desde i y, si hace falta, la ultima fila N (enunciado).
            if desde <= dia <= hasta:
                filas_mostradas.append(fila)
            elif dia == p.dias:
                if not filas_mostradas or filas_mostradas[-1]["dia"] != p.dias:
                    filas_mostradas.append(fila)

        # Indicadores pedidos (1–5) + tres variables extra del grupo (6.a–6.c).
        indicadores = {
            "tiempo_promedio": tiempo_total_acum / p.dias,
            "porcentaje_pausa_y_extra": (cont_pausa_y_extra / p.dias) * 100,
            "cantidad_sin_pausa_y_sin_extra": cont_sin_pausa_y_sin_extra,
            "tiempo_maximo": tiempo_max,
            "tiempo_minimo": tiempo_min,
            "porcentaje_rechazo": (cont_rechazo / p.dias) * 100,
            "porcentaje_supera_umbral": (cont_supera_umbral / p.dias) * 100,
            "promedio_demora_extra_si_ocurre": (
                tiempo_demora_extra_acum / cont_demora_extra if cont_demora_extra else 0.0
            ),
        }

        return {
            "filas": filas_mostradas,
            "indicadores": indicadores,
            "estrategias": self._estrategias,
        }
