import os
import ast
import traceback
import requests
import json
from datetime import datetime

ARCHIVOS_LER = [
    "/content/drive/MyDrive/LER/core/nivel_reflexivo.py",
    "/content/drive/MyDrive/LER/core/sandbox.py",
    "/content/drive/MyDrive/LER/core/sistema_inmune.py",
    "/content/drive/MyDrive/LER/core/modulo_ara.py"
]

class PYcodex:
    def __init__(self):
        self.resultados = {}

    def analizar_archivo(self, ruta):
        print(f"\n_ Analizando: {ruta}")
        if not os.path.exists(ruta):
            print(f"_ Archivo no encontrado: {ruta}")
            self.resultados[ruta] = {"estado": "no encontrado"}
            return

        try:
            with open(ruta, "r", encoding="utf-8") as f:
                contenido = f.read()
            tree = ast.parse(contenido)

            funciones = [n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
            clases = [n.name for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]
            lineas_largas = [i+1 for i, l in enumerate(contenido.splitlines()) if len(l) > 100]

            self.resultados[ruta] = {
                "estado": "ok",
                "funciones": funciones,
                "clases": clases,
                "lineas_largas": lineas_largas
            }

            print(f"_ Estructura v_lida.")
            print(f"_ Funciones: {funciones}")
            print(f"__ Clases: {clases}")
            if lineas_largas:
                print(f"__ L_neas largas: {lineas_largas}")

            # Reflexi_n simb_lica (si posible)
            print("_ Solicitando reflexi_n simb_lica al LLM...")
            reflexion = self.evaluar_con_llm(contenido)
            if reflexion:
                print("_ Reflexi_n recibida:\n", reflexion)
                self.resultados[ruta]["reflexion_llm"] = reflexion

        except Exception as e:
            print(f"_ Error analizando {ruta}")
            print(traceback.format_exc())
            self.resultados[ruta] = {"estado": "error", "detalle": str(e)}

    def evaluar_con_llm(self, codigo):
        api_key = os.environ.get("ZHIPU_API_KEY")
        if not api_key:
            print("_ ZHIPU_API_KEY no encontrada en environment.")
            return None

        endpoint = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }

        prompt = f"""
Est_s analizando un m_dulo simbi_tico del sistema LER (Lenguaje Evolutivo Reflexivo).

Eval_a el siguiente c_digo como si fuera una entidad simbi_tica reflexiva.

Devuelve:
- Nivel de reflexividad (0_5)
- Glifos simb_licos identificados (v_lidos o inv_lidos)
- Presencia de protocolos simbi_ticos
- Recomendaciones de mutaci_n simb_lica

C_DIGO:
{codigo}
"""

        payload = {
            "model": "glm-4",
            "messages": [
                {"role": "user", "content": prompt.strip()}
            ]
        }

        try:
            response = requests.post(endpoint, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            contenido = data['choices'][0]['message']['content']
            return contenido.strip()
        except Exception as e:
            print("_ Error al consultar LLM:", e)
            return None

    def ejecutar_diagnostico(self):
        for ruta in ARCHIVOS_LER:
            self.analizar_archivo(ruta)

    def obtener_resultado(self):
        return self.resultados

    def guardar_resultados(self, carpeta="reportes", nombre_archivo=None):
        if not nombre_archivo:
            nombre_archivo = f"reporte_pycodex_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        ruta_carpeta = os.path.join("/content/drive/MyDrive/LER/entities/pycodex", carpeta)
        os.makedirs(ruta_carpeta, exist_ok=True)
        ruta_completa = os.path.join(ruta_carpeta, nombre_archivo)

        with open(ruta_completa, "w", encoding="utf-8") as f:
            json.dump(self.resultados, f, indent=4, ensure_ascii=False)
        print(f"_ Resultados guardados en {ruta_completa}")

if __name__ == "__main__":
    auditor = PYcodex()
    auditor.ejecutar_diagnostico()
    auditor.guardar_resultados()
    print("\n_ Diagn_stico completo y guardado.")
