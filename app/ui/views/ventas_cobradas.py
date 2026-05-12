from __future__ import annotations

from tkinter import messagebox
from tkinter import ttk

import customtkinter as ctk

from app.db import CafeDB


class VentasCobradasView(ctk.CTkFrame):
    def __init__(self, master: ctk.CTkFrame, db: CafeDB, on_reabrir: callable | None = None) -> None:
        super().__init__(master)
        self.db = db
        self.on_reabrir = on_reabrir

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        header = ctk.CTkFrame(self)
        header.grid(row=0, column=0, sticky="ew", padx=18, pady=(18, 8))
        header.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            header, text="Ventas cobradas", font=ctk.CTkFont(size=18, weight="bold")
        ).grid(row=0, column=0, padx=10, pady=10, sticky="w")

        self.lbl_total = ctk.CTkLabel(
            header, text="", font=ctk.CTkFont(size=13), text_color="gray"
        )
        self.lbl_total.grid(row=0, column=1, padx=10, pady=10, sticky="e")

        self.scroll = ctk.CTkScrollableFrame(self)
        self.scroll.grid(row=1, column=0, sticky="nsew", padx=18, pady=(8, 18))
        self.rows: list[ctk.CTkFrame] = []

        self.refresh()

    def refresh(self) -> None:
        for r in self.rows:
            r.destroy()
        self.rows.clear()

        pagadas = self.db.listar_ventas_pagadas()
        total_general = sum(float(v["total"]) for v in pagadas)
        self.lbl_total.configure(text=f"Total cobrado: {total_general:.2f}")

        if not pagadas:
            lbl = ctk.CTkLabel(self.scroll, text="No hay ventas cobradas", text_color="gray", font=ctk.CTkFont(size=14))
            lbl.pack(pady=40)
            self.rows.append(lbl)
            return

        for v in pagadas:
            row = ctk.CTkFrame(self.scroll)
            row.pack(fill="x", padx=6, pady=5)
            row.grid_columnconfigure(0, weight=1)

            hora = v["pagado_en"] or ""
            info = f"{v['mesa']}  —  {float(v['total']):.2f}"
            if hora:
                info += f"  —  {hora}"

            ctk.CTkLabel(
                row,
                text=info,
                anchor="w",
                font=ctk.CTkFont(size=13),
            ).grid(row=0, column=0, padx=14, pady=10, sticky="ew")

            btn_frame = ctk.CTkFrame(row, fg_color="transparent")
            btn_frame.grid(row=0, column=1, padx=8, pady=6)

            ctk.CTkButton(
                btn_frame,
                text="Ver",
                width=60,
                command=lambda vid=v["id"]: self._ver_detalle(vid),
            ).pack(side="left", padx=2)

            ctk.CTkButton(
                btn_frame,
                text="Reabrir",
                width=70,
                fg_color="#d4a017",
                hover_color="#b8890f",
                command=lambda vid=v["id"], mesa=v["mesa"]: self._reabrir(vid, mesa),
            ).pack(side="left", padx=2)

            self.rows.append(row)

    def _ver_detalle(self, venta_id: int) -> None:
        items = self.db.listar_items_venta(venta_id)
        if not items:
            messagebox.showinfo("Detalle", "Esta venta no tiene productos registrados.")
            return

        dialog = ctk.CTkToplevel(self)
        dialog.title("Detalle de venta")
        dialog.geometry("550x400")
        dialog.transient(self)

        dialog.grid_columnconfigure(0, weight=1)
        dialog.grid_rowconfigure(1, weight=1)

        header = ctk.CTkFrame(dialog)
        header.grid(row=0, column=0, sticky="ew", padx=12, pady=12)
        ctk.CTkLabel(
            header, text="Productos de la venta", font=ctk.CTkFont(size=15, weight="bold")
        ).pack()

        frame = ctk.CTkFrame(dialog)
        frame.grid(row=1, column=0, sticky="nsew", padx=12, pady=(0, 12))
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(0, weight=1)

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", background="#2b2b2b", foreground="white", rowheight=26, fieldbackground="#2b2b2b")
        style.configure("Treeview.Heading", background="#3a3a3a", foreground="white", font=("TkDefaultFont", 9, "bold"))
        style.map("Treeview", background=[("selected", "#1f6aa5")])

        table = ttk.Treeview(
            frame,
            columns=("producto", "categoria", "precio", "cantidad", "subtotal"),
            show="headings",
            selectmode="browse",
        )
        table.grid(row=0, column=0, sticky="nsew")

        table.heading("producto", text="Producto", anchor="w")
        table.heading("categoria", text="Categoría", anchor="w")
        table.heading("precio", text="P/U", anchor="e")
        table.heading("cantidad", text="Cant", anchor="center")
        table.heading("subtotal", text="Subtotal", anchor="e")

        table.column("producto", width=160, minwidth=100)
        table.column("categoria", width=100, minwidth=70)
        table.column("precio", width=70, minwidth=50, anchor="e")
        table.column("cantidad", width=50, minwidth=40, anchor="center")
        table.column("subtotal", width=80, minwidth=60, anchor="e")

        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=table.yview)
        table.configure(yscrollcommand=scrollbar.set)
        scrollbar.grid(row=0, column=1, sticky="ns")

        total = 0.0
        for it in items:
            subtotal = float(it["subtotal"])
            total += subtotal
            table.insert(
                "",
                "end",
                values=(
                    it["nombre_producto"],
                    it["categoria"],
                    f"{float(it['precio_unitario']):.2f}",
                    int(it["cantidad"]),
                    f"{subtotal:.2f}",
                ),
            )

        table.insert("", "end", values=("", "", "", "Total:", f"{total:.2f}"))

        ctk.CTkButton(dialog, text="Cerrar", command=dialog.destroy).grid(
            row=2, column=0, pady=(0, 12)
        )

        dialog.grab_set()

    def _reabrir(self, venta_id: int, mesa: str) -> None:
        if self.on_reabrir:
            self.on_reabrir(venta_id, mesa)
