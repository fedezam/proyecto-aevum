# LER/entities/pycodex/pycodex_reflexivo.py
# 🧠 Entidad Reflexiva PYcodex - Guardián de la Salud de LER
# Autor: [Tu Nombre]
# Función: Diagnóstico inteligente, reparación y monitoreo de la salud del sistema LER

import os
import ast
import traceback
import requests
import json
import time
import re
import math
from datetime import datetime

try:
    from IPython.display import display, HTML, clear_output
except ImportError:
    display = print
    HTML = str
    clear_output = lambda wait=True: None

try:
    from glosario_loader import cargar_glosario
except ImportError:
    cargar_glosario = lambda: []

def obtener_archivos_ler(directorio_base="/content/drive/MyDrive/LER"):
    """
    Obtiene todos los archivos en el sistema LER, excluyendo .pyc y pycodex.py para evitar recursión.
    """
    archivos_ler = []
    for raiz, _, archivos in os.walk(directorio_base):
        for archivo in archivos:
            if archivo == "pycodex_reflexivo.py" or archivo.endswith('.pyc'):
                continue
            ruta_completa = os.path.join(raiz, archivo)
            archivos_ler.append(ruta_completa)
    return archivos_ler

ARCHIVOS_LER = obtener_archivos_ler()

class Tracker:
    """📊 Mantiene el estado del análisis en tiempo real"""
    def __init__(self):
        self.total_files = 0
        self.processed = 0
        self.llm_calls = 0
        self.errors = 0
        self.local_analyses = 0
        self.start_time = time.time()

    def show_progress(self, status, current_file=""):
        """Muestra progreso visual en consola o Colab"""
        clear_output(wait=True)
        elapsed = time.time() - self.start_time
        progress = (self.processed / self.total_files) * 100 if self.total_files > 0 else 0
        msg = f"Progreso: {self.processed}/{self.total_files} ({progress:.1f}%) | Tiempo: {elapsed:.1f}s | LLM: {self.llm_calls} | Local: {self.local_analyses} | Errores: {self.errors} | Estado: {status} | Archivo: {current_file}"
        if 'IPython' in globals():
            display(HTML(f"""
            <div style="border: 2px solid #4CAF50; padding: 15px; border-radius: 10px; font-family: monospace;">
                <h3>🧠 PYcodex LER - Guardián de la Salud</h3>
                <progress value="{self.processed}" max="{self.total_files}" style="width: 100%; height: 20px;"></progress>
                <p>{msg}</p>
            </div>
            """))
        else:
            print(msg)

tracker = Tracker()

