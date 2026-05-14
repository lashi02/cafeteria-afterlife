from __future__ import annotations

import time
from dataclasses import dataclass
from tkinter import messagebox

import customtkinter as ctk

from app.db import CafeDB, Producto


@dataclass
class MesaState:
    mesa: str
    venta_id: int
    tiempo_inicio: float


class MesasView(ctk.CTkFrame):
    def __init__(self, master: ctk.CTkFrame, db: CafeDB, on_cobrar: callable | None = None) -> None:
        super().__init__(master)
        self.db = db
        self.on_cobrar = on_cobrar
        self.mesas: dict[str, MesaState] = {}
        self.selected_mesa: str | None = None

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0)
        self.grid_rowconfigure(0, weight=1)

        self.body = ctk.CTkFrame(self)
        self.body.grid(row=0, column=0, sticky="nsew", padx=18, pady=(18, 18))
        self.body.grid_columnconfigure((0, 1, 2, 3), weight=1)
        self.body.grid_rowconfigure(0, weight=0)
        self.body.grid_rowconfigure(1, weight=1)

        header = ctk.CTkFrame(self.body)
        header.grid(row=0, column=0, sticky="ew", padx=0, pady=(0, 12))
        header.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            header, text="Salón", font=ctk.CTkFont(size=18, weight="bold")
        ).grid(row=0, column=0, padx=8, pady=8, sticky="w")

        self.btn_agregar_mesa = ctk.CTkButton(
            header, text="+ Nueva Mesa", width=120, command=self._abrir_mesa_custom
        )
        self.btn_agregar_mesa.grid(row=0, column=1, padx=6, pady=8, sticky="w")

        self.mesas_container = ctk.CTkFrame(self.body, fg_color="transparent")
        self.mesas_container.grid(row=1, column=0, sticky="nsew")
        for i in range(4):
            self.mesas_container.grid_columnconfigure(i, weight=1)

        self.mesa_btns: dict[str, ctk.CTkFrame] = {}
        self._mesas_fijas = ["Mesa 1", "Mesa 2", "Mesa 3", "Mesa 4", "Mesa 5", "Mesa 6", "Mesa 7", "Mesa 8"]

        self.sidebar = ctk.CTkFrame(self, width=320)
        self.sidebar.grid(row=0, column=1, sticky="nsew")
        self.sidebar.grid_rowconfigure(0, weight=0)
        self.sidebar.grid_rowconfigure(1, weight=0)
        self.sidebar.grid_rowconfigure(2, weight=1)

        self._build_sidebar()
        self._mostrar_sidebar_vacio()

        self._render_mesas_grid()
        self._iniciar_timer()

    def _build_sidebar(self) -> None:
        title_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        title_frame.grid(row=0, column=0, sticky="ew", padx=12, pady=(10, 6))
        title_frame.grid_columnconfigure(0, weight=1)

        self.sidebar_titulo = ctk.CTkLabel(
            title_frame, text="Selecciona una mesa", font=ctk.CTkFont(size=16, weight="bold")
        )
        self.sidebar_titulo.grid(row=0, column=0, sticky="w")

        self.sidebar_tiempo = ctk.CTkLabel(title_frame, text="", text_color="gray", font=ctk.CTkFont(size=12))
        self.sidebar_tiempo.grid(row=1, column=0, sticky="w", pady=(3, 0))

        btn_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        btn_frame.grid(row=1, column=0, sticky="ew", padx=12, pady=(6, 6))
        btn_frame.grid_columnconfigure(0, weight=1)
        btn_frame.grid_columnconfigure(1, weight=1)

        self.btn_agregar_sidebar = ctk.CTkButton(
            btn_frame, text="+ Producto", command=self._agregar_desde_sidebar, state="disabled"
        )
        self.btn_agregar_sidebar.grid(row=0, column=0, padx=(0, 4), pady=4, sticky="ew")

        self.btn_cerrar_sidebar = ctk.CTkButton(
            btn_frame,
            text="Cerrar Mesa",
            fg_color="#b23b3b",
            hover_color="#8d2f2f",
            command=self._cerrar_mesa_sidebar,
            state="disabled",
        )
        self.btn_cerrar_sidebar.grid(row=0, column=1, padx=(4, 0), pady=4, sticky="ew")

        self.sidebar_items = ctk.CTkScrollableFrame(self.sidebar)
        self.sidebar_items.grid(row=2, column=0, sticky="nsew", padx=12, pady=(6, 10))
        self.sidebar_item_rows: list[ctk.CTkFrame] = []

        footer = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        footer.grid(row=3, column=0, sticky="ew", padx=12, pady=(6, 10))
        footer.grid_columnconfigure(0, weight=1)

        self.lbl_total = ctk.CTkLabel(
            footer, text="Total: 0.00", font=ctk.CTkFont(size=18, weight="bold")
        )
        self.lbl_total.grid(row=0, column=0, pady=6)

    def _mostrar_sidebar_vacio(self) -> None:
        self.selected_mesa = None
        self.sidebar_titulo.configure(text="Selecciona una mesa")
        self.sidebar_tiempo.configure(text="")
        self.btn_agregar_sidebar.configure(state="disabled")
        self.btn_cerrar_sidebar.configure(state="disabled")

        for r in self.sidebar_item_rows:
            r.destroy()
        self.sidebar_item_rows.clear()

        self.lbl_total.configure(text="Total: 0.00")

    def _mostrar_sidebar_mesa(self, mesa: str) -> None:
        self.selected_mesa = mesa
        state = self.mesas[mesa]
        self.sidebar_titulo.configure(text=mesa)

        self._actualizar_sidebar()

    def _actualizar_sidebar(self) -> None:
        if not self.selected_mesa or self.selected_mesa not in self.mesas:
            self._mostrar_sidebar_vacio()
            return

        mesa = self.selected_mesa
        state = self.mesas[mesa]

        self.sidebar_tiempo.configure(text=f"Ocupada hace: {self._formatear_tiempo(state.tiempo_inicio)}")
        self.btn_agregar_sidebar.configure(state="normal")
        self.btn_cerrar_sidebar.configure(state="normal")

        for r in self.sidebar_item_rows:
            r.destroy()
        self.sidebar_item_rows.clear()

        items = self.db.listar_items_venta(state.venta_id)

        if not items:
            self.lbl_total.configure(text="Total: 0.00")
            return

        gran_total = 0.0
        for it in items:
            detalle_id = int(it["id"])
            nombre = str(it["nombre_producto"])
            precio = float(it["precio_unitario"])
            cantidad = int(it["cantidad"])
            subtotal = float(it["subtotal"])
            gran_total += subtotal

            row = ctk.CTkFrame(self.sidebar_items)
            row.pack(fill="x", padx=2, pady=4)
            row.grid_columnconfigure(0, weight=1)

            ctk.CTkLabel(
                row, text=nombre, anchor="w", font=ctk.CTkFont(size=11)
            ).grid(row=0, column=0, columnspan=3, padx=6, pady=(6, 2), sticky="ew")

            info_frame = ctk.CTkFrame(row, fg_color="transparent")
            info_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=6, pady=(0, 6))
            info_frame.grid_columnconfigure(0, weight=1)

            ctk.CTkLabel(
                info_frame,
                text=f"{cantidad} x {precio:.2f}",
                text_color="gray",
                font=ctk.CTkFont(size=10),
            ).pack(side="left")

            ctk.CTkLabel(
                info_frame,
                text=f"{subtotal:.2f}",
                font=ctk.CTkFont(size=12, weight="bold"),
            ).pack(side="right")

            ctk.CTkButton(
                row,
                text="Eliminar",
                width=60,
                height=24,
                fg_color="#b23b3b",
                hover_color="#8d2f2f",
                font=ctk.CTkFont(size=10),
                command=lambda did=detalle_id: self._eliminar_item_sidebar(did),
            ).grid(row=1, column=2, padx=(0, 6), pady=(0, 6), sticky="e")

            self.sidebar_item_rows.append(row)

        self.lbl_total.configure(text=f"Total: {gran_total:.2f}")

    def _eliminar_item_sidebar(self, detalle_id: int) -> None:
        if not messagebox.askyesno(
            "Eliminar producto",
            "¿Estás seguro de eliminar este producto de la mesa?\n"
            "El stock será restaurado automáticamente.",
        ):
            return
        try:
            self.db.borrar_item_detalle(detalle_id)
            self._render_mesas_grid()
            self._actualizar_sidebar()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo eliminar el producto.\n\n{e}")

    def _render_mesas_grid(self) -> None:
        for btn in self.mesa_btns.values():
            btn.destroy()
        self.mesa_btns.clear()

        mesas = self._mesas_fijas + [m for m in self.mesas.keys() if m not in self._mesas_fijas]

        if not mesas:
            ctk.CTkLabel(self.mesas_container, text="No hay mesas").grid(
                row=0, column=0, columnspan=4, pady=40
            )
            return

        for idx, mesa_nombre in enumerate(mesas):
            row = idx // 4
            col = idx % 4
            self._crear_mesa_card(mesa_nombre, row, col)

    def _crear_mesa_card(self, mesa_nombre: str, row: int, col: int) -> None:
        esta_abierta = mesa_nombre in self.mesas
        es_seleccionada = mesa_nombre == self.selected_mesa

        card = ctk.CTkFrame(
            self.mesas_container,
            fg_color="#2d8a2d" if esta_abierta else "#3b3b3b",
            border_width=3,
            border_color="#ffffff" if es_seleccionada else ("#1f5f1f" if esta_abierta else "#3b3b3b"),
        )
        card.grid(row=row, column=col, padx=8, pady=8, sticky="nsew")
        card.grid_rowconfigure(3, weight=1)

        def on_click(m=mesa_nombre):
            if m in self.mesas:
                self._mostrar_sidebar_mesa(m)

        card.bind("<Button-1>", lambda e, m=mesa_nombre: on_click(m))
        for child in card.winfo_children():
            child.bind("<Button-1>", lambda e, m=mesa_nombre: on_click(m))

        numero = mesa_nombre.replace("Mesa ", "")
        ctk.CTkLabel(
            card,
            text=f"Mesa {numero.zfill(2)}",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).grid(row=0, column=0, padx=10, pady=(12, 4))

        estado = "Ocupada" if esta_abierta else "Libre"
        color_estado = "#ff6b6b" if esta_abierta else "#6bff6b"
        ctk.CTkLabel(
            card, text=estado, text_color=color_estado, font=ctk.CTkFont(size=12)
        ).grid(row=1, column=0, padx=10, pady=(0, 4))

        lbl_tiempo = ctk.CTkLabel(card, text="", font=ctk.CTkFont(size=11), text_color="gray")
        lbl_tiempo.grid(row=2, column=0, padx=10, pady=(0, 4))
        if esta_abierta:
            lbl_tiempo.configure(text=self._formatear_tiempo(self.mesas[mesa_nombre].tiempo_inicio))
            items = self.db.listar_items_venta(self.mesas[mesa_nombre].venta_id)
            total = sum(float(it["subtotal"]) for it in items)
            count = sum(int(it["cantidad"]) for it in items)
            ctk.CTkLabel(
                card,
                text=f"{count} items | Total: {total:.2f}",
                font=ctk.CTkFont(size=14, weight="bold"),
            ).grid(row=3, column=0, padx=10, pady=(4, 8), sticky="s")

        btn_frame = ctk.CTkFrame(card, fg_color="transparent")
        btn_frame.grid(row=4, column=0, padx=10, pady=(0, 10))

        if esta_abierta:
            ctk.CTkButton(
                btn_frame,
                text="Agregar",
                width=65,
                command=lambda m=mesa_nombre: self._abrir_popup_productos(m),
            ).pack(side="left", padx=2)

            ctk.CTkButton(
                btn_frame,
                text="Cobrar",
                width=55,
                fg_color="#b23b3b",
                hover_color="#8d2f2f",
                command=lambda m=mesa_nombre: self._cobrar_mesa(m),
            ).pack(side="left", padx=2)
        else:
            ctk.CTkButton(
                btn_frame,
                text="Abrir",
                width=100,
                fg_color="#1f538d",
                command=lambda m=mesa_nombre: self._abrir_mesa(m),
            ).pack()

        self.mesa_btns[mesa_nombre] = card

    def _formatear_tiempo(self, tiempo_inicio: float) -> str:
        elapsed = int(time.time() - tiempo_inicio)
        if elapsed < 60:
            return f"{elapsed}s"
        elif elapsed < 3600:
            mins = elapsed // 60
            return f"{mins} min"
        else:
            hours = elapsed // 3600
            mins = (elapsed % 3600) // 60
            return f"{hours}h {mins}m"

    def _iniciar_timer(self) -> None:
        self._actualizar_tiempos()
        self.after(1000, self._iniciar_timer)

    def _actualizar_tiempos(self) -> None:
        if self.selected_mesa and self.selected_mesa in self.mesas:
            if self.sidebar_tiempo.winfo_exists():
                state = self.mesas[self.selected_mesa]
                self.sidebar_tiempo.configure(text=f"Ocupada hace: {self._formatear_tiempo(state.tiempo_inicio)}")

        for mesa_nombre, state in self.mesas.items():
            if mesa_nombre in self.mesa_btns:
                card = self.mesa_btns[mesa_nombre]
                for child in card.winfo_children():
                    if isinstance(child, ctk.CTkLabel):
                        texto = child.cget("text")
                        if "s" in texto or "min" in texto or "h" in texto:
                            child.configure(text=self._formatear_tiempo(state.tiempo_inicio))
                            break

    def _agregar_desde_sidebar(self) -> None:
        if self.selected_mesa:
            self._abrir_popup_productos(self.selected_mesa)

    def _cerrar_mesa_sidebar(self) -> None:
        if self.selected_mesa:
            self._cerrar_mesa(self.selected_mesa)

    def _abrir_mesa(self, mesa: str) -> None:
        if mesa not in self.mesas:
            venta_id = self.db.crear_venta(mesa)
            self.mesas[mesa] = MesaState(mesa=mesa, venta_id=venta_id, tiempo_inicio=time.time())
        self._render_mesas_grid()
        self._mostrar_sidebar_mesa(mesa)

    def _abrir_mesa_custom(self) -> None:
        dialog = ctk.CTkToplevel(self)
        dialog.title("Crear mesa")
        dialog.geometry("300x150")
        dialog.resizable(False, False)
        dialog.transient(self)

        ctk.CTkLabel(dialog, text="Nombre de la mesa:").pack(pady=(20, 5))
        var = ctk.StringVar()
        entry = ctk.CTkEntry(dialog, textvariable=var, width=200)
        entry.pack(pady=5)
        entry.focus()

        def accept():
            nombre = var.get().strip()
            if nombre:
                dialog.destroy()
                self._abrir_mesa(nombre)

        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(pady=15)
        btn_frame.grid_columnconfigure(0, weight=1)
        btn_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkButton(btn_frame, text="Cancelar", fg_color="#444", width=80, command=dialog.destroy).grid(
            row=0, column=0, padx=5
        )
        ctk.CTkButton(btn_frame, text="Crear", width=80, command=accept).grid(
            row=0, column=1, padx=5
        )

        dialog.bind("<Return>", lambda _: accept())
        dialog.grab_set()
        dialog.focus_force()

    def _abrir_popup_productos(self, mesa: str) -> None:
        if mesa not in self.mesas:
            self._abrir_mesa(mesa)

        dialog = ctk.CTkToplevel(self)
        dialog.title(f"Agregar consumo - {mesa}")
        dialog.geometry("500x500")
        dialog.transient(self)

        dialog.grid_columnconfigure(0, weight=1)
        dialog.grid_rowconfigure(3, weight=1)

        header = ctk.CTkFrame(dialog)
        header.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        ctk.CTkLabel(header, text=f"Productos para {mesa}", font=ctk.CTkFont(size=16, weight="bold")).pack()

        search_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        search_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 6))

        search_var = ctk.StringVar()
        ctk.CTkEntry(search_frame, placeholder_text="Buscar producto...", textvariable=search_var, width=280).pack(
            side="left", padx=(0, 8)
        )

        cat_var = ctk.StringVar(value="Todas")
        cat_menu = ctk.CTkOptionMenu(search_frame, values=["Todas"], variable=cat_var, width=140)
        cat_menu.pack(side="left")

        qty_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        qty_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=(0, 8))
        qty_frame.grid_columnconfigure(3, weight=1)

        ctk.CTkLabel(qty_frame, text="Cantidad:", font=ctk.CTkFont(size=13)).pack(side="left", padx=(0, 8))

        qty_var = ctk.IntVar(value=1)

        def _decrementar() -> None:
            v = qty_var.get()
            if v > 1:
                qty_var.set(v - 1)

        def _incrementar() -> None:
            qty_var.set(qty_var.get() + 1)

        btn_minus = ctk.CTkButton(qty_frame, text="−", width=32, height=32, command=_decrementar)
        btn_minus.pack(side="left", padx=(0, 4))

        qty_entry = ctk.CTkEntry(qty_frame, textvariable=qty_var, width=60, justify="center")
        qty_entry.pack(side="left", padx=(0, 4))

        btn_plus = ctk.CTkButton(qty_frame, text="+", width=32, height=32, command=_incrementar)
        btn_plus.pack(side="left")

        productos_frame = ctk.CTkScrollableFrame(dialog)
        productos_frame.grid(row=3, column=0, sticky="nsew", padx=10, pady=(0, 10))

        producto_btns: list[ctk.CTkButton] = []
        db = self.db

        def refresh_productos() -> None:
            cats = ["Todas"] + db.listar_categorias()
            if cat_var.get() not in cats:
                cat_var.set("Todas")
            cat_menu.configure(values=cats)

            for b in producto_btns:
                b.destroy()
            producto_btns.clear()

            productos = db.buscar_productos(texto=search_var.get(), categoria=cat_var.get())
            for p in productos:
                label = f"{p.nombre} — {p.precio_venta:.2f}"
                if p.usa_inventario:
                    label += f" (Stock: {p.stock})"
                btn = ctk.CTkButton(
                    productos_frame,
                    text=label,
                    anchor="w",
                    command=lambda prod=p: _agregar_producto(prod),
                )
                btn.pack(fill="x", padx=4, pady=4)
                producto_btns.append(btn)

        def _agregar_producto(p: Producto) -> None:
            if mesa not in self.mesas:
                return
            try:
                cantidad = int(qty_var.get())
                if cantidad < 1:
                    raise ValueError("La cantidad debe ser al menos 1.")
                if p.usa_inventario and cantidad > p.stock:
                    raise ValueError(f"Stock insuficiente para '{p.nombre}'. Disponible: {p.stock}.")
                self.db.agregar_item_a_venta(self.mesas[mesa].venta_id, p, cantidad=cantidad)
                self._render_mesas_grid()
                if self.selected_mesa == mesa:
                    self._actualizar_sidebar()
                dialog.destroy()
            except Exception as e:
                messagebox.showerror("Error", str(e))

        search_var.trace_add("write", lambda *_: refresh_productos())
        cat_var.trace_add("write", lambda *_: refresh_productos())
        refresh_productos()

        dialog.grab_set()

    def _cobrar_mesa(self, mesa: str) -> None:
        if mesa not in self.mesas:
            return
        items = self.db.listar_items_venta(self.mesas[mesa].venta_id)
        if not items:
            if messagebox.askyesno("Confirmar", f"{mesa} está vacía. ¿Cerrar sin cobrar?"):
                self.db.borrar_venta(self.mesas[mesa].venta_id)
                del self.mesas[mesa]
                self._render_mesas_grid()
                if self.selected_mesa == mesa:
                    self._mostrar_sidebar_vacio()
            return
        total = sum(float(it["subtotal"]) for it in items)
        if messagebox.askyesno("Confirmar", f"Cobrar {total:.2f} de {mesa}?"):
            self.db.finalizar_venta(self.mesas[mesa].venta_id)
            del self.mesas[mesa]
            self._render_mesas_grid()
            if self.selected_mesa == mesa:
                self._mostrar_sidebar_vacio()
            if self.on_cobrar:
                self.on_cobrar()
            messagebox.showinfo("Éxito", f"Mesa {mesa} cobrada: {total:.2f}")

    def _cerrar_mesa(self, mesa: str) -> None:
        if not messagebox.askyesno("Cerrar Mesa", f"Cerrar {mesa} sin cobrar?"):
            return
        if mesa in self.mesas:
            self.db.borrar_venta(self.mesas[mesa].venta_id)
            del self.mesas[mesa]
            self._render_mesas_grid()
            if self.selected_mesa == mesa:
                self._mostrar_sidebar_vacio()

    def reabrir_mesa(self, mesa: str, venta_id: int) -> None:
        if mesa in self.mesas:
            messagebox.showwarning("Reabrir", f"{mesa} ya está abierta.")
            return
        self.mesas[mesa] = MesaState(mesa=mesa, venta_id=venta_id, tiempo_inicio=time.time())
        self._render_mesas_grid()
        self._mostrar_sidebar_mesa(mesa)

    def refresh(self) -> None:
        self._render_mesas_grid()
        self._actualizar_sidebar()