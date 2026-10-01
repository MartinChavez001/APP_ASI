"""
Sistema de Gestión de Turnos - Grupo 3: Administración
Prototipo v1 (Python + Tkinter, sin dependencias externas)

Funciones:
  - Consultar turnos en una tabla
  - Filtrar por especialidad, profesional, estado y texto (paciente)
  - Ver cantidad de turnos e indicadores (total, atendidos, cancelados, pendientes, % cancelación)
  - Identificar cancelaciones (filas en rojo)
  - Cambiar el estado de un turno seleccionado (para probar los indicadores)
"""

import random
import tkinter as tk
from datetime import date, datetime, timedelta
from tkinter import ttk, messagebox

# ----------------------------------------------------------------------
# Datos de ejemplo (en un sistema real vendrían de una base de datos)
# ----------------------------------------------------------------------
PROFESIONALES = [
    ("Dra. Laura Gómez", "Clínica médica"),
    ("Dr. Martín Pérez", "Clínica médica"),
    ("Dra. Sofía Ramírez", "Pediatría"),
    ("Dr. Andrés Torres", "Cardiología"),
    ("Dra. Carolina Díaz", "Dermatología"),
    ("Dr. Javier Suárez", "Traumatología"),
]

PACIENTES = [
    "Ana López", "Bruno Fernández", "Camila Ruiz", "Diego Morales",
    "Elena Castro", "Facundo Silva", "Gabriela Núñez", "Hernán Ortiz",
    "Inés Vega", "Julián Rojas", "Karina Molina", "Lucas Herrera",
    "Marina Acosta", "Nicolás Benítez", "Olivia Paz", "Pablo Medina",
]

ESTADOS = ("Atendido", "Cancelado", "Pendiente")
TODOS = "Todos"


def generar_turnos(cantidad=48, semilla=7):
    """Genera turnos de ejemplo. Con semilla fija para que sea reproducible."""
    rnd = random.Random(semilla)
    hoy = date.today()
    turnos = []
    for i in range(1, cantidad + 1):
        profesional, especialidad = rnd.choice(PROFESIONALES)
        dia = hoy + timedelta(days=rnd.randint(-14, 7))
        hora = f"{rnd.randint(8, 17):02d}:{rnd.choice(['00', '20', '40'])}"
        # Turnos pasados: atendidos o cancelados. Futuros: pendientes.
        if dia < hoy:
            estado = rnd.choices(["Atendido", "Cancelado"], weights=[80, 20])[0]
        elif dia == hoy:
            estado = rnd.choice(ESTADOS)
        else:
            estado = rnd.choices(["Pendiente", "Cancelado"], weights=[85, 15])[0]
        turnos.append({
            "id": i,
            "fecha": dia,
            "hora": hora,
            "paciente": rnd.choice(PACIENTES),
            "profesional": profesional,
            "especialidad": especialidad,
            "estado": estado,
        })
    turnos.sort(key=lambda t: (t["fecha"], t["hora"]))
    return turnos


# ----------------------------------------------------------------------
# Lógica (separada de la interfaz para poder probarla fácilmente)
# ----------------------------------------------------------------------
def filtrar_turnos(turnos, especialidad=TODOS, profesional=TODOS,
                   estado=TODOS, texto=""):
    texto = texto.strip().lower()
    resultado = []
    for t in turnos:
        if especialidad != TODOS and t["especialidad"] != especialidad:
            continue
        if profesional != TODOS and t["profesional"] != profesional:
            continue
        if estado != TODOS and t["estado"] != estado:
            continue
        if texto and texto not in t["paciente"].lower():
            continue
        resultado.append(t)
    return resultado


def calcular_indicadores(turnos):
    total = len(turnos)
    atendidos = sum(1 for t in turnos if t["estado"] == "Atendido")
    cancelados = sum(1 for t in turnos if t["estado"] == "Cancelado")
    pendientes = sum(1 for t in turnos if t["estado"] == "Pendiente")
    pct_cancel = (cancelados / total * 100) if total else 0.0
    return {
        "total": total,
        "atendidos": atendidos,
        "cancelados": cancelados,
        "pendientes": pendientes,
        "pct_cancelacion": pct_cancel,
    }


