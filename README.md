# Cafeteria After-life (Gestión de Café)

App de escritorio en **Python + CustomTkinter + SQLite** para ventas por mesa, inventario/menú y contabilidad básica con **cierre de caja diario**.

## Requisitos

- Python 3.10+ (probado con 3.13)

## Instalación

```bash
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

## Ejecutar

```bash
python main.py
```

## Base de datos

- Persistente: `productos`
- Temporales (se vacían al cierre): `ventas_diarias`, `detalle_ventas`

El archivo SQLite se crea como `cafeteria.db` en la raíz del proyecto.

