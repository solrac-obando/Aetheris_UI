import subprocess
import os

def test_core_type_consistency():
    """Valida vía mypy que el tipado agregado en elements y engine sea consistente."""
    # Obtenemos la ruta real de los elementos
    core_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'core'))
    elements_file = os.path.join(core_path, 'elements.py')
    
    # Run mypy specifically on elements.py where we just added strict type hints
    result = subprocess.run(['mypy', elements_file, '--ignore-missing-imports'], capture_output=True, text=True)
    
    # Comprobar si hubo fallos de tipo
    assert result.returncode == 0, f"Mypy errors found in elements.py: {result.stdout}"