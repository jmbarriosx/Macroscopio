#######################
# Agente Basico De IA #
# Herramientas        #
#######################

# Importacion para el manejo de sistema
import os
import requests

class IntermediateTools:

    def __init__(self):
        pass

    # Herramienta para consultar el tipo de cambio
    def consultar_tipo_cambio_api(self, moneda: str):
        print(f"Herramienta consultar_tipo_cambio_api llamada con moneda: {moneda}")

        if not moneda:
            return "Error: Se requiere el código de la moneda para obtener el tipo de cambio."

        # URL del servicio para obtener el tipo de cambio según la moneda:
        url = (
            f"https://open.er-api.com/v6/latest/{moneda.upper()}"
        )

        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()  # Lanza una excepción si la respuesta no es exitosa
            return response.json()  # Intentar decodificar la respuesta como JSON
        except Exception as e:
            print(f"Error al obtener_tipo_cambio_api: {moneda}. Error: {e}")
            return f"ERROR: No se pudo obtener el tipo de cambio para la moneda: {moneda}" 

    # Herramienta para consultar serie historica de un indicador economico
    def consultar_serie_historica_indicador_api(self, pais: str, indicador: str, anio_inicio: str, anio_fin: str):
        print(f"Herramienta consultar_serie_historica_indicador_api llamada: pais={pais}, indicador={indicador}, {anio_inicio}-{anio_fin}")

        if not pais or not indicador:
            return "Error: Se requiere país e indicador."

        url = f"https://api.worldbank.org/v2/country/{pais.upper()}/indicator/{indicador}?format=json&date={anio_inicio}:{anio_fin}"

        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            data = response.json()

            if not data or len(data) < 2 or not data[1]:
                return f"ERROR: No hay datos para {pais} con el indicador {indicador} en ese rango de años."

            serie = [
                {"anio": d["date"], "valor": d["value"]}
                for d in data[1] if d["value"] is not None
            ]
            return serie
        except Exception as e:
            print(f"Error al consultar_serie_historica_indicador_api: {e}")
            return f"ERROR: No se pudo obtener la serie histórica para {pais}"

    # Herramienta para consultar precio e informacion de una accion
    def consultar_precio_accion_api(self, ticker: str, rango: str = "1mo"):
        print(f"Herramienta consultar_precio_accion_api llamada: ticker={ticker}, rango={rango}")

        if not ticker:
            return "Error: Se requiere el ticker de la acción, por ejemplo NVDA."

        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker.upper()}?range={rango}&interval=1d"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

        try:
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            data = response.json()

            resultado = data["chart"]["result"][0]
            meta = resultado["meta"]
            precios_cierre = resultado["indicators"]["quote"][0]["close"]
            precios_cierre = [p for p in precios_cierre if p is not None]

            return {
                "empresa": meta.get("longName", ticker),
                "precio_actual": meta.get("regularMarketPrice"),
                "cambio_pct_dia": meta.get("regularMarketChangePercent"),
                "maximo_52_semanas": meta.get("fiftyTwoWeekHigh"),
                "minimo_52_semanas": meta.get("fiftyTwoWeekLow"),
                "precios_cierre_serie": precios_cierre
            }
        except Exception as e:
            print(f"Error al consultar_precio_accion_api: {e}")
            return f"ERROR: No se pudo obtener información para el ticker {ticker}"

    # Herramienta para calcular variacion entre periodos consecutivos de una serie
    def calcular_variacion_porcentual(self, valores: list, etiquetas: list = None, es_tasa: bool = False):
        print(f"Herramienta calcular_variacion_porcentual llamada con {len(valores) if valores else 0} valores, es_tasa={es_tasa}")

        if not valores or len(valores) < 2:
            return "Error: Se necesitan al menos 2 valores para calcular variación."

        if not etiquetas:
            etiquetas = [f"periodo_{i}" for i in range(len(valores))]

        variaciones = []
        for i in range(1, len(valores)):
            anterior = valores[i - 1]
            actual = valores[i]

            if es_tasa:
                # La serie ya es una tasa (ej. % de crecimiento del PIB, inflación).
                # No tiene sentido calcular un % de variación sobre un %.
                # En su lugar, reportamos la diferencia en puntos porcentuales.
                diferencia_pp = actual - anterior
                variaciones.append({
                    "desde": etiquetas[i - 1],
                    "hasta": etiquetas[i],
                    "variacion_puntos_porcentuales": round(diferencia_pp, 2)
                })
            else:
                # La serie es un nivel (ej. precio, PIB en dolares, poblacion).
                # Aqui si tiene sentido el % de variacion relativa.
                if anterior == 0:
                    variaciones.append({
                        "desde": etiquetas[i - 1],
                        "hasta": etiquetas[i],
                        "variacion_pct": None
                    })
                    continue

                variacion_pct = ((actual - anterior) / abs(anterior)) * 100
                variaciones.append({
                    "desde": etiquetas[i - 1],
                    "hasta": etiquetas[i],
                    "variacion_pct": round(variacion_pct, 2)
                })

        return variaciones

  
        # Herramienta para calcular estadisticas descriptivas de una serie
    def calcular_estadisticas_descriptivas(self, valores: list):
        print(f"Herramienta calcular_estadisticas_descriptivas llamada con {len(valores) if valores else 0} valores")

        if not valores or len(valores) < 2:
            return "Error: Se necesitan al menos 2 valores para calcular estadísticas."

        n = len(valores)
        media = sum(valores) / n
        varianza = sum((x - media) ** 2 for x in valores) / n
        desviacion_estandar = varianza ** 0.5

        resultado = {
            "n_observaciones": n,
            "media": round(media, 4),
            "desviacion_estandar": round(desviacion_estandar, 4),
            "minimo": round(min(valores), 4),
            "maximo": round(max(valores), 4)
        }

        # El coeficiente de variacion (CV = desviacion / media) pierde sentido cuando
        # la media esta cerca de cero: pequenios cambios en la media disparan el CV
        # a valores enormes que no reflejan la dispersion real de los datos.
        # En vez de comparar la media contra un umbral relativo (sensible a casos
        # limite), ponemos un techo directo al propio resultado del CV: si supera
        # 300%, se considera no interpretable y se omite con una nota.
        CV_LIMITE_INTERPRETABLE = 300

        if media == 0:
            resultado["coeficiente_variacion_pct"] = None
            resultado["nota_cv"] = (
                "El coeficiente de variación no se reporta porque la media es cero."
            )
        else:
            cv = (desviacion_estandar / media) * 100
            if abs(cv) > CV_LIMITE_INTERPRETABLE:
                resultado["coeficiente_variacion_pct"] = None
                resultado["nota_cv"] = (
                    f"El coeficiente de variación calculado ({round(cv, 1)}%) supera el límite "
                    f"interpretable ({CV_LIMITE_INTERPRETABLE}%), lo que indica que la media está "
                    "demasiado cerca de cero. Se recomienda interpretar solo la desviación estándar."
                )
            else:
                resultado["coeficiente_variacion_pct"] = round(cv, 2)

        return resultado