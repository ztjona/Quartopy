import importlib.util
import sys
from pathlib import Path
from .Bot import BotAI


import inspect

def load_bot_class(file_path: str | Path) -> type[BotAI]:
    """Importa la primera clase que hereda de BotAI desde el archivo especificado."""
    file_path = Path(file_path)
    module_name = file_path.stem

    spec = importlib.util.spec_from_file_location(module_name, file_path)

    if spec is None or spec.loader is None:
        raise ImportError(f"El archivo {file_path} debe ser un módulo Python válido.")

    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)

    # Buscar una clase que herede de BotAI
    for name, obj in inspect.getmembers(module, inspect.isclass):
        if issubclass(obj, BotAI) and obj is not BotAI:
            return obj

    raise AttributeError(
        f"Módulo {module_name} no contiene una clase que herede de 'BotAI'"
    )