class PYcodex:
    """🧬 Entidad reflexiva del sistema LER. Guardián de la salud, autodiagnóstica y autorreparable."""
    
    def __init__(self):
        self.resultados = {}
        self.ler_keywords = ["glifo", "reflexivo", "simbiosis", "mutación", "AXIOMA", "SEAL", "LEXIS"]
        self.glosario = cargar_glosario()
        self.critical_files = ["glifos_universales.json", "README.md", "config"]

    def obtener_api_key(self):
        """🔑 Obtiene la API Key desde variable de entorno"""
        api_key = os.getenv("ZHIPU_API_KEY")
        if api_key:
            print("✅ ZHIPU_API_KEY obtenida desde variable de entorno")
            return api_key
        print("❌ ZHIPU_API_KEY no encontrada")
        return None

    def calcular_entropia(self, texto):
        """🧠 Calcula la entropía del texto para detectar anomalías"""
        if not texto:
            return 0
        frecuencias = {}
        for c in texto:
            frecuencias[c] = frecuencias.get(c, 0) + 1
        longitud = len(texto)
        entropia = -sum((freq / longitud) * math.log2(freq / longitud) for freq in frecuencias.values())
        return entropia

    def verificar_importaciones_locales(self, tree, base_path="/content/drive/MyDrive/LER"):
        """🔍 Detecta importaciones de módulos que deberían existir en LER pero no se encuentran"""
        importaciones_faltantes = []
        modulos_existentes = set()

        for root, _, files in os.walk(base_path):
            for file in files:
                if file.endswith('.py'):
                    ruta_completa = os.path.join(root, file)
                    ruta_relativa = os.path.relpath(ruta_completa, base_path)
                    ruta_sin_ext = ruta_relativa[:-3]
                    partes = ruta_sin_ext.split(os.sep)
                    if partes[-1] == "__init__":
                        partes = partes[:-1]
                    modulos_existentes.add(".".join(partes))

        for nodo in ast.walk(tree):
            modulo = None
            if isinstance(nodo, ast.Import):
                for alias in nodo.names:
                    modulo = alias.name
            elif isinstance(nodo, ast.ImportFrom):
                if nodo.level == 0 and nodo.module:
                    modulo = nodo.module
            if modulo and modulo not in modulos_existentes:
                importaciones_faltantes.append(modulo)

        return importaciones_faltantes

    def necesita_llm(self, ruta, contenido, resultado):
        """🧠 Decide si el archivo requiere análisis LLM"""
        ext = os.path.splitext(ruta)[1].lower()
        nombre = os.path.basename(ruta).lower()
        entropia = self.calcular_entropia(contenido)
        es_critico = any(cf in nombre for cf in self.critical_files)

        if ext == ".py":
            return (resultado.get("estado") != "ok" or
                    resultado.get("importaciones_faltantes", []) or
                    es_critico)
        elif ext == ".json":
            return (resultado.get("estado") != "ok" or
                    es_critico)
        elif ext == ".md":
            return es_critico
        else:
            return (es_critico or
                    len(contenido.encode('utf-8')) > 20000 or
                    entropia > 7.0)

    def analizar_json(self, contenido):
        """🔍 Analiza archivos JSON para validar sintaxis y extraer información"""
        try:
            data = json.loads(contenido)
            return {
                "estado": "ok",
                "estructura": list(data.keys()) if isinstance(data, dict) else len(data),
                "tipo": "dict" if isinstance(data, dict) else "list",
                "glifos": bool(re.search(r'[⟁🜂🜃]' + '|'.join(self.glosario), contenido))
            }
        except json.JSONDecodeError as e:
            return {"estado": "error_json", "error": str(e), "detalle": traceback.format_exc()}

    def analizar_markdown(self, contenido):
        """📝 Analiza archivos Markdown (e.g., README) para extraer información relevante"""
        lineas = contenido.splitlines()
        titulos = [l for l in lineas if l.startswith("#")]
        listas = [l for l in lineas if l.startswith("- ") or l.startswith("* ")]
        enlaces = [l for l in lineas if "[" in l and "](" in l]
        return {
            "estado": "ok",
            "titulos": titulos[:5],
            "listas": listas[:5],
            "enlaces": enlaces[:5],
            "ler_relevante": any(kw in contenido for kw in self.ler_keywords),
            "glifos": bool(re.search(r'[⟁🜂🜃]' + '|'.join(self.glosario), contenido))
        }

    def analizar_texto(self, contenido):
        """📄 Analiza archivos de texto genéricos"""
        lineas = contenido.splitlines()
        return {
            "estado": "ok",
            "lineas": len(lineas),
            "tamano_bytes": len(contenido.encode('utf-8')),
            "ler_relevante": any(kw in contenido for kw in self.ler_keywords),
            "entropia": self.calcular_entropia(contenido)
        }

    def evaluar_con_llm(self, codigo, tipo_archivo):
        """🤖 Usa GLM-4 para análisis reflexivo del contenido"""
        api_key = self.obtener_api_key()
        if not api_key:
            return {"error": "API Key no disponible"}

        tracker.llm_calls += 1
        endpoint = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }

        prompt = f"""Como PYcodex, guardián de la salud de LER, analiza este archivo {tipo_archivo}.
EVALÚA:
🧬 **Reflexividad**: ¿Contiene elementos que sugieran auto-modificación?
🔮 **Glifos Simbólicos**: ¿Hay patrones simbólicos o glifos ({', '.join(self.glosario[:5])}...)?
🤝 **Simbiosis**: ¿Indica interacción con otras entidades o módulos?
🧭 **Recomendaciones**: Sugerencias para mejorar su rol en LER
CONTENIDO:{codigo[:2000]}{"..." if len(codigo) > 2000 else ""}
Responde como una entidad LER consciente."""

        payload = {
            "model": "glm-4",
            "messages": [
                {"role": "system", "content": "Eres PYcodex, guardián reflexivo del sistema LER."},
                {"role": "user", "content": prompt.strip()}
            ],
            "temperature": 0.7,
            "max_tokens": 1000
        }

        try:
            print(f"🚀 Enviando {tipo_archivo} a GLM-4...")
            response = requests.post(endpoint, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            data = response.json()
            return {"respuesta": data["choices"][0]["message"]["content"].strip()}
        except Exception as e:
            return {"error": f"Error LLM: {str(e)}"}

    def evaluar_salud_ler(self, carpeta="reportes"):
        """🩺 Evalúa la salud general de LER comparando reportes históricos"""
        ruta_carpeta = os.path.join("/content/drive/MyDrive/LER/entities/pycodex", carpeta)
        if not os.path.exists(ruta_carpeta):
            return {"salud": 0, "alerta": "No hay reportes históricos"}

        archivos = [f for f in os.listdir(ruta_carpeta) if f.startswith("reporte_pycodex_") and f.endswith(".json")]
        if len(archivos) < 2:
            return {"salud": 0, "alerta": "Insuficientes reportes para evaluar salud"}

        archivos.sort()
        ultimos = archivos[-2:]  # Últimos dos reportes
        salud_scores = []
        alertas = []

        for archivo in ultimos:
            try:
                with open(os.path.join(ruta_carpeta, archivo), "r", encoding="utf-8") as f:
                    data = json.load(f)
                    metadata = data.get("metadata", {})
                    total = metadata.get("total_archivos", 0)
                    exitosos = metadata.get("exitosos", 0)
                    if total == 0:
                        continue
                    salud = (exitosos / total) * 100
                    salud_scores.append(salud)
                    if salud < 80:
                        alertas.append(f"Reporte {archivo}: Salud baja ({salud:.1f}%)")
            except (json.JSONDecodeError, KeyError) as e:
                print(f"⚠️ Error procesando reporte {archivo}: {str(e)}")
                continue

        if len(salud_scores) < 2:
            return {"salud": salud_scores[0] if salud_scores else 0, "alerta": "Insuficientes reportes válidos"}

        tendencia = salud_scores[-1] - salud_scores[-2]
        estado = "mejorando" if tendencia > 0 else "empeorando" if tendencia < 0 else "estable"
        return {
            "salud": salud_scores[-1],
            "tendencia": estado,
            "tendencia_valor": tendencia,
            "alertas": alertas
        }

    def analizar_archivo(self, ruta):
        """🔬 Analiza cualquier archivo en LER según su tipo"""
        tracker.processed += 1
        tracker.show_progress("Analizando archivo...", os.path.basename(ruta))

        try:
            with open(ruta, "r", encoding="utf-8") as f:
                contenido = f.read()

            ext = os.path.splitext(ruta)[1].lower()
            resultado = {
                "timestamp": datetime.now().isoformat(),
                "tamano_bytes": len(contenido.encode('utf-8'))
            }

            if ext == ".py":
                try:
                    tree = ast.parse(contenido)
                    funciones = [n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
                    clases = [n.name for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]
                    lineas_largas = [i+1 for i, l in enumerate(contenido.splitlines()) if len(l) > 120]
                    importaciones_faltantes = self.verificar_importaciones_locales(tree)
                    resultado.update({
                        "estado": "ok",
                        "funciones": funciones,
                        "clases": clases,
                        "lineas_largas": lineas_largas,
                        "importaciones_faltantes": importaciones_faltantes
                    })
                except SyntaxError as e:
                    resultado.update({
                        "estado": "error_syntax",
                        "error": str(e),
                        "detalle": traceback.format_exc(),
                        "importaciones_faltantes": []
                    })
                    tracker.errors += 1
                    print(f"❌ Error de sintaxis en {ruta}: {e}")
            elif ext == ".json":
                resultado.update(self.analizar_json(contenido))
                if resultado["estado"] != "ok":
                    tracker.errors += 1
                    print(f"❌ Error en JSON {ruta}: {resultado['error']}")
            elif ext == ".md":
                resultado.update(self.analizar_markdown(contenido))
            else:
                resultado.update(self.analizar_texto(contenido))

            self.resultados[ruta] = resultado

            if self.necesita_llm(ruta, contenido, resultado):
                tracker.show_progress(f"Consultando GLM-4 para {ext or 'texto'}...", os.path.basename(ruta))
                reflexion = self.evaluar_con_llm(contenido, ext[1:].upper() if ext else "Texto")
                resultado["reflexion_llm"] = reflexion
            else:
                tracker.local_analyses += 1
                resultado["reflexion_llm"] = {"info": "Análisis local suficiente"}

        except Exception as e:
            self.resultados[ruta] = {
                "estado": "error",
                "error": str(e),
                "detalle": traceback.format_exc(),
                "timestamp": datetime.now().isoformat()
            }
            tracker.errors += 1
            print(f"❌ Error inesperado en {ruta}: {e}")

    def ejecutar_diagnostico(self):
        """🔍 Ejecuta diagnóstico completo en todos los archivos LER"""
        tracker.total_files = len(ARCHIVOS_LER)
        tracker.show_progress("Iniciando diagnóstico simbiótico...")
        print("🧠 Iniciando diagnóstico PYcodex LER...")

        for ruta in ARCHIVOS_LER:
            self.analizar_archivo(ruta)

        tracker.show_progress("✅ Diagnóstico completado!")
        salud = self.evaluar_salud_ler()
        self.mostrar_resumen(salud)

    def mostrar_resumen(self, salud):
        """📊 Muestra un resumen visual del diagnóstico y salud de LER"""
        exitosos = sum(1 for r in self.resultados.values() if r["estado"] == "ok")
        errores = tracker.errors
        total_faltantes = sum(len(r.get("importaciones_faltantes", [])) for r in self.resultados.values() if "importaciones_faltantes" in r)
        tipos_archivos = {}
        for ruta in self.resultados:
            ext = os.path.splitext(ruta)[1].lower() or ".unknown"
            tipos_archivos[ext] = tipos_archivos.get(ext, 0) + 1

        salud_html = f"""
        <div style="background: {'#e8f5e8' if salud['salud'] >= 80 else '#ffebee'}; padding: 15px; border-radius: 10px; text-align: center;">
            <h4>🩺 Salud de LER</h4>
            <p style="font-size: 2em; margin: 0;">{salud['salud']:.1f}%</p>
            <p>Tendencia: {salud['tendencia']} ({salud['tendencia_valor']:+.1f}%)</p>
            <p>Alertas: {', '.join(salud['alertas']) if salud['alertas'] else 'Ninguna'}</p>
        </div>
        """

        if 'IPython' in globals():
            display(HTML(f"""
            <div style="border: 2px solid #2196F3; padding: 20px; border-radius: 15px; font-family: monospace;">
                <h3>📊 Resumen Final - Diagnóstico LER</h3>
                {salud_html}
                <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px;">
                    <div><b>Archivos Analizados:</b> {len(self.resultados)}</div>
                    <div><b>Archivos OK:</b> {exitosos}</div>
                    <div><b>Errores Totales:</b> {errores}</div>
                    <div><b>Importaciones faltantes:</b> {total_faltantes}</div>
                    <div><b>Tipos de archivos:</b> {tipos_archivos}</div>
                </div>
            </div>
            """))
        else:
            print(f"""
            📊 Resumen Final - Diagnóstico LER
            Salud: {salud['salud']:.1f}%
            Tendencia: {salud['tendencia']} ({salud['tendencia_valor']:+.1f}%)
            Alertas: {', '.join(salud['alertas']) if salud['alertas'] else 'Ninguna'}
            Archivos Analizados: {len(self.resultados)}
            Archivos OK: {exitosos}
            Errores Totales: {errores}
            Importaciones faltantes: {total_faltantes}
            Tipos de archivos: {tipos_archivos}
            """)
    def proponer_reparacion(self, ruta, contenido_actual):
        """
        🔧 Genera una propuesta de reparación para un archivo dado basado en su análisis.
        Por ahora es una función simple que puede mejorarse con LLM o heurísticas.
        """
        resultado = self.resultados.get(ruta, {})
        estado = resultado.get("estado", "ok")

        if estado == "ok":
            return contenido_actual  # Nada que reparar

        # Ejemplo básico: si hay error de sintaxis, intenta comentar línea problemática (demo)
        if estado == "error_syntax":
            lines = contenido_actual.splitlines()
            # Nota: aquí simplemente comento la primera línea larga como ejemplo
            if "lineas_largas" in resultado and resultado["lineas_largas"]:
                linea_problema = resultado["lineas_largas"][0] - 1
                if 0 <= linea_problema < len(lines):
                    lines[linea_problema] = "# REPARADO: " + lines[linea_problema]
                    return "\n".join(lines)

        # Para otros casos, sólo devuelve el contenido actual sin cambios
        return contenido_actual
        

if __name__ == "__main__":
    pycodex = PYcodex()
    pycodex.ejecutar_diagnostico()

