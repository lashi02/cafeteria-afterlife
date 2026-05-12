from __future__ import annotations

from datetime import date
from pathlib import Path
from tkinter import messagebox

import customtkinter as ctk

from app.db import CafeDB
from app.ui.views.contabilidad import ContabilidadView
from app.ui.views.inventario_menu import InventarioMenuView
from app.ui.views.mesas import MesasView
from app.ui.views.ventas_cobradas import VentasCobradasView


class CafeApp(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.title("Cafeteria After-life")
        self.geometry("1100x700")
        self.minsize(980, 620)

        self.db = CafeDB()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        self._build_layout()

    def _build_layout(self) -> None:
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.sidebar = ctk.CTkFrame(self, width=210, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsw")
        self.sidebar.grid_rowconfigure(10, weight=1)

        title = ctk.CTkLabel(
            self.sidebar, text="Panel de Control", font=ctk.CTkFont(size=18, weight="bold")
        )
        title.grid(row=0, column=0, padx=16, pady=(18, 12), sticky="w")

        self.btn_mesas = ctk.CTkButton(self.sidebar, text="Mesas", command=self._show_mesas)
        self.btn_mesas.grid(row=1, column=0, padx=16, pady=8, sticky="ew")

        self.btn_inventario = ctk.CTkButton(
            self.sidebar, text="Inventario/Menú", command=self._show_inventario
        )
        self.btn_inventario.grid(row=2, column=0, padx=16, pady=8, sticky="ew")

        self.btn_conta = ctk.CTkButton(
            self.sidebar, text="Contabilidad", command=self._show_contabilidad
        )
        self.btn_conta.grid(row=3, column=0, padx=16, pady=8, sticky="ew")

        self.btn_ventas = ctk.CTkButton(
            self.sidebar, text="Ventas cobradas", command=self._show_ventas_cobradas
        )
        self.btn_ventas.grid(row=4, column=0, padx=16, pady=8, sticky="ew")

        self.btn_cierre = ctk.CTkButton(
            self.sidebar,
            text="Cierre de Día",
            fg_color="#b23b3b",
            hover_color="#8d2f2f",
            command=self._cierre_de_dia,
        )
        self.btn_cierre.grid(row=9, column=0, padx=16, pady=(8, 18), sticky="ew")

        self.content = ctk.CTkFrame(self, corner_radius=0)
        self.content.grid(row=0, column=1, sticky="nsew")
        self.content.grid_rowconfigure(0, weight=1)
        self.content.grid_columnconfigure(0, weight=1)

        self.view_mesas = MesasView(self.content, self.db, on_cobrar=self._on_mesa_cobrada)
        self.view_inventario = InventarioMenuView(self.content, self.db)
        self.view_conta = ContabilidadView(self.content, self.db)
        self.view_ventas = VentasCobradasView(self.content, self.db, on_reabrir=self._on_reabrir_mesa)

        self._show_mesas()

    def _on_mesa_cobrada(self) -> None:
        self.view_conta.refresh()
        self.view_ventas.refresh()

    def _on_reabrir_mesa(self, venta_id: int, mesa: str) -> None:
        self.db.reabrir_venta(venta_id)
        self.view_mesas.reabrir_mesa(mesa, venta_id)
        self._show_mesas()

    def _clear_content(self) -> None:
        for child in self.content.winfo_children():
            child.grid_forget()

    def _show_mesas(self) -> None:
        self._clear_content()
        self.view_mesas.grid(row=0, column=0, sticky="nsew")

    def _show_inventario(self) -> None:
        self._clear_content()
        self.view_inventario.refresh()
        self.view_inventario.grid(row=0, column=0, sticky="nsew")

    def _show_contabilidad(self) -> None:
        self._clear_content()
        self.view_conta.refresh()
        self.view_conta.grid(row=0, column=0, sticky="nsew")

    def _show_ventas_cobradas(self) -> None:
        self._clear_content()
        self.view_ventas.refresh()
        self.view_ventas.grid(row=0, column=0, sticky="nsew")

    def _cierre_de_dia(self) -> None:
        if not messagebox.askyesno(
            "Cierre de Día",
            "Esto generará el reporte CSV y borrará las ventas del día (NO borra productos). ¿Continuar?",
        ):
            return

        nombre = f"Reporte_{date.today().isoformat()}.csv"
        ruta = Path(nombre)

        try:
            meta = self.db.generar_reporte_csv(ruta)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo generar el reporte.\n\n{e}")
            return

        # Respaldo: confirmar que el CSV existe y tiene contenido
        if not (ruta.exists() and ruta.is_file() and ruta.stat().st_size > 0):
            messagebox.showerror(
                "Error",
                "El CSV no se creó correctamente. Se cancela el borrado por seguridad.",
            )
            return

        try:
            self.db.limpiar_dia()
        except Exception as e:
            messagebox.showerror("Error", f"El reporte se creó, pero falló la limpieza.\n\n{e}")
            return

        messagebox.showinfo(
            "Cierre completado",
            f"Reporte generado: {ruta.resolve()}\n"
            f"Productos agrupados: {meta['filas']}\n"
            f"Gran total: {meta['gran_total']:.2f}",
        )
        self.view_mesas.refresh()
        self.view_conta.refresh()
        self.view_ventas.refresh()

    def _on_close(self) -> None:
        try:
            self.db.close()
        finally:
            self.destroy()

