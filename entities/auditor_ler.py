import os
import sys  # Missing import added here
import json
import logging
from pathlib import Path
from datetime import datetime
import time
import requests
import shutil
import importlib.util
import subprocess
import traceback
import signal
import threading
import queue
import argparse
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

# ========= CONFIG LOGGING GLÍFICO =========
class GlyphicFormatter(logging.Formatter):
    LEVEL_GLYPHS = {
        'DEBUG': '◯',
        'INFO': '◌', 
        'WARNING': '◐',
        'ERROR': '◉',
        'CRITICAL': '■'
    }
    
    def format(self, record):
        glyph = self.LEVEL_GLYPHS.get(record.levelname, '○')
        record.glyph = glyph
        return super().format(record)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(glyph)s [%(name)s] %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("AuditorLER")

# Configurar formatter glífico de forma segura
if logger.handlers:
    logger.handlers[0].setFormatter(GlyphicFormatter())
else:
    handler = logging.StreamHandler()
    handler.setFormatter(GlyphicFormatter())
    logger.addHandler(handler)

# ========= UTILIDADES =========
def load_json(path):
    if not os.path.exists(path):
        logger.error(f"◉ No se encontró: {path}")
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"◉ JSON inválido en {path}: {e}")
        return {}

def save_json(data, path):
    """Guarda JSON con formato elegante"""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def snapshot_file(file_path: Path, snapshots_dir: Path):
    if not file_path.exists():
        return None
    snapshots_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest = snapshots_dir / f"{file_path.name}.{timestamp}.bak"
    shutil.copy(file_path, dest)
    logger.info(f"◌ Snapshot: {dest.name}")
    return dest

def verify_python_syntax(file_path: Path):
    """Verifica sintaxis Python"""
    try:
        with open(file_path, 'rb') as f:
            compile(f.read(), file_path, 'exec')
        return True, "OK"
    except SyntaxError as e:
        return False, f"SyntaxError línea {e.lineno}: {e.msg}"
    except Exception as e:
        return False, str(e)

def smoke_test_import(file_path: Path, timeout=5):
    """Test de importación con timeout"""
    if not file_path.name.endswith('.py'):
        return True, "No-Python file"
    
    try:
        spec = importlib.util.spec_from_file_location("test_module", file_path)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
        return True, "Import OK"
    except Exception as e:
        return False, f"Import failed: {str(e)[:100]}"

