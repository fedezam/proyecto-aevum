import os
import ast
import traceback
import json
import time
from datetime import datetime
from pathlib import Path

class Tracker:
    def __init__(self):
        self.total_files = 0
        self.processed = 0
        self.llm_calls = 0
        self.errors = 0
        self.start_time = time.time()

    def show_progress(self, status, current_file=""):
        """Muestra progreso sin IPython.display para mejor compatibilidad"""
        elapsed = time.time() - self.start_time
        progress = (self.processed / self.total_files) * 100 if self.total_files > 0 else 0
        
        print(f"\n{'='*60}")
        print(f"_ PYcodex LER - An_lisis Simbi_tico")
        print(f"_ Progreso: {self.processed}/{self.total_files} archivos ({progress:.1f}%)")
        print(f"__ Tiempo: {elapsed:.1f}s | _ Consultas LLM: {self.llm_calls} | _ Errores: {self.errors}")
        print(f"_ Estado: {status}")
        if current_file:
            print(f"_ Archivo actual: {current_file}")
        print(f"{'='*60}")

tracker = Tracker()

class PYcodexLite:
    """Versi_n ligera de PYcodex que funciona sin API externa"""
    
    def __init__(self, base_dir=None):
        # Detectar si estamos en Colab
        self.is_colab = 'google.colab' in str(get_ipython()) if 'get_ipython' in globals() else False
        
        if base_dir is None:
            if self.is_colab:
                self.base_dir = Path("/content/drive/MyDrive/LER")
            else:
                self.base_dir = Path.cwd()
        else:
            self.base_dir = Path(base_dir)
        
        self.resultados = {}
        self.reports_dir = self.base_dir / "entities" / "pycodex" / "reportes"
        self.reports_dir.mkdir(parents=True, exist_ok=True)

    def obtener_archivos_ler(self):
        """Obtiene todos los archivos Python del directorio base"""
        archivos_ler = []
        for archivo in self.base_dir.rglob("*.py"):
            archivos_ler.append(str(archivo))
        return archivos_ler

    def verificar_importaciones_locales(self, tree):
        """Verifica importaciones faltantes dentro del proyecto"""
        importaciones_faltantes = []
        modulos_existentes = set()
        
        # Mapear todos los m_dulos Python existentes
        for archivo in self.base_dir.rglob("*.py"):
            ruta_relativa = archivo.relative_to(self.base_dir)
            ruta_sin_ext = str(ruta_relativa.with_suffix(''))
            partes = ruta_sin_ext.split(os.sep)
            
            if partes[-1] == "__init__":
                partes = partes[:-1]
            if partes:  # Evitar m_dulos vac_os
                modulos_existentes.add(".".join(partes))

        # Analizar importaciones en el AST
        for nodo in ast.walk(tree):
            if isinstance(nodo, ast.Import):
                for alias in nodo.names:
                    modulo = alias.name
                    if modulo and not self._es_modulo_estandar(modulo):
                        if modulo not in modulos_existentes:
                            importaciones_faltantes.append(modulo)
            elif isinstance(nodo, ast.ImportFrom):
                if nodo.level == 0 and nodo.module:  # Importaci_n absoluta
                    modulo = nodo.module
                    if modulo and not self._es_modulo_estandar(modulo):
                        if modulo not in modulos_existentes:
                            importaciones_faltantes.append(modulo)

        return list(set(importaciones_faltantes))  # Eliminar duplicados

    def _es_modulo_estandar(self, modulo):
        """Verifica si es un m_dulo est_ndar de Python o popular"""
        modulos_estandar = {
            'os', 'sys', 'json', 'time', 'datetime', 'pathlib', 'ast', 'traceback',
            'requests', 'numpy', 'pandas', 'matplotlib', 'IPython', 'google',
            'collections', 're', 'math', 'random', 'itertools', 'functools'
        }
        
        primer_nivel = modulo.split('.')[0]
        return primer_nivel in modulos_estandar

    def analizar_archivo_detallado(self, ruta):
        """An_lisis detallado sin LLM pero con m_tricas avanzadas"""
        resultado = {"estado": "ok", "metricas": {}}
        
        try:
            with open(ruta, "r", encoding="utf-8") as f:
                contenido = f.read()

            # An_lisis AST
            tree = ast.parse(contenido)
            
            # M_tricas b_sicas
            funciones = [n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
            clases = [n.name for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]
            lineas = contenido.splitlines()
            
            # M_tricas avanzadas
            resultado["funciones"] = funciones
            resultado["clases"] = clases
            resultado["total_lineas"] = len(lineas)
            resultado["lineas_codigo"] = len([l for l in lineas if l.strip() and not l.strip().startswith('#')])
            resultado["lineas_comentarios"] = len([l for l in lineas if l.strip().startswith('#')])
            resultado["lineas_largas"] = [i+1 for i, linea in enumerate(lineas) if len(linea) > 120]
            
            # An_lisis de complejidad
            resultado["metricas"]["complejidad_ciclomatica"] = self._calcular_complejidad(tree)
            resultado["metricas"]["anidamiento_maximo"] = self._calcular_anidamiento(tree)
            resultado["metricas"]["docstrings"] = self._contar_docstrings(tree)
            
            # Verificaciones espec_ficas
            resultado["importaciones_faltantes"] = self.verificar_importaciones_locales(tree)
            resultado["posibles_problemas"] = self._detectar_problemas(tree, contenido)
            
            # Si hay problemas, cambiar estado
            if resultado["importaciones_faltantes"] or resultado["posibles_problemas"]:
                resultado["estado"] = "con_advertencias"
            
            resultado["timestamp"] = datetime.now().isoformat()

        except SyntaxError as e:
            resultado = {
                "estado": "error_syntax",
                "error": str(e),
                "linea": e.lineno,
                "columna": e.offset,
                "timestamp": datetime.now().isoformat()
            }
            tracker.errors += 1
        except Exception as e:
            resultado = {
                "estado": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
            tracker.errors += 1

        return resultado

    def _calcular_complejidad(self, tree):
        """Calcula complejidad ciclom_tica aproximada"""
        complejidad = 1  # Base
        for nodo in ast.walk(tree):
            if isinstance(nodo, (ast.If, ast.While, ast.For, ast.Try, ast.With)):
                complejidad += 1
            elif isinstance(nodo, ast.BoolOp):
                complejidad += len(nodo.values) - 1
        return complejidad

    def _calcular_anidamiento(self, tree):
        """Calcula nivel m_ximo de anidamiento"""
        def _profundidad(nodo, nivel=0):
            max_nivel = nivel
            for hijo in ast.iter_child_nodes(nodo):
                if isinstance(hijo, (ast.If, ast.While, ast.For, ast.Try, ast.With, ast.FunctionDef, ast.ClassDef)):
                    max_nivel = max(max_nivel, _profundidad(hijo, nivel + 1))
                else:
                    max_nivel = max(max_nivel, _profundidad(hijo, nivel))
            return max_nivel
        return _profundidad(tree)

    def _contar_docstrings(self, tree):
        """Cuenta funciones y clases con docstrings"""
        total = 0
        con_doc = 0
        
        for nodo in ast.walk(tree):
            if isinstance(nodo, (ast.FunctionDef, ast.ClassDef)):
                total += 1
                if (nodo.body and isinstance(nodo.body[0], ast.Expr) and 
                    isinstance(nodo.body[0].value, ast.Str)):
                    con_doc += 1
        
        return {"total": total, "con_docstring": con_doc, "porcentaje": (con_doc/total)*100 if total > 0 else 0}

    def _detectar_problemas(self, tree, contenido):
        """Detecta problemas potenciales en el c_digo"""
        problemas = []
        
        # Funciones muy largas
        for nodo in ast.walk(tree):
            if isinstance(nodo, ast.FunctionDef):
                if hasattr(nodo, 'end_lineno') and nodo.end_lineno:
                    longitud = nodo.end_lineno - nodo.lineno
                    if longitud > 50:
                        problemas.append(f"Funci_n '{nodo.name}' muy larga ({longitud} l_neas)")
        
        # Imports al estilo 'import *'
        for nodo in ast.walk(tree):
            if isinstance(nodo, ast.ImportFrom):
                for alias in nodo.names:
                    if alias.name == '*':
                        problemas.append("Import con '*' detectado - no recomendado")
        
        # Variables no utilizadas (b_sico)
        lineas = contenido.splitlines()
        for i, linea in enumerate(lineas, 1):
            if 'TODO' in linea or 'FIXME' in linea or 'XXX' in linea:
                problemas.append(f"Comentario pendiente en l_nea {i}: {linea.strip()}")
        
        return problemas

    def analizar_archivo(self, ruta):
        """Interfaz compatible con el c_digo original"""
        tracker.processed += 1
        tracker.show_progress(f"Analizando archivo...", os.path.basename(ruta))
        print(f"_ Analizando: {ruta}")
        
        if not os.path.exists(ruta):
            print(f"_ Archivo no encontrado: {ruta}")
            self.resultados[ruta] = {"estado": "no encontrado"}
            tracker.errors += 1
            return

        resultado = self.analizar_archivo_detallado(ruta)
        self.resultados[ruta] = resultado
        
        # Mostrar resumen del archivo
        if resultado["estado"] == "ok":
            print(f"_ An_lisis exitoso: {len(resultado.get('funciones', []))} funciones, {len(resultado.get('clases', []))} clases")
        elif resultado["estado"] == "con_advertencias":
            print(f"__ Con advertencias: {len(resultado.get('importaciones_faltantes', []))} imports faltantes")
        else:
            print(f"_ Error: {resultado.get('error', 'Desconocido')}")

    def ejecutar_diagnostico(self):
        """Ejecuta el an_lisis en todos los archivos LER"""
        archivos_ler = self.obtener_archivos_ler()
        tracker.total_files = len(archivos_ler)
        tracker.show_progress("Iniciando diagn_stico simbi_tico LER...")
        print(f"_ Iniciando diagn_stico PYcodex LER Lite...")
        print(f"_ {tracker.total_files} archivos a analizar")
        
        for ruta in archivos_ler:
            self.analizar_archivo(ruta)

        # Mostrar resumen final
        tracker.show_progress("_ Diagn_stico completado exitosamente!")
        self.mostrar_resumen()

    def mostrar_resumen(self):
        """Muestra resumen del an_lisis"""
        exitosos = sum(1 for r in self.resultados.values() if r.get("estado") == "ok")
        con_advertencias = sum(1 for r in self.resultados.values() if r.get("estado") == "con_advertencias")
        errores = sum(1 for r in self.resultados.values() if r.get("estado") in ["error", "error_syntax"])
        
        total_importaciones_faltantes = sum(len(r.get("importaciones_faltantes", [])) for r in self.resultados.values())
        total_problemas = sum(len(r.get("posibles_problemas", [])) for r in self.resultados.values())
        
        print(f"\n{'='*60}")
        print(f"_ RESUMEN FINAL - Diagn_stico LER")
        print(f"{'='*60}")
        print(f"_ Archivos analizados: {len(self.resultados)}")
        print(f"_ Sin problemas: {exitosos}")
        print(f"__ Con advertencias: {con_advertencias}")
        print(f"_ Con errores: {errores}")
        print(f"_ Importaciones faltantes: {total_importaciones_faltantes}")
        print(f"_ Problemas detectados: {total_problemas}")
        print(f"__ Tiempo total: {time.time() - tracker.start_time:.1f} segundos")
        print(f"{'='*60}")

    def guardar_resultados(self, nombre_archivo=None):
        """Guarda resultados en JSON"""
        if not nombre_archivo:
            nombre_archivo = f"reporte_pycodex_lite_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        ruta_completa = self.reports_dir / nombre_archivo
        
        # Agregar metadata del an_lisis
        reporte_completo = {
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "total_archivos": len(self.resultados),
                "version": "PYcodex Lite",
                "base_dir": str(self.base_dir),
                "duracion_segundos": time.time() - tracker.start_time
            },
            "resultados": self.resultados
        }

        with open(ruta_completa, "w", encoding="utf-8") as f:
            json.dump(reporte_completo, f, indent=2, ensure_ascii=False)
        
        print(f"_ Resultados guardados en: {ruta_completa}")
        return str(ruta_completa)

    def mostrar_archivos_con_problemas(self):
        """Muestra archivos que necesitan atenci_n"""
        archivos_problematicos = []
        
        for archivo, resultado in self.resultados.items():
            tiene_problemas = (
                resultado.get("estado") != "ok" or 
                resultado.get("importaciones_faltantes") or
                resultado.get("posibles_problemas")
            )
            
            if tiene_problemas:
                archivos_problematicos.append({
                    "archivo": archivo,
                    "estado": resultado.get("estado", "desconocido"),
                    "importaciones_faltantes": len(resultado.get("importaciones_faltantes", [])),
                    "problemas": len(resultado.get("posibles_problemas", []))
                })
        
        if not archivos_problematicos:
            print("_ _No hay archivos con problemas detectados!")
            return []
        
        print(f"\n_ ARCHIVOS QUE NECESITAN ATENCI_N ({len(archivos_problematicos)}):")
        print("=" * 60)
        for i, info in enumerate(archivos_problematicos, 1):
            archivo = Path(info["archivo"]).name
            print(f"{i:2d}. {archivo}")
            print(f"    Estado: {info['estado']}")
            print(f"    Importaciones faltantes: {info['importaciones_faltantes']}")
            print(f"    Otros problemas: {info['problemas']}")
            print()
        
        return archivos_problematicos

# Funciones de conveniencia
def diagnostico_completo_lite(base_dir=None):
    """Ejecuta diagn_stico completo sin dependencias externas"""
    print("_ Ejecutando diagn_stico PYcodex Lite...")
    auditor = PYcodexLite(base_dir)
    auditor.ejecutar_diagnostico()
    ruta_reporte = auditor.guardar_resultados()
    
    print(f"\n_ Diagn_stico completado")
    auditor.mostrar_archivos_con_problemas()
    
    return auditor

def analizar_archivo_especifico(ruta_archivo):
    """Analiza un archivo espec_fico"""
    auditor = PYcodexLite()
    auditor.analizar_archivo(ruta_archivo)
    return auditor.resultados.get(ruta_archivo, {})

# Uso principal
if __name__ == "__main__":
    print("_ PYcodex Lite - An_lisis sin API externa")
    print("=" * 50)
    auditor = diagnostico_completo_lite()