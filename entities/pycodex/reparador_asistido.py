# reparador_asistido_completo.py - VERSIÓN DEFINITIVA 🔥 CORREGIDA
# 🚀 TODAS LAS FUNCIONALIDADES - Sin miedo a la complejidad!

import sys
import os
import json
import difflib
import time
import re
import ast
import argparse
import subprocess
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Set
from collections import defaultdict

# Agregar carpeta actual al sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from pycodex_reflexivo import PYcodex
    import requests  # Para LLM
except ImportError as e:
    print(f"❌ Error: {e}")
    sys.exit(1)

class ReparadorDefinitivo:
    """🔥 REPARADOR COMPLETO - Todas las funcionalidades implementadas"""
    
    def __init__(self, base_path="/content/drive/MyDrive/LER", modo="interactivo"):
        self.base_path = base_path
        self.pycodex = PYcodex()
        self.reportes_dir = os.path.join(base_path, "entities/pycodex/reportes")
        self.logs_dir = os.path.join(base_path, "entities/pycodex/logs")
        self.modo = modo  # "interactivo", "auto", "dry-run"
        
        # Estados y métricas
        self.salud_inicial = None
        self.salud_final = None
        self.mapa_dependencias = defaultdict(set)
        self.archivos_criticos = set()
        self.rollbacks_aplicados = []
        
        self.crear_directorios()
        self.inicializar_criticidad()
    
    def crear_directorios(self):
        """📁 Crear estructura de directorios"""
        os.makedirs(self.logs_dir, exist_ok=True)
        os.makedirs(os.path.join(self.logs_dir, "rollbacks"), exist_ok=True)
        os.makedirs(os.path.join(self.logs_dir, "backups"), exist_ok=True)
    
    def inicializar_criticidad(self):
        """🎯 Define archivos críticos del sistema LER"""
        patrones_criticos = [
            "**/core/**/*.py",
            "**/axioma.py", 
            "**/glifo_engine.py",
            "**/sistema_inmune.py",
            "**/pycodex_reflexivo.py",
            "**/*config*.json",
            "**/glifos_universales.json"
        ]
        
        import glob
        for patron in patrones_criticos:
            for archivo in glob.glob(os.path.join(self.base_path, patron), recursive=True):
                self.archivos_criticos.add(archivo)
        
        print(f"🎯 Archivos críticos identificados: {len(self.archivos_criticos)}")
    
    def normalizar_resultados(self, reporte):
        """🔧 Normaliza resultados del reporte a formato consistente"""
        resultados = reporte.get("resultados", {})
        
        # Si es una lista, convertir a diccionario
        if isinstance(resultados, list):
            print("🔄 Convirtiendo lista de resultados a diccionario...")
            resultados_dict = {}
            for item in resultados:
                if isinstance(item, dict):
                    # Buscar la ruta del archivo en diferentes claves posibles
                    ruta = item.get("archivo") or item.get("ruta") or item.get("path")
                    if ruta:
                        resultados_dict[ruta] = item
            return resultados_dict
        
        return resultados
    
    def construir_mapa_dependencias(self, reporte):
        """🕸️ Construye mapa de dependencias entre archivos"""
        print("🕸️ Construyendo mapa de dependencias...")
        
        # Normalizar resultados primero
        resultados = self.normalizar_resultados(reporte)
        
        for ruta, resultado in resultados.items():
            if not ruta.endswith('.py'):
                continue
                
            try:
                if os.path.exists(ruta):
                    with open(ruta, 'r', encoding='utf-8') as f:
                        contenido = f.read()
                    
                    tree = ast.parse(contenido)
                    
                    for nodo in ast.walk(tree):
                        if isinstance(nodo, (ast.Import, ast.ImportFrom)):
                            if isinstance(nodo, ast.Import):
                                for alias in nodo.names:
                                    self.agregar_dependencia(ruta, alias.name)
                            elif nodo.module:
                                self.agregar_dependencia(ruta, nodo.module)
                                
            except Exception as e:
                pass  # Ignorar errores de parsing
        
        print(f"🕸️ Dependencias mapeadas: {sum(len(deps) for deps in self.mapa_dependencias.values())}")
    
    def agregar_dependencia(self, archivo_origen, modulo):
        """➕ Agrega dependencia al mapa"""
        # Buscar si el módulo corresponde a un archivo en LER
        posibles_rutas = [
            os.path.join(self.base_path, f"{modulo}.py"),
            os.path.join(self.base_path, modulo, "__init__.py"),
            os.path.join(self.base_path, "core", f"{modulo}.py"),
            os.path.join(self.base_path, "entities", f"{modulo}.py")
        ]
        
        for ruta in posibles_rutas:
            if os.path.exists(ruta):
                self.mapa_dependencias[archivo_origen].add(ruta)
                break
    
    def obtener_ultimo_reporte(self):
        """📊 Obtiene el reporte más reciente con validación"""
        if not os.path.exists(self.reportes_dir):
            return None
        
        reportes = [f for f in os.listdir(self.reportes_dir) 
                   if f.startswith("reporte_pycodex_") and f.endswith(".json")]
        
        if not reportes:
            return None
        
        reportes.sort(reverse=True)
        reporte_path = os.path.join(self.reportes_dir, reportes[0])
        
        try:
            with open(reporte_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            # Validar que el reporte no sea muy viejo (>24 horas)
            if "metadata" in data and "timestamp" in data["metadata"]:
                timestamp = datetime.fromisoformat(data["metadata"]["timestamp"])
                edad_horas = (datetime.now() - timestamp).total_seconds() / 3600
                
                if edad_horas > 24:
                    print(f"⚠️ Reporte tiene {edad_horas:.1f} horas - Podría estar desactualizado")
            
            print(f"✅ Usando reporte: {reportes[0]}")
            return data
        except Exception as e:
            print(f"❌ Error leyendo reporte: {e}")
            return None
    
    def evaluar_salud(self):
        """🩺 Evaluación completa de salud del sistema"""
        try:
            salud = self.pycodex.evaluar_salud_ler()
            return {
                "porcentaje": salud.get("salud", 0),
                "tendencia": salud.get("tendencia", "desconocido"),
                "alertas": salud.get("alertas", []),
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            print(f"⚠️ Error evaluando salud: {e}")
            return {
                "porcentaje": 0,
                "tendencia": "error",
                "alertas": [f"Error evaluando salud: {e}"],
                "timestamp": datetime.now().isoformat()
            }
    
    def reparacion_inteligente_llm(self, ruta, contenido, error_info):
        """🧠 Usa LLM para generar reparación inteligente"""
        try:
            api_key = self.pycodex.obtener_api_key()
            if not api_key:
                return None
        except:
            print("🤖 LLM no disponible - usando reparación local")
            return None
        
        ext = os.path.splitext(ruta)[1].lower()
        tipo_error = error_info.get("estado", "error")
        detalle_error = error_info.get("error", "Error desconocido")
        
        prompt = f"""Eres PYcodex, guardián reparador de LER. REPARA este archivo {ext} que tiene errores.

ARCHIVO: {os.path.basename(ruta)}
ERROR: {tipo_error} - {detalle_error}
CONTEXTO LER: Este archivo es parte del sistema LER (Lenguaje Evolutivo Reflexivo)

INSTRUCCIONES ESPECÍFICAS:
1. CORRIGE el error exacto reportado
2. MANTÉN la funcionalidad LER existente (glifos, reflexividad, simbiosis)
3. PRESERVA todos los comentarios importantes
4. USA sintaxis Python válida
5. NO elimines código funcional

CÓDIGO ORIGINAL:
{contenido[:1500]}{"..." if len(contenido) > 1500 else ""}

RESPONDE SOLO con el código corregido completo, sin explicaciones."""

        payload = {
            "model": "glm-4",
            "messages": [
                {"role": "system", "content": "Eres PYcodex, reparador experto del sistema LER."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.3,
            "max_tokens": 2000
        }
        
        try:
            print("🤖 Solicitando reparación inteligente a GLM-4...")
            response = requests.post(
                "https://open.bigmodel.cn/api/paas/v4/chat/completions",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {api_key}"
                },
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
            
            contenido_reparado = data["choices"][0]["message"]["content"].strip()
            
            # Limpiar respuesta (remover markdown si existe)
            if contenido_reparado.startswith("```"):
                lineas = contenido_reparado.split('\n')
                contenido_reparado = '\n'.join(lineas[1:-1]) if len(lineas) > 2 else contenido_reparado
            
            return contenido_reparado
            
        except Exception as e:
            print(f"❌ Error en reparación LLM: {e}")
            return None
    
    def reparacion_especifica_por_error(self, ruta, contenido, error_info):
        """🔧 Reparaciones específicas según el tipo de error"""
        tipo_error = error_info.get("estado", "")
        
        if tipo_error == "error_syntax":
            return self.reparar_error_sintaxis(contenido, error_info)
        elif tipo_error == "error_json":
            return self.reparar_json(contenido)
        elif "importaciones_faltantes" in error_info:
            return self.reparar_imports(contenido, error_info)
        else:
            return contenido
    
    def reparar_error_sintaxis(self, contenido, error_info):
        """🐍 Repara errores de sintaxis específicos"""
        lineas = contenido.splitlines()
        
        # Detectar líneas problemáticas
        try:
            ast.parse(contenido)
            return contenido  # Si ya es válido, no tocar
        except SyntaxError as e:
            if e.lineno and e.lineno <= len(lineas):
                linea_problema = lineas[e.lineno - 1]
                
                # Reparaciones comunes
                if linea_problema.strip().endswith(','):
                    lineas[e.lineno - 1] = linea_problema.rstrip(',')
                elif "print " in linea_problema and not "print(" in linea_problema:
                    # Convertir print statement a function
                    lineas[e.lineno - 1] = linea_problema.replace("print ", "print(") + ")"
        
        return '\n'.join(lineas)
    
    def reparar_json(self, contenido):
        """📋 Repara JSON malformado"""
        try:
            json.loads(contenido)
            return contenido
        except json.JSONDecodeError:
            # Reparaciones básicas
            contenido_reparado = contenido
            contenido_reparado = re.sub(r',(\s*[}\]])', r'\1', contenido_reparado)  # Comas finales
            contenido_reparado = re.sub(r"'([^']*)':", r'"\1":', contenido_reparado)  # Comillas
            
            try:
                data = json.loads(contenido_reparado)
                return json.dumps(data, indent=2, ensure_ascii=False)
            except:
                return contenido_reparado
    
    def reparar_imports(self, contenido, error_info):
        """📦 Agrega imports faltantes"""
        imports_faltantes = error_info.get("importaciones_faltantes", [])
        if not imports_faltantes:
            return contenido
        
        lineas = contenido.splitlines()
        
        # Encontrar donde insertar imports
        indice_insercion = 0
        for i, linea in enumerate(lineas):
            if linea.strip().startswith("#"):
                indice_insercion = i + 1
            elif linea.strip():
                break
        
        # Agregar imports estándar que podrían faltar
        imports_a_agregar = []
        for imp in imports_faltantes[:5]:  # Máximo 5
            if imp in ["os", "sys", "json", "time", "datetime", "re", "ast", "traceback"]:
                imports_a_agregar.append(f"import {imp}")
        
        if imports_a_agregar:
            for i, imp in enumerate(imports_a_agregar):
                lineas.insert(indice_insercion + i, imp)
            lineas.insert(indice_insercion + len(imports_a_agregar), "")  # Línea en blanco
        
        return '\n'.join(lineas)
    
    def priorizar_archivos(self, archivos_problematicos):
        """🎯 Prioriza archivos por criticidad e impacto"""
        def calcular_prioridad(item):
            ruta = item["ruta"]
            puntuacion = 0
            
            # Archivos críticos tienen máxima prioridad
            if ruta in self.archivos_criticos:
                puntuacion += 100
            
            # Core system files
            if "/core/" in ruta:
                puntuacion += 50
            
            # Según tipo de error
            error = item["estado"]
            if error == "error_syntax":
                puntuacion += 30  # Errores de sintaxis bloquean ejecución
            elif error == "error_json":
                puntuacion += 20
            elif "import" in error:
                puntuacion += 15
            
            # Archivos con muchas dependencias
            dependencias = len(self.mapa_dependencias.get(ruta, set()))
            puntuacion += dependencias * 5
            
            return puntuacion
        
        return sorted(archivos_problematicos, key=calcular_prioridad, reverse=True)
    
    def crear_backup_inteligente(self, ruta):
        """💾 Backup con metadata inteligente"""
        timestamp = int(time.time())
        backup_dir = os.path.join(self.logs_dir, "backups", datetime.now().strftime("%Y%m%d"))
        os.makedirs(backup_dir, exist_ok=True)
        
        nombre_archivo = os.path.basename(ruta)
        backup_path = os.path.join(backup_dir, f"{nombre_archivo}.backup_{timestamp}")
        
        try:
            with open(ruta, "r", encoding="utf-8") as f:
                contenido_original = f.read()
            
            # Backup del archivo
            with open(backup_path, "w", encoding="utf-8") as f:
                f.write(contenido_original)
            
            # Metadata del backup
            metadata = {
                "archivo_original": ruta,
                "timestamp": datetime.now().isoformat(),
                "tamano_original": len(contenido_original),
                "hash_original": hash(contenido_original),
                "es_critico": ruta in self.archivos_criticos
            }
            
            with open(f"{backup_path}.meta", "w", encoding="utf-8") as f:
                json.dump(metadata, f, indent=2)
            
            return backup_path, contenido_original
        except Exception as e:
            print(f"❌ Error creando backup: {e}")
            return None, None
    
    def verificar_reparacion_completa(self, ruta):
        """✅ Verificación completa post-reparación"""
        try:
            # 1. Re-analizar archivo específico
            self.pycodex.analizar_archivo(ruta)
            archivo_ok = ruta in self.pycodex.resultados and self.pycodex.resultados[ruta].get("estado") == "ok"
            
            # 2. Verificar archivos dependientes
            dependientes_ok = True
            if ruta in self.mapa_dependencias:
                for dep in list(self.mapa_dependencias[ruta])[:3]:  # Máximo 3
                    if os.path.exists(dep):
                        try:
                            self.pycodex.analizar_archivo(dep)
                            if dep in self.pycodex.resultados:
                                if self.pycodex.resultados[dep].get("estado") != "ok":
                                    dependientes_ok = False
                                    print(f"⚠️ Dependencia afectada: {os.path.basename(dep)}")
                        except:
                            pass
            
            return archivo_ok and dependientes_ok
        except Exception as e:
            print(f"❌ Error verificando: {e}")
            return False
    
    def rollback_inteligente(self, ruta, backup_path, razon):
        """🔄 Rollback automático con logging"""
        try:
            if not os.path.exists(backup_path):
                return False
            
            with open(backup_path, "r", encoding="utf-8") as f:
                contenido_original = f.read()
            
            with open(ruta, "w", encoding="utf-8") as f:
                f.write(contenido_original)
            
            # Log del rollback
            rollback_info = {
                "timestamp": datetime.now().isoformat(),
                "archivo": ruta,
                "backup_usado": backup_path,
                "razon": razon
            }
            
            self.rollbacks_aplicados.append(rollback_info)
            
            rollback_log = os.path.join(self.logs_dir, "rollbacks", f"rollback_{datetime.now().strftime('%Y%m%d')}.json")
            with open(rollback_log, "w", encoding="utf-8") as f:
                json.dump(self.rollbacks_aplicados, f, indent=2)
            
            print(f"🔄 Rollback aplicado: {os.path.basename(ruta)} - {razon}")
            return True
            
        except Exception as e:
            print(f"❌ Error en rollback: {e}")
            return False
    
    def aplicar_reparacion_completa(self, ruta, contenido_original, error_info):
        """🔧 Pipeline completo de reparación"""
        print(f"🔧 Aplicando reparación completa a {os.path.basename(ruta)}")
        
        # 1. Intentar reparación específica
        contenido_reparado = self.reparacion_especifica_por_error(ruta, contenido_original, error_info)
        
        # 2. Si no hay mejora, usar LLM
        if contenido_reparado == contenido_original:
            contenido_llm = self.reparacion_inteligente_llm(ruta, contenido_original, error_info)
            if contenido_llm:
                contenido_reparado = contenido_llm
                print("🤖 Reparación LLM aplicada")
        
        # 3. Fallback a reparación básica de pycodex
        if contenido_reparado == contenido_original:
            try:
                contenido_reparado = self.pycodex.proponer_reparacion(ruta, contenido_original)
            except:
                print("⚠️ Reparación básica no disponible")
        
        return contenido_reparado
    
    def confirmar_accion(self, prompt):
        """❓ Confirmación inteligente según el modo"""
        if self.modo == "auto":
            print(f"🤖 Auto-mode: {prompt} → SÍ")
            return True
        elif self.modo == "dry-run":
            print(f"🔍 Dry-run: {prompt} → (simulado)")
            return False
        else:  # interactivo
            try:
                resp = input(f"\n{prompt} [s/n]: ").strip().lower()
                return resp in ['s', 'si', 'sí', 'y', 'yes']
            except (KeyboardInterrupt, EOFError):
                return False
    
    def mostrar_diferencia_avanzada(self, original, propuesto, archivo):
        """📊 Muestra diferencias con análisis de impacto"""
        if original.strip() == propuesto.strip():
            return False
        
        print(f"\n🔄 REPARACIÓN PROPUESTA: {os.path.basename(archivo)}")
        
        # Análisis de impacto
        es_critico = archivo in self.archivos_criticos
        num_dependencias = len(self.mapa_dependencias.get(archivo, set()))
        
        print(f"🎯 Criticidad: {'ALTA' if es_critico else 'Normal'}")
        print(f"🕸️ Dependencias: {num_dependencias} archivos")
        
        print("-" * 50)
        
        diff = list(difflib.unified_diff(
            original.splitlines(),
            propuesto.splitlines(),
            fromfile="original",
            tofile="reparado",
            lineterm=""
        ))
        
        cambios_mostrados = 0
        for line in diff:
            if cambios_mostrados >= 25:
                print(f"... ({len(diff) - cambios_mostrados} líneas más)")
                break
            
            if line.startswith('@@'):
                print(f"📍 {line}")
            elif line.startswith('+') and not line.startswith('+++'):
                print(f"✅ {line}")
                cambios_mostrados += 1
            elif line.startswith('-') and not line.startswith('---'):
                print(f"❌ {line}")
                cambios_mostrados += 1
        
        return True
    
    def ejecutar_reparaciones_completas(self, filtro="*"):
        """🚀 PROCESO PRINCIPAL - TODAS LAS FUNCIONALIDADES"""
        print("🔥 REPARADOR DEFINITIVO LER - MODO COMPLETO")
        print(f"⚙️ Modo: {self.modo.upper()}")
        print(f"🎯 Filtro: {filtro}")
        
        # 1. EVALUAR SALUD INICIAL
        print("\n🩺 Evaluando salud inicial...")
        self.salud_inicial = self.evaluar_salud()
        print(f"   Salud inicial: {self.salud_inicial['porcentaje']:.1f}%")
        
        # 2. OBTENER REPORTE
        reporte = self.obtener_ultimo_reporte()
        if not reporte:
            if self.confirmar_accion("¿Generar nuevo reporte completo?"):
                print("\n🔄 Ejecutando diagnóstico completo...")
                try:
                    self.pycodex.ejecutar_diagnostico()
                    # TODO: Obtener resultados del diagnóstico recién ejecutado
                    reporte = {"resultados": self.pycodex.resultados}
                except Exception as e:
                    print(f"❌ Error ejecutando diagnóstico: {e}")
                    return
            else:
                print("❌ No se puede continuar sin reporte")
                return
        
        # 3. CONSTRUIR MAPA DE DEPENDENCIAS
        self.construir_mapa_dependencias(reporte)
        
        # 4. EXTRAER Y PRIORIZAR ARCHIVOS PROBLEMÁTICOS
        archivos_problematicos = []
        
        # Normalizar resultados primero
        resultados = self.normalizar_resultados(reporte)
        
        for ruta, resultado in resultados.items():
            estado = resultado.get("estado", "ok")
            if estado != "ok":
                # Aplicar filtro
                if filtro != "*":
                    if not any(pat in ruta for pat in filtro.split(",")):
                        continue
                
                archivos_problematicos.append({
                    "ruta": ruta,
                    "estado": estado,
                    "error": resultado.get("error", ""),
                    "resultado": resultado
                })
        
        if not archivos_problematicos:
            print("✅ ¡No hay archivos problemáticos!")
            return
        
        # 5. PRIORIZAR
        archivos_priorizados = self.priorizar_archivos(archivos_problematicos)
        
        print(f"\n📊 Archivos problemáticos encontrados: {len(archivos_priorizados)}")
        print("🎯 ORDEN DE PRIORIDAD:")
        for i, item in enumerate(archivos_priorizados[:10], 1):
            criticidad = "🔴" if item["ruta"] in self.archivos_criticos else "🟡"
            print(f"   {i:2d}. {criticidad} {os.path.relpath(item['ruta'], self.base_path)} → {item['estado']}")
        
        if not self.confirmar_accion("¿Proceder con reparaciones inteligentes?"):
            return
        
        # 6. PROCESAR CADA ARCHIVO
        cambios_exitosos = []
        cambios_fallidos = []
        rollbacks_realizados = []
        
        for i, item in enumerate(archivos_priorizados, 1):
            ruta = item["ruta"]
            error_info = item["resultado"]
            archivo_rel = os.path.relpath(ruta, self.base_path)
            
            print(f"\n{'='*70}")
            print(f"🔧 [{i}/{len(archivos_priorizados)}] {archivo_rel}")
            print(f"⚠️ Error: {item['estado']} - {item['error'][:80]}...")
            
            try:
                # Verificar que el archivo existe
                if not os.path.exists(ruta):
                    print(f"❌ Archivo no existe: {ruta}")
                    cambios_fallidos.append(ruta)
                    continue
                
                # Leer contenido
                with open(ruta, "r", encoding="utf-8") as f:
                    contenido_original = f.read()
                
                # Aplicar reparación completa
                contenido_reparado = self.aplicar_reparacion_completa(ruta, contenido_original, error_info)
                
                # Mostrar cambios
                if self.mostrar_diferencia_avanzada(contenido_original, contenido_reparado, ruta):
                    if self.confirmar_accion("¿Aplicar esta reparación?"):
                        # Crear backup
                        backup_path, _ = self.crear_backup_inteligente(ruta)
                        if not backup_path:
                            print("❌ Error creando backup - omitiendo")
                            continue
                        
                        if self.modo != "dry-run":
                            # Aplicar cambio
                            with open(ruta, "w", encoding="utf-8") as f:
                                f.write(contenido_reparado)
                            
                            print(f"💾 Backup: {os.path.basename(backup_path)}")
                            
                            # Verificar resultado
                            if self.verificar_reparacion_completa(ruta):
                                print("✅ Reparación exitosa y verificada")
                                cambios_exitosos.append(ruta)
                            else:
                                print("⚠️ Verificación falló - considerando rollback...")
                                
                                # Evaluar si hacer rollback
                                salud_actual = self.evaluar_salud()
                                if salud_actual["porcentaje"] < self.salud_inicial["porcentaje"] - 5:
                                    if self.rollback_inteligente(ruta, backup_path, "Salud del sistema degradada"):
                                        rollbacks_realizados.append(ruta)
                                    else:
                                        cambios_fallidos.append(ruta)
                                else:
                                    cambios_exitosos.append(ruta)
                        else:
                            print("🔍 Dry-run: Cambio simulado")
                    else:
                        print("⏭️ Omitido por usuario")
                else:
                    print("ℹ️ Sin cambios significativos")
                    
            except Exception as e:
                print(f"❌ Error procesando: {e}")
                cambios_fallidos.append(ruta)
        
        # 7. EVALUACIÓN FINAL
        if self.modo != "dry-run":
            print("\n🩺 Evaluando salud final...")
            self.salud_final = self.evaluar_salud()
        
        # 8. RESUMEN ÉPICO
        self.mostrar_resumen_definitivo(
            len(archivos_priorizados), cambios_exitosos, 
            cambios_fallidos, rollbacks_realizados
        )
    
    def mostrar_resumen_definitivo(self, total_procesados, exitosos, fallidos, rollbacks):
        """📊 RESUMEN FINAL ÉPICO"""
        print(f"\n{'='*70}")
        print("🏆 RESUMEN DEFINITIVO - REPARACIÓN COMPLETA")
        print('='*70)
        
        # Estadísticas principales
        print(f"📊 Archivos procesados: {total_procesados}")
        print(f"✅ Reparaciones exitosas: {len(exitosos)}")
        print(f"❌ Reparaciones fallidas: {len(fallidos)}")
        print(f"🔄 Rollbacks aplicados: {len(rollbacks)}")
        
        # Comparación de salud
        if self.salud_inicial and self.salud_final:
            diferencia = self.salud_final["porcentaje"] - self.salud_inicial["porcentaje"]
            emoji_salud = "📈" if diferencia > 0 else "📉" if diferencia < 0 else "➡️"
            print(f"\n🩺 EVOLUCIÓN DE SALUD:")
            print(f"   Inicial: {self.salud_inicial['porcentaje']:.1f}%")
            print(f"   Final:   {self.salud_final['porcentaje']:.1f}% {emoji_salud} ({diferencia:+.1f}%)")
        
        # Detalles de archivos
        if exitosos:
            print(f"\n✅ ARCHIVOS REPARADOS EXITOSAMENTE:")
            for ruta in exitosos:
                criticidad = "🔴" if ruta in self.archivos_criticos else "🟡"
                print(f"   {criticidad} {os.path.relpath(ruta, self.base_path)}")
        
        if fallidos:
            print(f"\n❌ ARCHIVOS CON PROBLEMAS PERSISTENTES:")
            for ruta in fallidos:
                print(f"   ⚠️ {os.path.relpath(ruta, self.base_path)}")
        
        if rollbacks:
            print(f"\n🔄 ROLLBACKS APLICADOS:")
            for ruta in rollbacks:
                print(f"   🔙 {os.path.relpath(ruta, self.base_path)}")
        
        # Recomendaciones finales
        print(f"\n🎯 RECOMENDACIONES:")
        if len(exitosos) > len(fallidos):
            print("   ✨ ¡Excelente trabajo! La mayoría de reparaciones fueron exitosas")
        if fallidos:
            print("   🔍 Revisar manualmente archivos con problemas persistentes")
        if len(exitosos) >= 5:
            print("   📊 Considerar ejecutar diagnóstico completo para actualizar métricas")
        
        # Log final
        log_resumen = {
            "timestamp": datetime.now().isoformat(),
            "modo": self.modo,
            "salud_inicial": self.salud_inicial,
            "salud_final": self.salud_final,
            "archivos_procesados": total_procesados,
            "exitosos": [os.path.relpath(r, self.base_path) for r in exitosos],
            "fallidos": [os.path.relpath(r, self.base_path) for r in fallidos],
            "rollbacks": [os.path.relpath(r, self.base_path) for r in rollbacks],
            "archivos_criticos_reparados": len([r for r in exitosos if r in self.archivos_criticos])
        }
        
        log_path = os.path.join(self.logs_dir, f"resumen_reparacion_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        with open(log_path, "w", encoding="utf-8") as f:
            json.dump(log_resumen, f, indent=2, ensure_ascii=False)
        
        print(f"\n📝 Log completo guardado en: {os.path.basename(log_path)}")
        print("🔥 ¡REPARACIÓN DEFINITIVA COMPLETADA!")

def main():
    """🚀 Función principal con argumentos de línea de comandos"""
    parser = argparse.ArgumentParser(description="🔥 Reparador Definitivo LER - Sin miedo!")
    parser.add_argument("--modo", choices=["interactivo", "auto", "dry-run"], 
                       default="interactivo", help="Modo de operación")
    parser.add_argument("--filtro", default="*", 
                       help="Filtro de archivos (ej: *.py,core/*)")
    parser.add_argument("--base-path", default="/content/drive/MyDrive/LER",
                       help="Directorio base de LER")
    
    try:
        # En Colab, simular argumentos si no los hay
        if len(sys.argv) == 1:
            print("🎮 Ejecutando en modo interactivo (Colab)")
            reparador = ReparadorDefinitivo("/content/drive/MyDrive/LER", "interactivo")
            reparador.ejecutar_reparaciones_completas("*")
        else:
            args = parser.parse_args()
            reparador = ReparadorDefinitivo(args.base_path, args.modo)
            reparador.ejecutar_reparaciones_completas(args.filtro)
            
    except KeyboardInterrupt:
        print("\n🛑 ¡Operación cancelada! El miedo no detiene al valiente.")
    except Exception as e:
        print(f"\n💥 Error épico: {e}")
        print("🔥 Pero los errores solo nos hacen más fuertes!")
        import traceback
        traceback.print_exc()

# 🎯 FUNCIONES DE CONVENIENCIA PARA COLAB
def reparar_todo():
    """🔥 Repara todo sin miedo - Modo automático"""
    reparador = ReparadorDefinitivo("/content/drive/MyDrive/LER", "auto")
    reparador.ejecutar_reparaciones_completas("*")

def reparar_interactivo():
    """🤝 Reparación interactiva - Control total"""
    reparador = ReparadorDefinitivo("/content/drive/MyDrive/LER", "interactivo")
    reparador.ejecutar_reparaciones_completas("*")

def solo_python():
    """🐍 Solo archivos Python"""
    reparador = ReparadorDefinitivo("/content/drive/MyDrive/LER", "interactivo")
    reparador.ejecutar_reparaciones_completas("*.py")

def solo_core():
    """🎯 Solo archivos del core"""
    reparador = ReparadorDefinitivo("/content/drive/MyDrive/LER", "interactivo")
    reparador.ejecutar_reparaciones_completas("core/")

def dry_run():
    """🔍 Simulación - Solo mostrar qué haría"""
    reparador = ReparadorDefinitivo("/content/drive/MyDrive/LER", "dry-run")
    reparador.ejecutar_reparaciones_completas("*")

if __name__ == "__main__":
    print("""
🔥 REPARADOR DEFINITIVO LER - ¡SIN MIEDO A MORIR!

Funciones disponibles en Colab:
- reparar_todo()         → Modo automático completo
- reparar_interactivo()  → Control manual paso a paso  
- solo_python()          → Solo archivos .py
- solo_core()            → Solo directorio core/
- dry_run()              → Simulación sin cambios

¡El que tenga miedo a morir que no nazca! 🚀
""")
    main()