# ----------------------------------------------------------------------
# Interfaz
# ----------------------------------------------------------------------
class AppTurnos(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Gestión de Turnos - Administración")
        self.geometry("980x620")
        self.minsize(820, 500)

        self.turnos = generar_turnos()

        self.var_especialidad = tk.StringVar(value=TODOS)
        self.var_profesional = tk.StringVar(value=TODOS)
        self.var_estado = tk.StringVar(value=TODOS)
        self.var_texto = tk.StringVar()

        self._crear_widgets()
        self._actualizar_profesionales()
        self.actualizar_vista()

    # ---------- construcción de la interfaz ----------
    def _crear_widgets(self):
        # Indicadores
        marco_ind = ttk.LabelFrame(self, text="Indicadores")
        marco_ind.pack(fill="x", padx=10, pady=(10, 5))
        self.lbl_indicadores = ttk.Label(marco_ind, font=("Segoe UI", 12, "bold"))
        self.lbl_indicadores.pack(anchor="w", padx=10, pady=(6, 2))
        self.lbl_porcentaje = ttk.Label(marco_ind)
        self.lbl_porcentaje.pack(anchor="w", padx=10, pady=(0, 6))

        # Filtros
        marco_f = ttk.LabelFrame(self, text="Filtros")
        marco_f.pack(fill="x", padx=10, pady=5)

        ttk.Label(marco_f, text="Especialidad:").grid(row=0, column=0, padx=6, pady=6, sticky="e")
        especialidades = [TODOS] + sorted({e for _, e in PROFESIONALES})
        cb_esp = ttk.Combobox(marco_f, textvariable=self.var_especialidad,
                              values=especialidades, state="readonly", width=18)
        cb_esp.grid(row=0, column=1, padx=6, pady=6)
        cb_esp.bind("<<ComboboxSelected>>", self._al_cambiar_especialidad)

        ttk.Label(marco_f, text="Profesional:").grid(row=0, column=2, padx=6, pady=6, sticky="e")
        self.cb_prof = ttk.Combobox(marco_f, textvariable=self.var_profesional,
                                    state="readonly", width=22)
        self.cb_prof.grid(row=0, column=3, padx=6, pady=6)
        self.cb_prof.bind("<<ComboboxSelected>>", lambda e: self.actualizar_vista())

        ttk.Label(marco_f, text="Estado:").grid(row=1, column=0, padx=6, pady=6, sticky="e")
        cb_est = ttk.Combobox(marco_f, textvariable=self.var_estado,
                              values=[TODOS, *ESTADOS], state="readonly", width=18)
        cb_est.grid(row=1, column=1, padx=6, pady=6)
        cb_est.bind("<<ComboboxSelected>>", lambda e: self.actualizar_vista())

        ttk.Label(marco_f, text="Paciente:").grid(row=1, column=2, padx=6, pady=6, sticky="e")
        ent = ttk.Entry(marco_f, textvariable=self.var_texto, width=24)
        ent.grid(row=1, column=3, padx=6, pady=6)
        self.var_texto.trace_add("write", lambda *a: self.actualizar_vista())

        ttk.Button(marco_f, text="Limpiar filtros", command=self.limpiar_filtros)\
            .grid(row=0, column=4, rowspan=2, padx=12)

        # Tabla
        marco_t = ttk.Frame(self)
        marco_t.pack(fill="both", expand=True, padx=10, pady=5)

        columnas = ("id", "fecha", "hora", "paciente", "profesional", "especialidad", "estado")
        titulos = ("N°", "Fecha", "Hora", "Paciente", "Profesional", "Especialidad", "Estado")
        anchos = (45, 90, 60, 160, 170, 130, 90)

        self.tabla = ttk.Treeview(marco_t, columns=columnas, show="headings",
                                  selectmode="browse")
        for col, tit, ancho in zip(columnas, titulos, anchos):
            self.tabla.heading(col, text=tit)
            self.tabla.column(col, width=ancho, anchor="center" if col in ("id", "hora") else "w")

        scroll = ttk.Scrollbar(marco_t, orient="vertical", command=self.tabla.yview)
        self.tabla.configure(yscrollcommand=scroll.set)
        self.tabla.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        # Colores por estado (las cancelaciones se ven en rojo)
        self.tabla.tag_configure("Cancelado", background="#f8d7da", foreground="#842029")
        self.tabla.tag_configure("Atendido", background="#d1e7dd", foreground="#0f5132")
        self.tabla.tag_configure("Pendiente", background="#fff3cd", foreground="#664d03")

        # Acciones
        marco_a = ttk.Frame(self)
        marco_a.pack(fill="x", padx=10, pady=(0, 10))
        ttk.Label(marco_a, text="Turno seleccionado:").pack(side="left")
        for estado in ESTADOS:
            ttk.Button(marco_a, text=f"Marcar {estado.lower()}",
                       command=lambda e=estado: self.cambiar_estado(e)).pack(side="left", padx=4)
        self.lbl_cuenta = ttk.Label(marco_a)
        self.lbl_cuenta.pack(side="right")

    # ---------- eventos ----------
    def _al_cambiar_especialidad(self, _evento=None):
        self._actualizar_profesionales()
        self.actualizar_vista()

    def _actualizar_profesionales(self):
        esp = self.var_especialidad.get()
        nombres = sorted({p for p, e in PROFESIONALES if esp == TODOS or e == esp})
        self.cb_prof["values"] = [TODOS] + nombres
        if self.var_profesional.get() not in self.cb_prof["values"]:
            self.var_profesional.set(TODOS)

    def limpiar_filtros(self):
        self.var_especialidad.set(TODOS)
        self.var_estado.set(TODOS)
        self.var_texto.set("")
        self._actualizar_profesionales()
        self.var_profesional.set(TODOS)
        self.actualizar_vista()

    def cambiar_estado(self, nuevo_estado):
        seleccion = self.tabla.selection()
        if not seleccion:
            messagebox.showinfo("Sin selección", "Seleccioná un turno de la tabla primero.")
            return
        id_turno = int(seleccion[0])
        for t in self.turnos:
            if t["id"] == id_turno:
                t["estado"] = nuevo_estado
                break
        self.actualizar_vista()
        if self.tabla.exists(str(id_turno)):
            self.tabla.selection_set(str(id_turno))

    # ---------- refresco ----------
    def actualizar_vista(self):
        visibles = filtrar_turnos(
            self.turnos,
            especialidad=self.var_especialidad.get(),
            profesional=self.var_profesional.get(),
            estado=self.var_estado.get(),
            texto=self.var_texto.get(),
        )

        self.tabla.delete(*self.tabla.get_children())
        for t in visibles:
            self.tabla.insert("", "end", iid=str(t["id"]), tags=(t["estado"],), values=(
                t["id"], t["fecha"].strftime("%d/%m/%Y"), t["hora"], t["paciente"],
                t["profesional"], t["especialidad"], t["estado"],
            ))

        ind = calcular_indicadores(visibles)
        self.lbl_indicadores.config(
            text=(f"Total {ind['total']}  |  Atendidos {ind['atendidos']}  |  "
                  f"Cancelados {ind['cancelados']}  |  Pendientes {ind['pendientes']}")
        )
        self.lbl_porcentaje.config(
            text=f"Tasa de cancelación: {ind['pct_cancelacion']:.1f}%"
        )
        self.lbl_cuenta.config(text=f"Mostrando {len(visibles)} de {len(self.turnos)} turnos")


if __name__ == "__main__":
    AppTurnos().mainloop()
