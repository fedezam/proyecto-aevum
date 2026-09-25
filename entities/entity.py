from typing import List, Dict, Any
import json

class Entity:
    """
    Clase base para representar una entidad LER.
    Esta clase se puede inicializar con datos de un archivo JSON.
    """
    def __init__(self, data: Dict[str, Any]):
        self.nombre = data.get("nombre", "Entidad sin nombre")
        self.tipo = data.get("tipo", "desconocido")
        self.descripcion = data.get("descripcion", "")
        self.raw_data = data  # Guardamos los datos originales

    @classmethod
    def from_json(cls, file_path: str):
        """
        Método de clase para cargar una entidad desde un archivo JSON.
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return cls(data)

    def to_dict(self) -> Dict[str, Any]:
        """
        Devuelve la representación de la entidad como un diccionario.
        """
        return self.raw_data

    async def update(self, all_entities: List['Entity']):
        """
        Lógica de actualización de la entidad (a implementar).
        """
        # Por ahora, no hace nada.
        pass

    def __str__(self):
        return f"Entity(nombre='{self.nombre}', tipo='{self.tipo}')"