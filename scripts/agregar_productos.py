import sqlite3

conn = sqlite3.connect('D:/Personal Projects/Cafeteria After-life/cafeteria.db')

conn.execute("INSERT INTO productos (nombre, categoria, precio_venta, usa_inventario, stock, es_agregado) VALUES ('Pan', 'Panaderia', 1.75, 0, 0, 0)")
conn.execute("INSERT INTO productos (nombre, categoria, precio_venta, usa_inventario, stock, es_agregado) VALUES ('Galleta', 'Snacks', 1.0, 0, 0, 0)")
conn.execute("INSERT INTO productos (nombre, categoria, precio_venta, usa_inventario, stock, es_agregado) VALUES ('Servicio', 'Servicios', 2.0, 0, 0, 0)")

conn.commit()
print("Productos de ejemplo agregados de nuevo")
conn.close()