# ========= CLASE AUDITOR REFLEXIVO =========
class AuditorLER:
    def __init__(self, ghost_path: str, plan_path: str, root_dir: str = ".", force_reaudit=False):
        self.root_dir = Path(root_dir)
        self.ghost = load_json(ghost_path)
        self.plan = load_json(plan_path)
        
        # Configuración de directorios
        self.logs_dir = self.root_dir / "memoria" / "logs"
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self.snapshots_dir = self.root_dir / "memoria" / "snapshots"
        
        # Estado interno
        self.state_log = self.logs_dir / "auditor_state.json"
        self.actions_log = self.logs_dir / "actions.jsonl"
        self.visited_files = []
        self.analysis_results = {}
        self.session_start = datetime.now()
        self.processed_folders = set()
        
        # Nuevo: opción de re-auditoría forzada
        self.force_reaudit = force_reaudit
        
        # Nueva funcionalidad de pausa
        self.pause_requested = False
        self.input_queue = queue.Queue()
        self.monitor_thread = None
        self.should_stop_monitoring = False
        
        # Cargar estado previo (pero respetando force_reaudit)
        self.load_previous_state()
        
        if force_reaudit:
            logger.info("🔄 Modo re-auditoría activado - ignorando estado previo")
        
        # Configurar monitoreo de teclado
        self.setup_pause_monitoring()
        
        logger.info(f"◌ {self.ghost.get('IDENTITY', {}).get('NAME', 'AuditorLER')} inicializado")
        logger.info(f"◌ Axiomas activos: {self.ghost.get('IDENTITY', {}).get('AXIOMS', [])}")

    def load_previous_state(self):
        """Carga estado de sesiones anteriores (respetando force_reaudit)"""
        if self.state_log.exists() and not self.force_reaudit:
            previous_state = load_json(self.state_log)
            self.visited_files = previous_state.get('visited_files', [])
            self.processed_folders = set(previous_state.get('processed_folders', []))
            logger.info(f"◌ Estado previo cargado: {len(self.visited_files)} archivos, {len(self.processed_folders)} carpetas procesadas")
        elif self.force_reaudit and self.state_log.exists():
            logger.info("🔄 Estado previo ignorado por re-auditoría forzada")
            # Crear backup del estado anterior
            backup_path = self.state_log.with_suffix('.backup.json')
            shutil.copy(self.state_log, backup_path)
            logger.info(f"💾 Backup del estado anterior: {backup_path.name}")

    def setup_pause_monitoring(self):
        """Configura monitoreo de input para pausas"""
        def monitor_input():
            while not self.should_stop_monitoring:
                try:
                    import sys
                    import select
                    
                    if select.select([sys.stdin], [], [], 0.5)[0]:
                        user_input = input().strip().lower()
                        self.input_queue.put(user_input)
                except (EOFError, KeyboardInterrupt, OSError):
                    break
                except:
                    try:
                        user_input = input().strip().lower()
                        self.input_queue.put(user_input)
                    except:
                        time.sleep(0.1)  # Evitar consumo excesivo de CPU
                        break
        
        try:
            self.monitor_thread = threading.Thread(target=monitor_input, daemon=True)
            self.monitor_thread.start()
        except:
            logger.warning("◐ Monitoreo de pausa deshabilitado en este sistema")

    def check_pause_request(self):
        """Verifica si el usuario quiere pausar"""
        if not hasattr(self, 'input_queue'):
            return False
            
        try:
            while not self.input_queue.empty():
                user_input = self.input_queue.get_nowait()
                if user_input in ['p', 'pause', 'pausa']:
                    self.pause_requested = True
                    logger.info("⏸️  Pausa solicitada por el usuario")
                    return True
                elif user_input in ['q', 'quit', 'stop']:
                    logger.info("🛑 Detención solicitada por el usuario")
                    return 'quit'
                elif user_input in ['c', 'continue', 'continuar']:
                    self.pause_requested = False
                    logger.info("▶️  Continuando...")
        except queue.Empty:
            pass
        
        return False

    def handle_pause(self):
        """Maneja el estado de pausa con opciones extendidas"""
        print(f"\n⏸️  AUDITORÍA PAUSADA")
        print(f"   📊 Archivos procesados: {len(self.visited_files)}")
        print(f"   📁 Carpetas completadas: {len(self.processed_folders)}")
        print(f"\nOpciones disponibles:")
        print(f"   c/continue   - Continuar en carpeta actual")
        print(f"   ch/change    - Cambiar a otra carpeta")
        print(f"   sk/skip      - Saltar carpeta actual")
        print(f"   re/reaudit   - Re-auditar carpeta actual")
        print(f"   reset        - Opciones de reseteo")
        print(f"   s/status     - Ver estado detallado")
        print(f"   r/report     - Generar reporte parcial")
        print(f"   q/quit       - Guardar estado y salir")
        
        while self.pause_requested:
            try:
                choice = input("\n⏸️  Elije opción: ").strip().lower()
                
                if choice in ['c', 'continue']:
                    self.pause_requested = False
                    logger.info("▶️  Reanudando carpeta actual...")
                    return 'continue'
                    
                elif choice in ['ch', 'change', 'cambiar']:
                    new_folder = self.select_new_folder()
                    if new_folder:
                        self.pause_requested = False
                        return ('change', new_folder)
                        
                elif choice in ['sk', 'skip', 'saltar']:
                    self.pause_requested = False
                    return 'skip'
                    
                elif choice in ['re', 'reaudit', 'reauditar']:
                    confirm = input("¿Re-auditar carpeta actual desde cero? (s/n): ").strip().lower()
                    if confirm == 's':
                        self.pause_requested = False
                        return 'reaudit'
                        
                elif choice in ['reset', 'limpiar']:
                    self.handle_state_reset()
                    
                elif choice in ['s', 'status']:
                    self.show_pause_status()
                    
                elif choice in ['r', 'report']:
                    self.generate_partial_report()
                    
                elif choice in ['q', 'quit']:
                    self.save_state()
                    logger.info("💾 Estado guardado. Para continuar: python3 auditor_ler.py [carpeta]")
                    return 'quit'
                    
                else:
                    print("❌ Opción no válida. Opciones: c, ch, sk, re, reset, s, r, q")
                    
            except (KeyboardInterrupt, EOFError):
                self.save_state()
                return 'quit'

    def handle_state_reset(self):
        """Maneja el reseteo completo del estado"""
        print(f"\n🗑️  OPCIONES DE RESETEO:")
        print(f"   1. Solo carpetas procesadas")
        print(f"   2. Solo archivos visitados") 
        print(f"   3. Estado completo")
        print(f"   4. Cancelar")
        
        while True:
            choice = input("Elige opción (1-4): ").strip()
            
            if choice == '1':
                self.processed_folders.clear()
                logger.info("🧹 Carpetas procesadas limpiadas")
                break
            elif choice == '2':
                self.visited_files.clear()
                self.analysis_results.clear()
                logger.info("🧹 Archivos visitados limpiados")
                break
            elif choice == '3':
                confirm = input("⚠️  Esto borrará TODO el progreso. ¿Confirmas? (s/n): ").strip().lower()
                if confirm == 's':
                    self.visited_files.clear()
                    self.analysis_results.clear()
                    self.processed_folders.clear()
                    # Crear backup antes de limpiar
                    if self.state_log.exists():
                        backup_path = self.state_log.with_suffix(f'.backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
                        shutil.copy(self.state_log, backup_path)
                        logger.info(f"💾 Backup creado: {backup_path.name}")
                    logger.info("🧹 Estado completo reiniciado")
                    break
            elif choice == '4':
                break
            else:
                print("Opción inválida")

    def select_new_folder(self):
        """Permite seleccionar una nueva carpeta interactivamente"""
        project_tree, _ = self.scan_project()
        
        print(f"\n📁 CARPETAS DISPONIBLES:")
        print(f"{'Carpeta':<25} {'Archivos':<10} {'Procesada':<10}")
        print("-" * 50)
        
        folder_options = {}
        for i, (folder, files) in enumerate(project_tree.items(), 1):
            if not files:
                continue
                
            status = "✅ Sí" if folder in self.processed_folders else "⏳ No"
            file_count = len(files)
            
            print(f"{i:2}. {folder:<22} {file_count:<10} {status:<10}")
            folder_options[str(i)] = folder
            folder_options[folder] = folder
        
        while True:
            choice = input(f"\n📁 Selecciona carpeta (número/nombre, o 'b' para volver): ").strip()
            
            if choice.lower() == 'b':
                return None
                
            if choice in folder_options:
                selected_folder = folder_options[choice]
                file_count = len(project_tree[selected_folder])
                
                if file_count > 20:
                    print(f"⚠️  Esta carpeta tiene {file_count} archivos.")
                    confirm = input(f"¿Estás seguro? (s/n): ").strip().lower()
                    if confirm != 's':
                        continue
                
                logger.info(f"📁 Cambiando a carpeta: {selected_folder} ({file_count} archivos)")
                return selected_folder
                
            else:
                print(f"❌ Opción no válida. Intenta de nuevo.")

    def show_pause_status(self):
        """Muestra estado detallado durante la pausa"""
        duration = (datetime.now() - self.session_start).total_seconds() / 60
        
        print(f"\n📊 ESTADO ACTUAL DE LA AUDITORÍA:")
        print(f"   ⏱️  Tiempo transcurrido: {duration:.1f} minutos")
        print(f"   📁 Archivos procesados: {len(self.visited_files)}")
        
        if self.analysis_results:
            problems_found = sum(1 for analysis in self.analysis_results.values() 
                               if analysis.get("problemas") and 
                               analysis["problemas"] != ["Sin problemas detectados"])
            
            print(f"   🔍 Archivos con problemas: {problems_found}")
            print(f"   📋 Carpetas completadas: {len(self.processed_folders)}")
            
            if self.processed_folders:
                print(f"   ✅ Completadas: {', '.join(list(self.processed_folders)[:3])}")

    def generate_partial_report(self):
        """Genera reporte parcial durante pausa"""
        report = self.generate_final_report()
        print(f"\n📋 REPORTE PARCIAL:")
        print(f"   📊 Archivos procesados: {report['statistics']['files_processed']}")
        print(f"   🔧 Archivos modificados: {report['statistics']['files_changed']}")
        print(f"   ⏱️  Duración: {report['session']['duration_minutes']:.1f} minutos")
        return report

    def save_state(self):
        """Guarda estado con información de contexto de pausa"""
        state = {
            "entity": self.ghost.get("IDENTITY", {}).get("NAME", "AuditorLER"),
            "session_start": self.session_start.isoformat(),
            "last_update": datetime.now().isoformat(),
            "visited_files": self.visited_files,
            "processed_folders": list(self.processed_folders),
            "files_processed": len(self.visited_files),
            "ghost_version": self.ghost.get("VERSION", "unknown"),
            "plan_version": self.plan.get("PLAN_MODE", "unknown"),
            "resume_hint": "Para continuar: python3 auditor_ler.py [nombre_carpeta]"
        }
        save_json(state, self.state_log)
        logger.info(f"💾 Estado guardado en: {self.state_log}")

    def log_action(self, action_type: str, file_path: Path, details: dict):
        """Registra acciones en formato JSONL para análisis posterior"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "action": action_type,
            "file": str(file_path.relative_to(self.root_dir)),
            "entity": self.ghost.get("IDENTITY", {}).get("NAME"),
            "details": details
        }
        
        with open(self.actions_log, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")

    def scan_project(self):
        """Escaneo inteligente del proyecto"""
        project_tree = {}
        protected_paths = []
        
        for root, dirs, files in os.walk(self.root_dir):
            root_path = Path(root)
            rel_root = root_path.relative_to(self.root_dir)
            
            if any(skip in str(rel_root) for skip in [".git", "__pycache__", "node_modules"]):
                continue
                
            if self.is_protected_path(root_path):
                protected_paths.append(str(rel_root))
            
            relevant_files = [f for f in files if f.endswith(('.py', '.json', '.md'))]
            if relevant_files:
                project_tree[str(rel_root)] = relevant_files
        
        logger.info(f"◌ Proyecto escaneado: {len(project_tree)} carpetas, {len(protected_paths)} protegidas")
        return project_tree, protected_paths

    def is_protected_path(self, path: Path):
        """Verifica si una ruta está protegida según axiomas"""
        protected = [
            self.root_dir / "glifos", 
            self.root_dir / "core" / "mathema"
        ]
        path = path.resolve()
        return any(path.is_relative_to(p.resolve()) for p in protected if p.exists())

    def build_llm_prompt(self, file_path: Path, content: str, phase: str = "THINK"):
        """Construye prompt contextual según la fase del ciclo THINK→PLAN→CONFIRM→DO"""
        base_context = {
            "phase": phase,
            "file_path": str(file_path.relative_to(self.root_dir)),
            "content": content,
            "entity_identity": self.ghost.get("IDENTITY", {}),
            "active_glyphs": self.ghost.get("COGNITIVE_STATE", {}).get("ACTIVE_GLYPHS", []),
            "axioms": self.ghost.get("IDENTITY", {}).get("AXIOMS", []),
            "session_context": {
                "files_processed": len(self.visited_files),
                "last_files": self.visited_files[-3:] if self.visited_files else []
            }
        }
        
        phase_prompts = self.ghost.get("PROMPTS_CANONICAL", {})
        specific_prompt = phase_prompts.get(phase, f"Procesa este archivo en fase {phase}")
        
        return {
            "role_prompt": self.ghost.get("MODEL_ADAPTERS", {}).get("DEFAULT", {}).get("ROLE_PROMPT", ""),
            "specific_instruction": specific_prompt,
            "context": base_context,
            "expected_format": "JSON con campos: analisis, problemas, sugerencia, gravedad, tests_recomendados"
        }

    def extract_json_from_text(self, text: str):
        """Extrae JSON de texto que puede contener otros elementos"""
        if not text:
            return {}
            
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
        
        import re
        json_patterns = [
            r'\{.*\}',
            r'\[.*\]'
        ]
        
        for pattern in json_patterns:
            matches = re.finditer(pattern, text, re.DOTALL)
            for match in matches:
                try:
                    return json.loads(match.group())
                except json.JSONDecodeError:
                    continue
        
        return {
            "analisis": text[:200] + "..." if len(text) > 200 else text,
            "problemas": ["Respuesta no estructurada del LLM"],
            "sugerencia": "Sin cambios sugeridos",
            "gravedad": "low"
        }

    def call_llm(self, prompt_data: dict):
        """Llamada mejorada al LLM con manejo de errores robusto"""
        try:
            # Verificar carga del .env
            api_key = os.getenv('ZHIPU_API_KEY')
            if not api_key:
                logger.error("◉ ZHIPU_API_KEY no encontrada en variables de entorno")
                logger.error(f"◉ Archivo .env existe: {os.path.exists('.env')}")
                logger.error(f"◉ Directorio actual: {os.getcwd()}")
                raise ValueError("ZHIPU_API_KEY not found")
            
            # Log de conexión (sin mostrar la key completa)
            logger.info(f"◌ API Key encontrada: {api_key[:10]}...")
            
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            model_config = self.ghost.get("MODEL_ADAPTERS", {}).get("DEFAULT", {})
            endpoint = model_config.get("endpoint", "https://open.bigmodel.cn/api/paas/v4/chat/completions")
            model = model_config.get("model", "glm-4")
            
            logger.info(f"◌ Endpoint: {endpoint}")
            logger.info(f"◌ Modelo: {model}")
            
            # Construir payload con prompt más claro para obtener JSON
            system_prompt = f"""Eres un auditor de código experto. Responde SIEMPRE en formato JSON válido con estos campos exactos:
{{
  "analisis": "descripción del análisis realizado",
  "problemas": ["lista", "de", "problemas", "encontrados"],
  "sugerencia": "cambios sugeridos o código mejorado",
  "gravedad": "low|medium|high",
  "tests_recomendados": ["tests", "sugeridos"]
}}

Si no hay problemas, usa: "problemas": ["Sin problemas detectados"]"""

            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Analiza este archivo:\n\n{json.dumps(prompt_data, ensure_ascii=False, indent=2)}"}
                ],
                "max_tokens": model_config.get("MAX_TOKENS", 4096),
                "temperature": model_config.get("TEMPERATURE", 0.12)
            }
            
            logger.info("◌ Enviando request al LLM...")
            response = requests.post(endpoint, headers=headers, json=payload, timeout=30)
            
            logger.info(f"◌ Status code: {response.status_code}")
            
            if not response.ok:
                logger.error(f"◉ Error HTTP: {response.status_code}")
                logger.error(f"◉ Response: {response.text[:200]}")
                response.raise_for_status()
            
            result = response.json()
            llm_output = result.get("choices", [{}])[0].get("message", {}).get("content", "{}")
            
            logger.info(f"◌ LLM response (primeros 100 chars): {llm_output[:100]}...")
            
            
            parsed_result = self.extract_json_from_text(llm_output)
            logger.info("◌ JSON parseado exitosamente")
            return parsed_result
                    
        except Exception as e:
            logger.error(f"◉ Error LLM: {str(e)[:100]}")
            return {
                "analisis": f"Error de comunicación con LLM: {str(e)}",
                "problemas": ["LLM_UNAVAILABLE"],
                "sugerencia": "Revisión manual requerida",
                "gravedad": "high",
                "error": str(e)
            }

    def extract_content_from_suggestion(self, suggestion):
        """Extrae contenido de archivo de una sugerencia que puede ser dict o string"""
        if isinstance(suggestion, str):
            return suggestion.strip()
        elif isinstance(suggestion, dict):
            # Buscar campos que contengan el código/contenido sugerido
            content_fields = ['sugerencia', 'content', 'codigo', 'file_content', 'new_content', 'codigo_mejorado', 'archivo_modificado']
            for field in content_fields:
                if field in suggestion:
                    value = suggestion[field]
                    if isinstance(value, str):
                        return value.strip()
                    elif isinstance(value, dict):
                        # Si el campo contiene otro dict, intentar extraer contenido recursivamente
                        return self.extract_content_from_suggestion(value)
            
            # Si no encuentra campos específicos, buscar el valor más largo que parezca código
            for key, value in suggestion.items():
                if isinstance(value, str) and len(value) > 50 and ('\n' in value or 'def ' in value or 'class ' in value):
                    return value.strip()
            
            # Como último recurso, devolver JSON formateado
            return json.dumps(suggestion, indent=2, ensure_ascii=False)
        else:
            return str(suggestion).strip() if hasattr(suggestion, 'strip') else str(suggestion)

    def audit_file(self, file_path: Path):
        """Auditoría completa de un archivo siguiendo el ciclo THINK→PLAN"""
        # Verificar si ya fue procesado (solo si no es re-auditoría forzada)
        if not self.force_reaudit and file_path in [Path(f) for f in self.visited_files]:
            logger.info(f"◐ Ya procesado: {file_path.name}")
            return None
        elif self.force_reaudit and file_path in [Path(f) for f in self.visited_files]:
            logger.info(f"🔄 Re-auditando: {file_path.name}")
            
        try:
            content = file_path.read_text(encoding="utf-8")
        except Exception as e:
            logger.error(f"◉ No se pudo leer {file_path}: {e}")
            return None

        logger.info(f"◌ Auditando: {file_path.relative_to(self.root_dir)}")

        # FASE THINK: Análisis
        think_prompt = self.build_llm_prompt(file_path, content, "THINK")
        analysis = self.call_llm(think_prompt)
        
        self.log_action("THINK", file_path, analysis)

        # FASE PLAN: Si hay problemas, generar plan de corrección
        if analysis.get("problemas") and analysis["problemas"] != ["Sin problemas detectados"]:
            plan_prompt = self.build_llm_prompt(file_path, content, "PLAN")
            plan_result = self.call_llm(plan_prompt)
            analysis["plan"] = plan_result
            self.log_action("PLAN", file_path, plan_result)

        # Registrar en estado
        if str(file_path) not in self.visited_files:
            self.visited_files.append(str(file_path))
        self.analysis_results[str(file_path)] = analysis
        self.save_state()
        
        return analysis

    def apply_changes(self, file_path: Path, new_content: str, analysis: dict):
        """Aplica cambios con verificación completa"""
        snapshot_path = snapshot_file(file_path, self.snapshots_dir)
        if not snapshot_path:
            logger.error(f"◉ No se pudo crear snapshot para {file_path}")
            return False

        try:
            file_path.write_text(new_content, encoding="utf-8")
            logger.info(f"◌ Cambios aplicados a {file_path.name}")

            syntax_ok, syntax_msg = True, "N/A"
            import_ok, import_msg = True, "N/A"
            
            if file_path.suffix == '.py':
                syntax_ok, syntax_msg = verify_python_syntax(file_path)
                if not syntax_ok:
                    logger.error(f"◉ Sintaxis inválida: {syntax_msg}")
                    shutil.copy(snapshot_path, file_path)
                    logger.info("◐ Cambios revertidos automáticamente")
                    return False
                
                import_ok, import_msg = smoke_test_import(file_path)
                if not import_ok:
                    logger.warning(f"◐ Advertencia de importación: {import_msg}")

            self.log_action("APPLY", file_path, {
                "snapshot": str(snapshot_path),
                "verification": {"syntax": syntax_ok, "import": import_ok},
                "gravedad": analysis.get("gravedad", "unknown")
            })
            
            return True
            
        except Exception as e:
            logger.error(f"◉ Error aplicando cambios: {e}")
            if snapshot_path and snapshot_path.exists():
                shutil.copy(snapshot_path, file_path)
                logger.info("◐ Cambios revertidos por error")
            return False

    def interactive_confirm(self, file_path: Path, analysis: dict) -> bool:
        """Confirmación interactiva inteligente"""
        problemas = analysis.get("problemas", [])
        gravedad = analysis.get("gravedad", "unknown")
        
        if not problemas or problemas == ["Sin problemas detectados"]:
            logger.info("◯ Sin cambios necesarios")
            return False
            
        print(f"\n◌ Archivo: {file_path.relative_to(self.root_dir)}")
        print(f"◐ Gravedad: {gravedad}")
        print(f"◉ Problemas: {', '.join(problemas[:3])}")
        
        if len(problemas) > 3:
            print(f"   ... y {len(problemas)-3} más")
            
        if gravedad == "low" and self.ghost.get("INTERFACE", {}).get("AUTO_APPLY_LOW", False):
            logger.info("◯ Aplicando automáticamente (gravedad baja)")
            return True
            
        while True:
            response = input("◌ ¿Aplicar cambios? (s/n/d=detalles): ").strip().lower()
            if response == 's':
                return True
            elif response == 'n':
                return False
            elif response == 'd':
                print(f"◯ Análisis: {analysis.get('analisis', 'N/A')}")
                plan = analysis.get('plan', {})
                if plan:
                    print(f"◯ Plan: {plan.get('plan_steps', 'N/A')}")
            else:
                print("◐ Respuesta no válida")

    def process_folder(self, folder_name: str, reaudit=False):
        """Procesa una carpeta específica con manejo de pausas y re-auditoría"""
        project_tree, protected_paths = self.scan_project()
        
        if folder_name not in project_tree:
            logger.error(f"❌ Carpeta no encontrada: {folder_name}")
            return 'skip'
        
        # Si es re-auditoría, remover carpeta del estado procesado
        if reaudit:
            self.processed_folders.discard(folder_name)
            # Remover archivos de esta carpeta del estado
            folder_files = [f for f in self.visited_files if folder_name in f]
            for file_path in folder_files:
                self.visited_files.remove(file_path)
                if file_path in self.analysis_results:
                    del self.analysis_results[file_path]
            logger.info(f"🔄 Re-auditando carpeta: {folder_name}")
        
        files_to_process = project_tree[folder_name]
        total_files = len(files_to_process)
        processed = 0
        
        logger.info(f"📁 Procesando: {folder_name} ({total_files} archivos)")
        if reaudit:
            print(f"🔄 Modo re-auditoría - procesando todos los archivos de nuevo")
        print(f"💡 Para pausar y cambiar carpeta, escribe 'p' y presiona Enter")
        
        for file in files_to_process:
            # Verificar pausa antes de cada archivo
            pause_result = self.check_pause_request()
            if pause_result:
                if pause_result == 'quit':
                    return 'quit'
                elif self.pause_requested:
                    handle_result = self.handle_pause()
                    if handle_result == 'quit':
                        return 'quit'
                    elif handle_result == 'skip':
                        return 'skip'
                    elif handle_result == 'reaudit':
                        # Reiniciar procesamiento de carpeta actual
                        return self.process_folder(folder_name, reaudit=True)
                    elif isinstance(handle_result, tuple) and handle_result[0] == 'change':
                        return handle_result
        
            file_path = self.root_dir / folder_name / file
            
            if file_path.name == "auditor_ler.py":
                continue
                
            analysis = self.audit_file(file_path)
            if not analysis:
                continue
                
            processed += 1
            logger.info(f"📊 Progreso: {processed}/{total_files} ({(processed/total_files)*100:.1f}%)")
            
            # Verificar si el archivo está protegido
            if self.is_protected_path(file_path):
                logger.info(f"◐ Protegido, solo análisis: {file_path.name}")
                continue
            
            # Proceso de confirmación y aplicación
            plan_result = analysis.get("plan", {})
            if plan_result and "sugerencia" in plan_result:
                new_content = self.extract_content_from_suggestion(plan_result["sugerencia"])
                
                # Validar que new_content sea una string válida
                if not isinstance(new_content, str):
                    logger.warning(f"◐ Sugerencia no es texto válido en {file_path.name}, saltando...")
                    continue
                
                try:
                    original_content = file_path.read_text(encoding="utf-8")
                    
                    if new_content.strip() != original_content.strip():
                        if self.interactive_confirm(file_path, analysis):
                            success = self.apply_changes(file_path, new_content, analysis)
                            if success:
                                logger.info(f"◌ ✓ {file_path.name} actualizado exitosamente")
                            else:
                                logger.error(f"◉ ✗ Error actualizando {file_path.name}")
                    else:
                        logger.info(f"◯ Sin cambios necesarios en {file_path.name}")
                except Exception as e:
                    logger.error(f"◉ Error procesando {file_path.name}: {e}")
            
            # Breve pausa para revisar logs y permitir pausas
            time.sleep(0.3)
        
        logger.info(f"✅ Carpeta {folder_name} completada")
        return 'completed'

    def run(self, start_folder: str = None):
        """Ciclo principal con soporte para cambio de ruta"""
        logger.info("▶️  Iniciando ciclo reflexivo de auditoría...")
        
        current_folder = start_folder
        
        while True:
            if not current_folder:
                current_folder = self.suggest_initial_folder()
                if not current_folder:
                    break
            
            result = self.process_folder(current_folder)
            
            if result == 'quit':
                break
            elif result == 'skip':
                logger.info(f"⏭️  Saltando carpeta: {current_folder}")
                self.processed_folders.add(current_folder)
                current_folder = None
            elif isinstance(result, tuple) and result[0] == 'change':
                logger.info(f"🔄 Cambiando de {current_folder} → {result[1]}")
                current_folder = result[1]
            elif result == 'completed':
                self.processed_folders.add(current_folder)
                self.generate_folder_completion_report(current_folder)
                next_folder = self.suggest_next_folder_auto()
                if next_folder:
                    current_folder = next_folder
                else:
                    current_folder = None
            else:
                break
        
        # Cleanup al finalizar
        self.should_stop_monitoring = True
        if self.monitor_thread:
            try:
                self.monitor_thread.join(timeout=1)
            except:
                pass
                
        logger.info("🏁 Auditoría finalizada")

    def suggest_initial_folder(self):
        """Sugiere carpeta inicial con información de tamaño"""
        project_tree, _ = self.scan_project()
        
        print(f"\n🎯 SELECCIÓN INTELIGENTE DE CARPETA:")
        
        small_folders = {k: v for k, v in project_tree.items() if len(v) <= 10 and v}
        medium_folders = {k: v for k, v in project_tree.items() if 10 < len(v) <= 30 and v}
        large_folders = {k: v for k, v in project_tree.items() if len(v) > 30}
        
        if small_folders:
            print(f"📦 Carpetas pequeñas (≤10 archivos) - Recomendadas:")
            for folder, files in small_folders.items():
                status = "✅" if folder in self.processed_folders else "⏳"
                print(f"   {status} {folder} ({len(files)} archivos)")
        
        if medium_folders:
            print(f"\n📦 Carpetas medianas (11-30 archivos):")
            for folder, files in medium_folders.items():
                status = "✅" if folder in self.processed_folders else "⏳"
                print(f"   {status} {folder} ({len(files)} archivos)")
        
        if large_folders:
            print(f"\n⚠️  Carpetas grandes (>30 archivos) - ¡Cuidado!")
            for folder, files in large_folders.items():
                status = "✅" if folder in self.processed_folders else "⏳"
                print(f"   {status} {folder} ({len(files)} archivos)")
        
        return self.select_new_folder()

    def generate_folder_completion_report(self, folder_name: str):
        """Genera reporte específico al completar una carpeta"""
        folder_files = [f for f in self.visited_files if folder_name in f]
        
        files_with_changes = 0
        for file_path in folder_files:
            analysis = self.analysis_results.get(file_path, {})
            if analysis.get("plan", {}).get("sugerencia"):
                files_with_changes += 1
        
        logger.info(f"📋 Carpeta '{folder_name}' completada:")
        logger.info(f"   📄 Archivos procesados: {len(folder_files)}")
        logger.info(f"   🔧 Archivos con cambios: {files_with_changes}")

    def suggest_next_folder_auto(self):
        """Sugiere automáticamente la siguiente carpeta sin interacción"""
        project_tree, _ = self.scan_project()
        
        pending_small = {}
        pending_medium = {}
        
        for folder, files in project_tree.items():
            if folder not in self.processed_folders and files:
                if len(files) <= 10:
                    pending_small[folder] = files
                elif len(files) <= 30:
                    pending_medium[folder] = files
        
        if pending_small:
            next_folder = min(pending_small.keys(), key=lambda x: len(pending_small[x]))
            print(f"\n🎯 Siguiente carpeta sugerida: {next_folder} ({len(pending_small[next_folder])} archivos)")
            
            response = input("¿Continuar con esta carpeta? (s/n/otra): ").strip().lower()
            if response == 's':
                return next_folder
            elif response == 'otra':
                return self.select_new_folder()
            else:
                return None
        
        elif pending_medium:
            next_folder = min(pending_medium.keys(), key=lambda x: len(pending_medium[x]))
            print(f"\n📦 Carpeta mediana disponible: {next_folder} ({len(pending_medium[next_folder])} archivos)")
            
            response = input("¿Procesar esta carpeta? (s/n): ").strip().lower()
            if response == 's':
                return next_folder
            else:
                return None
        
        else:
            print("\n🎉 ¡Todas las carpetas han sido procesadas!")
            self.show_final_project_summary()
            return None

    def show_final_project_summary(self):
        """Muestra resumen final del proyecto completo"""
        total_files = len(self.visited_files)
        files_with_changes = sum(1 for analysis in self.analysis_results.values() 
                               if analysis.get("plan", {}).get("sugerencia"))
        
        duration = (datetime.now() - self.session_start).total_seconds() / 60
        
        print(f"\n🎉 PROYECTO LER COMPLETAMENTE AUDITADO")
        print(f"=" * 50)
        print(f"📊 Total de archivos procesados: {total_files}")
        print(f"🔧 Archivos modificados: {files_with_changes}")
        print(f"📁 Carpetas completadas: {len(self.processed_folders)}")
        print(f"⏱️  Tiempo total: {duration:.1f} minutos")
        print(f"🛡️  Rutas protegidas respetadas: ✅")
        
        final_report = self.generate_final_report()
        logger.info(f"📋 Reporte final guardado")

    def generate_final_report(self):
        """Genera reporte final de la sesión"""
        files_changed = 0
        for analysis in self.analysis_results.values():
            plan = analysis.get("plan", {})
            if plan and "sugerencia" in plan:
                suggestion = plan["sugerencia"]
                content = self.extract_content_from_suggestion(suggestion)
                if content and content.strip():
                    files_changed += 1
        
        report = {
            "entity": self.ghost.get("IDENTITY", {}).get("NAME"),
            "session": {
                "start": self.session_start.isoformat(),
                "end": datetime.now().isoformat(),
                "duration_minutes": (datetime.now() - self.session_start).total_seconds() / 60
            },
            "statistics": {
                "files_processed": len(self.visited_files),
                "files_changed": files_changed,
                "folders_completed": len(self.processed_folders),
                "protected_paths_respected": True
            },
            "summary": {
                "axioms_followed": self.ghost.get("IDENTITY", {}).get("AXIOMS", []),
                "active_glyphs": self.ghost.get("COGNITIVE_STATE", {}).get("ACTIVE_GLYPHS", [])
            }
        }
        
        report_path = self.logs_dir / f"session_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        save_json(report, report_path)
        logger.info(f"◌ Reporte guardado: {report_path.name}")
        
        return report

# ========= PUNTO DE ENTRADA =========
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Auditor reflexivo LER con opciones de re-auditoría')
    parser.add_argument('folder', nargs='?', help='Carpeta inicial a procesar')
    parser.add_argument('--force', '-f', action='store_true', 
                       help='Forzar re-auditoría completa ignorando estado previo')
    parser.add_argument('--reset', action='store_true', 
                       help='Limpiar estado completamente y empezar desde cero')
    parser.add_argument('--reaudit-folder', 
                       help='Re-auditar una carpeta específica')
    
    args = parser.parse_args()
    
    # Mostrar ayuda si se solicita
    if len(sys.argv) == 1:
        print("🤖 AUDITOR LER - Sistema de auditoría reflexiva")
        print("\nUso:")
        print("  python3 auditor_ler.py [carpeta]              # Procesar carpeta específica")
        print("  python3 auditor_ler.py --force                # Re-auditar todo el proyecto")
        print("  python3 auditor_ler.py --reset                # Limpiar estado y empezar de cero")
        print("  python3 auditor_ler.py --reaudit-folder core  # Re-auditar carpeta específica")
        print("\nOpciones durante ejecución:")
        print("  'p' + Enter   - Pausar y mostrar menú")
        print("  'q' + Enter   - Guardar estado y salir")
        print("  'c' + Enter   - Continuar")
        print("\n💡 El estado se guarda automáticamente y se puede resumir después")
        sys.exit(0)
    
    root_dir = Path(__file__).resolve().parent.parent
    ghost_path = Path(__file__).resolve().parent / "ghost_auditor.json"
    plan_path = Path(__file__).resolve().parent / "plan_mode.json"
    
    if not ghost_path.exists():
        print(f"◉ No se encontró: {ghost_path}")
        sys.exit(1)
    
    if not plan_path.exists():
        print(f"◉ No se encontró: {plan_path}")
        sys.exit(1)
    
    try:
        auditor = AuditorLER(str(ghost_path), str(plan_path), str(root_dir), 
                           force_reaudit=args.force)
        
        if args.reset:
            auditor.visited_files.clear()
            auditor.analysis_results.clear()
            auditor.processed_folders.clear()
            logger.info("🧹 Estado reiniciado por --reset")
        
        # Manejar re-auditoría de carpeta específica
        start_folder = args.folder
        if args.reaudit_folder:
            # Limpiar estado para esa carpeta específica
            auditor.processed_folders.discard(args.reaudit_folder)
            folder_files = [f for f in auditor.visited_files if args.reaudit_folder in f]
            for file_path in folder_files:
                auditor.visited_files.remove(file_path)
                if file_path in auditor.analysis_results:
                    del auditor.analysis_results[file_path]
            start_folder = args.reaudit_folder
            logger.info(f"🔄 Re-auditoría configurada para: {args.reaudit_folder}")
        
        auditor.run(start_folder)
        
    except KeyboardInterrupt:
        print("\n🛑 Auditoría interrumpida por el usuario")
        print("💾 El estado se guardó automáticamente")
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
        logger.error(f"Error fatal: {e}")
        traceback.print_exc()