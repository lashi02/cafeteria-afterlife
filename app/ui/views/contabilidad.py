from __future__ import annotations

from datetime import date
from pathlib import Path
from tkinter import messagebox
from tkinter import ttk

import customtkinter as ctk

from app.db import CafeDB


class ContabilidadView(ctk.CTkFrame):
    def __init__(self, master: ctk.CTkFrame, db: CafeDB) -> None:
        super().__init__(master)
        self.db = db

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        header = ctk.CTkFrame(self)
        header.grid(row=0, column=0, sticky="ew", padx=18, pady=(18, 8))
        header.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            header, text="Contabilidad", font=ctk.CTkFont(size=18, weight="bold")
        ).grid(row=0, column=0, padx=10, pady=10, sticky="w")

        self.btn_previsualizar = ctk.CTkButton(
            header, text="Generar pre-reporte (sin borrar)", command=self._pre_reporte
        )
        self.btn_previsualizar.grid(row=0, column=1, padx=10, pady=10, sticky="e")

        self.body = ctk.CTkFrame(self)
        self.body.grid(row=1, column=0, sticky="nsew", padx=18, pady=(8, 18))
        self.body.grid_columnconfigure(0, weight=1)
        self.body.grid_rowconfigure(1, weight=1)

        self.lbl = ctk.CTkLabel(self.body, text="", justify="left", anchor="w")
        self.lbl.grid(row=0, column=0, padx=14, pady=14, sticky="ew")

        table_frame = ctk.CTkFrame(self.body)
        table_frame.grid(row=1, column=0, padx=14, pady=(0, 14), sticky="nsew")
        table_frame.grid_columnconfigure(0, weight=1)
        table_frame.grid_rowconfigure(0, weight=1)

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", background="#2b2b2b", foreground="white", rowheight=40, fieldbackground="#2b2b2b", font=("TkDefaultFont", 20))
        style.configure("Treeview.Heading", background="#3a3a3a", foreground="white", font=("TkDefaultFont", 20, "bold"))
        style.map("Treeview", background=[("selected", "#1f6aa5")])

        self.table = ttk.Treeview(
            table_frame,
            columns=("producto", "precio", "cantidad", "total"),
            show="headings",
            selectmode="browse",
        )
        self.table.grid(row=0, column=0, sticky="nsew")

        self.table.heading("producto", text="Producto", anchor="w")
        self.table.heading("precio", text="Precio", anchor="e")
        self.table.heading("cantidad", text="Cantidad", anchor="center")
        self.table.heading("total", text="Total", anchor="e")

        self.table.column("producto", width=200, minwidth=140)
        self.table.column("precio", width=90, minwidth=70, anchor="e")
        self.table.column("cantidad", width=80, minwidth=60, anchor="center")
        self.table.column("total", width=100, minwidth=80, anchor="e")

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.table.yview)
        self.table.configure(yscrollcommand=scrollbar.set)
        scrollbar.grid(row=0, column=1, sticky="ns")

        self.refresh()

    def refresh(self) -> None:
        rows, gran_total = self.db.obtener_resumen_diario_agrupado()

        self.lbl.configure(text=f"Fecha: {date.today().isoformat()}   |   Gran total (hoy): {gran_total:.2f}")

        for item in self.table.get_children():
            self.table.delete(item)

        if not rows:
            self.table.insert("", "end", values=("Sin ventas registradas hoy", "", "", ""))
        else:
            for r in rows:
                self.table.insert(
                    "",
                    "end",
                    values=(
                        r["producto"],
                        f"{float(r['precio']):.2f}",
                        int(r["cantidad_total"]),
                        f"{float(r['total_producto']):.2f}",
                    )
                )

    def _pre_reporte(self) -> None:
        nombre = f"PreReporte_{date.today().isoformat()}.csv"
        ruta = Path(nombre)
        try:
            meta = self.db.generar_reporte_csv(ruta)
        except Exception as e:
            messagebox.showerror("Reporte", str(e))
            return
        messagebox.showinfo(
            "Pre-reporte generado",
            f"CSV generado (sin borrar ventas): {ruta.resolve()}\n"
            f"Productos agrupados: {meta['filas']}\n"
            f"Gran total: {meta['gran_total']:.2f}",
        )
