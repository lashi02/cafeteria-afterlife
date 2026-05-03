from __future__ import annotations

from tkinter import messagebox

import customtkinter as ctk

from app.db import CafeDB, Producto


class AddProductoDialog(ctk.CTkToplevel):
    def __init__(self, master: ctk.CTkFrame, db: CafeDB, on_saved: callable) -> None:
        super().__init__(master)
        self.db = db
        self.on_saved = on_saved

        self.title("Agregar producto")
        self.geometry("520x420")
        self.resizable(False, False)

        self.grid_columnconfigure(1, weight=1)

        self.nombre_var = ctk.StringVar(value="")
        self.categoria_var = ctk.StringVar(value="")
        self.precio_var = ctk.StringVar(value="")
        self.stock_var = ctk.StringVar(value="")

        pad_x = 18
        pad_y = 10

        ctk.CTkLabel(self, text="Nuevo producto", font=ctk.CTkFont(size=18, weight="bold")).grid(
            row=0, column=0, columnspan=2, padx=pad_x, pady=(18, 12), sticky="w"
        )

        ctk.CTkLabel(self, text="Nombre").grid(row=1, column=0, padx=pad_x, pady=pad_y, sticky="w")
        ctk.CTkEntry(self, textvariable=self.nombre_var, placeholder_text="Ej: Latte").grid(
            row=1, column=1, padx=pad_x, pady=pad_y, sticky="ew"
        )

        ctk.CTkLabel(self, text="Categoría").grid(row=2, column=0, padx=pad_x, pady=pad_y, sticky="w")
        # Campo libre + sugerencias (categorías ya existentes)
        categorias_existentes = self.db.listar_categorias()
        if not categorias_existentes:
            categorias_existentes = ["(sin categorías aún)"]

        def aplicar_categoria(sel: str) -> None:
            if sel and sel != "(sin categorías aún)":
                self.categoria_var.set(sel)

        cat_row = ctk.CTkFrame(self, fg_color="transparent")
        cat_row.grid(row=2, column=1, padx=pad_x, pady=pad_y, sticky="ew")
        cat_row.grid_columnconfigure(0, weight=1)

        ctk.CTkEntry(cat_row, textvariable=self.categoria_var, placeholder_text="Escribe una categoría...").grid(
            row=0, column=0, padx=(0, 10), pady=0, sticky="ew"
        )
        self.categoria_picker = ctk.CTkOptionMenu(
            cat_row,
            values=categorias_existentes,
            command=aplicar_categoria,
            width=190,
        )
        self.categoria_picker.grid(row=0, column=1, sticky="e")
        self.categoria_picker.set("Elegir existente…")

        ctk.CTkLabel(self, text="Precio de venta").grid(row=3, column=0, padx=pad_x, pady=pad_y, sticky="w")
        ctk.CTkEntry(self, textvariable=self.precio_var, placeholder_text="Ej: 2.50").grid(
            row=3, column=1, padx=pad_x, pady=pad_y, sticky="ew"
        )

        ctk.CTkLabel(self, text="Stock (opcional)").grid(row=4, column=0, padx=pad_x, pady=pad_y, sticky="w")
        ctk.CTkEntry(self, textvariable=self.stock_var, placeholder_text="Vacío = no usa inventario").grid(
            row=4, column=1, padx=pad_x, pady=pad_y, sticky="ew"
        )

        footer = ctk.CTkFrame(self)
        footer.grid(row=5, column=0, columnspan=2, padx=pad_x, pady=(18, 18), sticky="ew")
        footer.grid_columnconfigure(0, weight=1)
        footer.grid_columnconfigure(1, weight=1)

        ctk.CTkButton(footer, text="Cancelar", fg_color="#444", hover_color="#333", command=self.destroy).grid(
            row=0, column=0, padx=10, pady=12, sticky="ew"
        )
        ctk.CTkButton(footer, text="Guardar", command=self._guardar).grid(
            row=0, column=1, padx=10, pady=12, sticky="ew"
        )

        self.grab_set()
        self.focus_force()

    def _guardar(self) -> None:
        try:
            stock_txt = (self.stock_var.get() or "").strip()
            usa_inventario = bool(stock_txt)
            stock = int(stock_txt) if stock_txt else 0
            self.db.crear_producto(
                nombre=self.nombre_var.get(),
                categoria=self.categoria_var.get(),
                precio_venta=float(self.precio_var.get().strip().replace(",", ".")),
                usa_inventario=usa_inventario,
                stock=stock,
            )
        except Exception as e:
            messagebox.showerror("Agregar producto", str(e))
            return

        try:
            self.on_saved()
        finally:
            self.destroy()


