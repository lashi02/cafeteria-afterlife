import sqlite3

conn = sqlite3.connect('D:/Personal Projects/Cafeteria After-life/cafeteria.db')

conn.execute("DELETE FROM detalle_ventas")
conn.execute("DELETE FROM ventas_diarias")
conn.commit()
print("Limpiado todo")
conn.close()