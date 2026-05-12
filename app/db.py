from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any


DB_PATH = Path("cafeteria.db")


@dataclass(frozen=True)
class Producto:
    id: int
    nombre: str
    categoria: str
    precio_venta: float
    usa_inventario: bool
    stock: int


class CafeDB:
    def __init__(self, db_path: Path | str = DB_PATH) -> None:
        self.db_path = Path(db_path)
        self._conn = sqlite3.connect(self.db_path)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA foreign_keys = ON;")

        self._create_schema()

    def close(self) -> None:
        self._conn.close()

    def _create_schema(self) -> None:
        # Persistente
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS productos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                categoria TEXT NOT NULL,
                precio_venta REAL NOT NULL,
                usa_inventario INTEGER NOT NULL DEFAULT 0,
                stock INTEGER NOT NULL DEFAULT 0
            );
            """
        )

        # Temporales (se vacían en cierre de caja)
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS ventas_diarias (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fecha TEXT NOT NULL,
                mesa TEXT NOT NULL,
                total REAL NOT NULL DEFAULT 0,
                pagado INTEGER NOT NULL DEFAULT 0,
                pagado_en TEXT
            );
            """
        )

        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS detalle_ventas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                venta_id INTEGER NOT NULL,
                producto_id INTEGER,
                nombre_producto TEXT NOT NULL,
                categoria TEXT NOT NULL,
                precio_unitario REAL NOT NULL,
                cantidad INTEGER NOT NULL,
                subtotal REAL NOT NULL,
                FOREIGN KEY (venta_id) REFERENCES ventas_diarias(id) ON DELETE CASCADE
            );
            """
        )

        # Migraciones para bases existentes
        for col, definition in [("pagado", "INTEGER NOT NULL DEFAULT 0"), ("pagado_en", "TEXT")]:
            try:
                self._conn.execute(f"ALTER TABLE ventas_diarias ADD COLUMN {col} {definition};")
            except sqlite3.OperationalError:
                pass

        self._conn.commit()

    # ---------- Productos ----------
    def listar_categorias(self) -> list[str]:
        rows = self._conn.execute(
            "SELECT DISTINCT categoria FROM productos ORDER BY categoria ASC;"
        ).fetchall()
        return [str(r["categoria"]) for r in rows]

    def buscar_productos(
        self, texto: str = "", categoria: str | None = None
    ) -> list[Producto]:
        texto = (texto or "").strip()
        params: list[Any] = []
        where: list[str] = []

        if texto:
            where.append("(nombre LIKE ?)")
            params.append(f"%{texto}%")

        if categoria and categoria != "Todas":
            where.append("categoria = ?")
            params.append(categoria)

        where_sql = f"WHERE {' AND '.join(where)}" if where else ""
        rows = self._conn.execute(
            f"""
            SELECT id, nombre, categoria, precio_venta, usa_inventario, stock
            FROM productos
            {where_sql}
            ORDER BY categoria ASC, nombre ASC;
            """,
            params,
        ).fetchall()
        return [self._row_to_producto(r) for r in rows]

    def crear_producto(
        self,
        nombre: str,
        categoria: str,
        precio_venta: float,
        usa_inventario: bool,
        stock: int,
    ) -> int:
        nombre = (nombre or "").strip()
        categoria = (categoria or "").strip()
        if not nombre:
            raise ValueError("El nombre del producto es obligatorio.")
        if not categoria:
            raise ValueError("La categoría es obligatoria.")
        precio_venta = float(precio_venta)
        if precio_venta < 0:
            raise ValueError("El precio no puede ser negativo.")
        stock = int(stock)
        if stock < 0:
            raise ValueError("El stock no puede ser negativo.")

        cur = self._conn.execute(
            """
            INSERT INTO productos (nombre, categoria, precio_venta, usa_inventario, stock)
            VALUES (?, ?, ?, ?, ?);
            """,
            (
                nombre,
                categoria,
                float(precio_venta),
                1 if usa_inventario else 0,
                int(stock),
            ),
        )
        self._conn.commit()
        return int(cur.lastrowid)

    def actualizar_stock(self, producto_id: int, nuevo_stock: int) -> None:
        self._conn.execute(
            "UPDATE productos SET stock = ? WHERE id = ?;", (int(nuevo_stock), int(producto_id))
        )
        self._conn.commit()

    def set_usa_inventario(self, producto_id: int, usa: bool) -> None:
        self._conn.execute(
            "UPDATE productos SET usa_inventario = ? WHERE id = ?;",
            (1 if usa else 0, int(producto_id)),
        )
        self._conn.commit()

    def actualizar_producto(
        self,
        producto_id: int,
        nombre: str,
        categoria: str,
        precio_venta: float,
        usa_inventario: bool,
        stock: int,
    ) -> None:
        nombre = (nombre or "").strip()
        categoria = (categoria or "").strip()
        if not nombre:
            raise ValueError("El nombre del producto es obligatorio.")
        if not categoria:
            raise ValueError("La categoría es obligatoria.")
        precio_venta = float(precio_venta)
        if precio_venta < 0:
            raise ValueError("El precio no puede ser negativo.")
        stock = int(stock)
        if stock < 0:
            raise ValueError("El stock no puede ser negativo.")

        self._conn.execute(
            """
            UPDATE productos
            SET nombre = ?, categoria = ?, precio_venta = ?, usa_inventario = ?, stock = ?
            WHERE id = ?;
            """,
            (
                nombre,
                categoria,
                float(precio_venta),
                1 if usa_inventario else 0,
                int(stock),
                int(producto_id),
            ),
        )
        self._conn.commit()

    def _row_to_producto(self, r: sqlite3.Row) -> Producto:
        return Producto(
            id=int(r["id"]),
            nombre=str(r["nombre"]),
            categoria=str(r["categoria"]),
            precio_venta=float(r["precio_venta"]),
            usa_inventario=bool(int(r["usa_inventario"])),
            stock=int(r["stock"]),
        )

    # ---------- Ventas ----------
    def crear_venta(self, mesa: str, fecha_: str | None = None) -> int:
        fecha_ = fecha_ or date.today().isoformat()
        cur = self._conn.execute(
            "INSERT INTO ventas_diarias (fecha, mesa, total) VALUES (?, ?, 0);",
            (fecha_, mesa.strip() or "Mesa",),
        )
        self._conn.commit()
        return int(cur.lastrowid)

    def agregar_item_a_venta(
        self,
        venta_id: int,
        producto: Producto,
        cantidad: int = 1,
    ) -> None:
        cantidad = int(cantidad)
        if cantidad <= 0:
            raise ValueError("La cantidad debe ser >= 1.")

        precio_unitario = float(producto.precio_venta)
        subtotal = precio_unitario * cantidad

        self._validar_y_desc_contar_stock(producto, cantidad)

        self._conn.execute(
            """
            INSERT INTO detalle_ventas
                (venta_id, producto_id, nombre_producto, categoria, precio_unitario, cantidad, subtotal)
            VALUES (?, ?, ?, ?, ?, ?, ?);
            """,
            (
                int(venta_id),
                int(producto.id),
                str(producto.nombre),
                str(producto.categoria),
                float(precio_unitario),
                int(cantidad),
                float(subtotal),
            ),
        )

        self._recalcular_total_venta(venta_id)
        self._conn.commit()

    def _validar_y_desc_contar_stock(self, p: Producto, cantidad: int) -> None:
        if not p.usa_inventario:
            return
        row = self._conn.execute(
            "SELECT stock FROM productos WHERE id = ?;", (int(p.id),)
        ).fetchone()
        if row is None:
            raise ValueError("Producto inexistente.")
        stock_actual = int(row["stock"])
        if stock_actual < cantidad:
            raise ValueError(f"Stock insuficiente para '{p.nombre}'. Disponible: {stock_actual}.")
        self._conn.execute(
            "UPDATE productos SET stock = stock - ? WHERE id = ?;", (int(cantidad), int(p.id))
        )

    def _recalcular_total_venta(self, venta_id: int) -> None:
        row = self._conn.execute(
            "SELECT COALESCE(SUM(subtotal),0) AS t FROM detalle_ventas WHERE venta_id = ?;",
            (int(venta_id),),
        ).fetchone()
        total = float(row["t"]) if row else 0.0
        self._conn.execute("UPDATE ventas_diarias SET total = ? WHERE id = ?;", (total, int(venta_id)))

    def listar_items_venta(self, venta_id: int) -> list[sqlite3.Row]:
        return self._conn.execute(
            """
            SELECT id, nombre_producto, categoria, precio_unitario, cantidad, subtotal
            FROM detalle_ventas
            WHERE venta_id = ?
            ORDER BY id ASC;
            """,
            (int(venta_id),),
        ).fetchall()

    def borrar_item_detalle(self, detalle_id: int) -> None:
        # Nota: no reponemos stock en este MVP (se puede añadir luego).
        row = self._conn.execute(
            "SELECT venta_id FROM detalle_ventas WHERE id = ?;", (int(detalle_id),)
        ).fetchone()
        if row is None:
            return
        venta_id = int(row["venta_id"])
        self._conn.execute("DELETE FROM detalle_ventas WHERE id = ?;", (int(detalle_id),))
        self._recalcular_total_venta(venta_id)
        self._conn.commit()

    def borrar_venta(self, venta_id: int) -> None:
        self._conn.execute("DELETE FROM detalle_ventas WHERE venta_id = ?;", (int(venta_id),))
        self._conn.execute("DELETE FROM ventas_diarias WHERE id = ?;", (int(venta_id),))
        self._conn.commit()

    def finalizar_venta(self, venta_id: int) -> None:
        from datetime import datetime
        ahora = datetime.now().strftime("%H:%M")
        self._conn.execute(
            "UPDATE ventas_diarias SET pagado = 1, pagado_en = ? WHERE id = ?;",
            (ahora, int(venta_id)),
        )
        self._conn.commit()

    def reabrir_venta(self, venta_id: int) -> None:
        self._conn.execute(
            "UPDATE ventas_diarias SET pagado = 0 WHERE id = ?;", (int(venta_id),)
        )
        self._conn.commit()

    def listar_ventas_pagadas(self) -> list[sqlite3.Row]:
        return self._conn.execute(
            """
            SELECT id, mesa, total, pagado_en
            FROM ventas_diarias
            WHERE pagado = 1
            ORDER BY id DESC;
            """
        ).fetchall()

    # ---------- Reporte / cierre ----------
    def _query_resumen(self) -> tuple[list[sqlite3.Row], float]:
        rows = self._conn.execute(
            """
            SELECT
                d.nombre_producto AS producto,
                d.precio_unitario AS precio,
                SUM(d.cantidad) AS cantidad_total,
                GROUP_CONCAT(DISTINCT v.mesa) AS mesas,
                SUM(d.subtotal) AS total_producto
            FROM detalle_ventas d
            JOIN ventas_diarias v ON v.id = d.venta_id AND v.pagado = 1
            GROUP BY d.nombre_producto, d.precio_unitario
            ORDER BY total_producto DESC, producto ASC;
            """
        ).fetchall()
        gt = self._conn.execute(
            "SELECT COALESCE(SUM(total),0) AS gt FROM ventas_diarias WHERE pagado = 1;"
        ).fetchone()
        gran_total = float(gt["gt"]) if gt else 0.0
        return rows, gran_total

    def generar_reporte_csv(self, ruta_csv: Path) -> dict[str, Any]:
        """
        Retorna metadatos del reporte: {'gran_total': float, 'filas': int}
        """
        rows, gran_total = self._query_resumen()
        ruta_csv = Path(ruta_csv)
        ruta_csv.parent.mkdir(parents=True, exist_ok=True)

        with ruta_csv.open("w", encoding="utf-8", newline="") as f:
            import csv

            w = csv.writer(f)
            w.writerow(
                ["Producto", "Precio", "Cantidad total (hoy)", "Mesas", "Total acumulado (producto)"]
            )
            for r in rows:
                w.writerow(
                    [
                        r["producto"],
                        f"{float(r['precio']):.2f}",
                        int(r["cantidad_total"]),
                        r["mesas"] or "",
                        f"{float(r['total_producto']):.2f}",
                    ]
                )
            w.writerow(["Gran Total", "", "", "", f"{gran_total:.2f}"])

        return {"gran_total": gran_total, "filas": len(rows)}

    def obtener_resumen_diario_agrupado(self) -> tuple[list[sqlite3.Row], float]:
        return self._query_resumen()

    def limpiar_dia(self) -> None:
        self._conn.execute("DELETE FROM detalle_ventas;")
        self._conn.execute("DELETE FROM ventas_diarias;")
        self._conn.commit()