class EditProductoDialog(ctk.CTkToplevel):
    def __init__(self, master: ctk.CTkFrame, db: CafeDB, producto: Producto, on_saved: callable) -> None:
        super().__init__(master)
        self.db = db
        self.producto = producto
        self.on_saved = on_saved

        self.title("Editar producto")
        self.geometry("520x420")
        self.resizable(False, False)

        self.grid_columnconfigure(1, weight=1)

        self.nombre_var = ctk.StringVar(value=producto.nombre)
        self.categoria_var = ctk.StringVar(value=producto.categoria)
        self.precio_var = ctk.StringVar(value=f"{producto.precio_venta:.2f}")
        self.stock_var = ctk.StringVar(value=str(producto.stock) if producto.usa_inventario else "")

        pad_x = 18
        pad_y = 10

        ctk.CTkLabel(self, text="Editar producto", font=ctk.CTkFont(size=18, weight="bold")).grid(
            row=0, column=0, columnspan=2, padx=pad_x, pady=(18, 12), sticky="w"
        )

        ctk.CTkLabel(self, text="Nombre").grid(row=1, column=0, padx=pad_x, pady=pad_y, sticky="w")
        ctk.CTkEntry(self, textvariable=self.nombre_var).grid(row=1, column=1, padx=pad_x, pady=pad_y, sticky="ew")

        ctk.CTkLabel(self, text="Categoría").grid(row=2, column=0, padx=pad_x, pady=pad_y, sticky="w")
        categorias_existentes = self.db.listar_categorias()
        if not categorias_existentes:
            categorias_existentes = ["(sin categorías aún)"]

        def aplicar_categoria(sel: str) -> None:
            if sel and sel != "(sin categorías aún)":
                self.categoria_var.set(sel)

        cat_row = ctk.CTkFrame(self, fg_color="transparent")
        cat_row.grid(row=2, column=1, padx=pad_x, pady=pad_y, sticky="ew")
        cat_row.grid_columnconfigure(0, weight=1)
        ctk.CTkEntry(cat_row, textvariable=self.categoria_var, placeholder_text="Escribe una categoría...").grid(
            row=0, column=0, padx=(0, 10), pady=0, sticky="ew"
        )
        picker = ctk.CTkOptionMenu(cat_row, values=categorias_existentes, command=aplicar_categoria, width=190)
        picker.grid(row=0, column=1, sticky="e")
        picker.set("Elegir existente…")

        ctk.CTkLabel(self, text="Precio de venta").grid(row=3, column=0, padx=pad_x, pady=pad_y, sticky="w")
        ctk.CTkEntry(self, textvariable=self.precio_var, placeholder_text="Ej: 2.50").grid(
            row=3, column=1, padx=pad_x, pady=pad_y, sticky="ew"
        )

        ctk.CTkLabel(self, text="Stock (opcional)").grid(row=4, column=0, padx=pad_x, pady=pad_y, sticky="w")
        ctk.CTkEntry(self, textvariable=self.stock_var, placeholder_text="Vacío = no usa inventario").grid(
            row=4, column=1, padx=pad_x, pady=pad_y, sticky="ew"
        )

        footer = ctk.CTkFrame(self)
        footer.grid(row=5, column=0, columnspan=2, padx=pad_x, pady=(18, 18), sticky="ew")
        footer.grid_columnconfigure(0, weight=1)
        footer.grid_columnconfigure(1, weight=1)

        ctk.CTkButton(footer, text="Cancelar", fg_color="#444", hover_color="#333", command=self.destroy).grid(
            row=0, column=0, padx=10, pady=12, sticky="ew"
        )
        ctk.CTkButton(footer, text="Guardar cambios", command=self._guardar).grid(
            row=0, column=1, padx=10, pady=12, sticky="ew"
        )

        self.grab_set()
        self.focus_force()

    def _guardar(self) -> None:
        try:
            stock_txt = (self.stock_var.get() or "").strip()
            usa_inventario = bool(stock_txt)
            stock = int(stock_txt) if stock_txt else 0
            self.db.actualizar_producto(
                producto_id=self.producto.id,
                nombre=self.nombre_var.get(),
                categoria=self.categoria_var.get(),
                precio_venta=float(self.precio_var.get().strip().replace(",", ".")),
                usa_inventario=usa_inventario,
                stock=stock,
            )
        except Exception as e:
            messagebox.showerror("Editar producto", str(e))
            return

        try:
            self.on_saved()
        finally:
            self.destroy()


class InventarioMenuView(ctk.CTkFrame):
    def __init__(self, master: ctk.CTkFrame, db: CafeDB) -> None:
        super().__init__(master)
        self.db = db
        self.page = 0
        self.page_size = 50

        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        header = ctk.CTkFrame(self)
        header.grid(row=0, column=0, sticky="ew", padx=18, pady=(18, 8))
        header.grid_columnconfigure(4, weight=1)

        ctk.CTkLabel(
            header, text="Inventario / Menú", font=ctk.CTkFont(size=18, weight="bold")
        ).grid(row=0, column=0, padx=10, pady=10, sticky="w")

        self.search_var = ctk.StringVar(value="")
        entry = ctk.CTkEntry(header, placeholder_text="Buscar...", textvariable=self.search_var, width=200)
        entry.grid(row=0, column=1, padx=10, pady=10, sticky="w")
        self.search_var.trace_add("write", lambda *_: self._on_filter_change())

        self.cat_var = ctk.StringVar(value="Todas")
        self.cat_menu = ctk.CTkOptionMenu(
            header,
            values=["Todas"],
            variable=self.cat_var,
            width=160,
            command=lambda *_: self._on_filter_change(),
        )
        self.cat_menu.grid(row=0, column=2, padx=10, pady=10, sticky="w")

        btn_add = ctk.CTkButton(header, text="+ Agregar", command=self._abrir_agregar_producto)
        btn_add.grid(row=0, column=3, padx=10, pady=10, sticky="e")

        cols = ctk.CTkFrame(self)
        cols.grid(row=1, column=0, sticky="ew", padx=18, pady=(0, 6))
        cols.grid_columnconfigure(1, weight=1)

        hdr_font = ctk.CTkFont(size=12, weight="bold")
        ctk.CTkLabel(cols, text="Categoría", font=hdr_font, width=110, anchor="w").grid(
            row=0, column=0, padx=16, pady=8, sticky="w"
        )
        ctk.CTkLabel(cols, text="Nombre", font=hdr_font, anchor="w").grid(
            row=0, column=1, padx=10, pady=8, sticky="w"
        )
        ctk.CTkLabel(cols, text="Precio", font=hdr_font, width=90, anchor="e").grid(
            row=0, column=2, padx=(6, 10), pady=8, sticky="e"
        )
        ctk.CTkLabel(cols, text="Stock", font=hdr_font, width=110, anchor="e").grid(
            row=0, column=3, padx=(6, 10), pady=8, sticky="e"
        )
        ctk.CTkLabel(cols, text="Editar", font=hdr_font, width=60, anchor="e").grid(
            row=0, column=4, padx=(0, 10), pady=8, sticky="e"
        )

        self.frame = ctk.CTkScrollableFrame(self)
        self.frame.grid(row=2, column=0, sticky="nsew", padx=18, pady=(0, 18))
        self.rows: list[ctk.CTkFrame] = []

        pagination = ctk.CTkFrame(self)
        pagination.grid(row=3, column=0, sticky="ew", padx=18, pady=(0, 10))
        pagination.grid_columnconfigure(0, weight=1)

        self.lbl_page = ctk.CTkLabel(pagination, text="")
        self.lbl_page.grid(row=0, column=0, padx=10, pady=5)

        self.btn_prev = ctk.CTkButton(pagination, text="< Anterior", width=100, command=self._prev_page)
        self.btn_prev.grid(row=0, column=1, padx=5, pady=5)

        self.btn_next = ctk.CTkButton(pagination, text="Siguiente >", width=100, command=self._next_page)
        self.btn_next.grid(row=0, column=2, padx=5, pady=5)

        self.all_productos: list[Producto] = []
        self.refresh()

    def _on_filter_change(self) -> None:
        self.page = 0
        self.refresh()

    def _update_categorias(self) -> None:
        cats = ["Todas"] + self.db.listar_categorias()
        actual = self.cat_var.get() or "Todas"
        if actual not in cats:
            self.cat_var.set("Todas")
        self.cat_menu.configure(values=cats)

    def _prev_page(self) -> None:
        if self.page > 0:
            self.page -= 1
            self.refresh()

    def _next_page(self) -> None:
        total_pages = (len(self.all_productos) + self.page_size - 1) // self.page_size
        if self.page < total_pages - 1:
            self.page += 1
            self.refresh()

    def _abrir_agregar_producto(self) -> None:
        AddProductoDialog(self, self.db, on_saved=self.refresh)

    def refresh(self) -> None:
        self._update_categorias()

        for r in self.rows:
            r.destroy()
        self.rows.clear()

        categoria = self.cat_var.get() if self.cat_var.get() != "Todas" else None
        self.all_productos = self.db.buscar_productos(texto=self.search_var.get(), categoria=categoria)

        start = self.page * self.page_size
        end = start + self.page_size
        page_products = self.all_productos[start:end]

        for p in page_products:
            self._add_row(p)

        total = len(self.all_productos)
        start_show = start + 1 if total > 0 else 0
        end_show = min(end, total)
        self.lbl_page.configure(text=f"Mostrando {start_show}-{end_show} de {total} productos")
        self.btn_prev.configure(state="normal" if self.page > 0 else "disabled")
        self.btn_next.configure(state="normal" if end < total else "disabled")

    def _add_row(self, p: Producto) -> None:
        row = ctk.CTkFrame(self.frame)
        row.pack(fill="x", padx=6, pady=6)
        row.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(row, text=p.categoria, width=110, anchor="w").grid(row=0, column=0, padx=10, pady=10, sticky="w")

        ctk.CTkLabel(row, text=p.nombre, anchor="w").grid(row=0, column=1, padx=10, pady=10, sticky="ew")
        ctk.CTkLabel(row, text=f"{p.precio_venta:.2f}", width=90, anchor="e").grid(
            row=0, column=2, padx=(6, 10), pady=10, sticky="e"
        )

        stock_txt = str(p.stock) if p.usa_inventario else "—"
        stock_color = "red" if p.usa_inventario and p.stock <= 5 else ("orange" if p.usa_inventario and p.stock <= 10 else "white")
        lbl_stock = ctk.CTkLabel(row, text=stock_txt, width=110, anchor="e", text_color=stock_color)
        lbl_stock.grid(row=0, column=3, padx=(6, 10), pady=10, sticky="e")

        btn_edit = ctk.CTkButton(
            row,
            text="✏️",
            width=44,
            command=lambda prod=p: EditProductoDialog(self, self.db, prod, on_saved=self.refresh),
        )
        btn_edit.grid(row=0, column=4, padx=(0, 10), pady=10, sticky="e")

        self.rows.append(row)

