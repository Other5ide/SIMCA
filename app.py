import sys
import socketio
import threading
import time
from collections import deque
import requests
import json

from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem,
    QLabel, QHBoxLayout, QSpacerItem, QSizePolicy
)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt
import pyqtgraph as pg

### Configuración DeepSeek API REST ###
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"
DEEPSEEK_API_KEY = "sk-49d88176d9e84d1fbfd0f3100d8db09f"  # Cambia aquí tu API Key


def llamar_ia_via_rest(prompt):
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.5,
        "stream": False
    }

    try:
        response = requests.post(DEEPSEEK_API_URL, headers=headers, json=data, timeout=15)
        response.raise_for_status()
        respuesta_json = response.json()
        return respuesta_json['choices'][0]['message']['content'].strip()
    except Exception as e:
        return f"Error en IA REST: {e}"


def evaluar_ambiente_rest(temperatura, ruido):
    prompt = f"""
    Evalúa si las condiciones ambientales son buenas o no basándote en los siguientes datos:
    Temperatura: {temperatura}°C
    Ruido: {ruido} dB

    Si ambas están dentro de rangos saludables, responde: "El ambiente actual es bueno.".
    Si no, da recomendaciones específicas como por ejemplo:
    "100 dB -> Nivel de ruido dañino para la salud. Intenta disminuir el volumen."
    "40°C -> El ambiente está muy caluroso. Intenta abrir una ventana."

    Responde de forma concisa.
    """
    return llamar_ia_via_rest(prompt)


class Visualizador(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Visualizador Ambiental")
        self.resize(1100, 700)
        self.setStyleSheet("background-color: #121212; color: #E0E0E0;")

        self.temperatura = None
        self.ruido = None

        fuente_titulos = QFont("Segoe UI", 11, QFont.Bold)
        fuente_normal = QFont("Segoe UI", 10)

        # Layout principal horizontal
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(20)
        self.setLayout(main_layout)

        # Panel izquierdo: IA + tabla
        panel_izquierdo = QVBoxLayout()
        panel_izquierdo.setSpacing(25)
        main_layout.addLayout(panel_izquierdo, 1)

        self.ia_label = QLabel("Asistente IA:\nEsperando datos...")
        self.ia_label.setWordWrap(True)
        self.ia_label.setFont(fuente_normal)
        self.ia_label.setStyleSheet("""
            background-color: #1E1E1E;
            border-radius: 10px;
            padding: 15px;
            border: 1px solid #333333;
        """)
        self.ia_label.setMinimumHeight(120)
        panel_izquierdo.addWidget(self.ia_label)

        titulo_tabla = QLabel("Lecturas actuales")
        titulo_tabla.setFont(fuente_titulos)
        panel_izquierdo.addWidget(titulo_tabla)

        self.table = QTableWidget(2, 2)
        self.table.setHorizontalHeaderLabels(["Variable", "Valor actual"])
        self.table.verticalHeader().setVisible(False)
        self.table.setFont(fuente_normal)
        self.table.setStyleSheet("""
            QHeaderView::section { background-color: #222222; color: #AAAAAA; }
            QTableWidget { background-color: #1E1E1E; gridline-color: #333333; }
            QTableWidget::item { color: #E0E0E0; }
        """)
        variables = ["Temperatura", "Decibeles"]
        for i, var in enumerate(variables):
            item_var = QTableWidgetItem(var)
            item_var.setFlags(Qt.ItemIsEnabled)
            self.table.setItem(i, 0, item_var)
            item_val = QTableWidgetItem("...")
            item_val.setFlags(Qt.ItemIsEnabled)
            self.table.setItem(i, 1, item_val)
        self.table.resizeColumnsToContents()
        self.table.setFixedHeight(90)
        panel_izquierdo.addWidget(self.table)

        panel_izquierdo.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))

        # Panel derecho: gráficas verticales
        panel_derecho = QVBoxLayout()
        panel_derecho.setSpacing(25)
        main_layout.addLayout(panel_derecho, 2)

        self.graphs = {}
        self.data_buffers = {}

        for key, title, y_range in [("temperature", "Temperatura (°C)", 60), ("noise", "Ruido (dB)", 120)]:
            graph = pg.PlotWidget(title=title)
            graph.setBackground("#121212")
            graph.getPlotItem().showGrid(x=True, y=True, alpha=0.3)
            graph.setYRange(0, y_range)
            graph.getPlotItem().getAxis("bottom").setPen(pg.mkPen("#888888"))
            graph.getPlotItem().getAxis("left").setPen(pg.mkPen("#888888"))
            graph.getPlotItem().getAxis("bottom").setTextPen("#AAAAAA")
            graph.getPlotItem().getAxis("left").setTextPen("#AAAAAA")
            curve = graph.plot(pen=pg.mkPen("#00CC66", width=2))
            self.graphs[key] = curve
            self.data_buffers[key] = deque(maxlen=200)
            panel_derecho.addWidget(graph)

        # Socket.IO client
        self.sio = socketio.Client()
        self.sio.on("new_data", self.on_new_data)
        threading.Thread(target=self.connect_socket, daemon=True).start()

        # Hilo que actualiza la IA cada 10 segundos
        threading.Thread(target=self.actualizar_asistente_ia, daemon=True).start()

    def connect_socket(self):
        try:
            self.sio.connect("http://3.221.0.222:8081/")
        except Exception as e:
            print("Error de conexión:", e)

    def on_new_data(self, data):
        var_type = data["type"]
        value = data["value"]

        if var_type == "temperature":
            self.temperatura = value
            self.table.setItem(0, 1, QTableWidgetItem(f"{value:.1f} °C"))
        elif var_type == "noise":
            self.ruido = value
            self.table.setItem(1, 1, QTableWidgetItem(f"{value:.1f} dB"))

        if var_type in self.graphs:
            self.data_buffers[var_type].append(value)
            y = list(self.data_buffers[var_type])
            x = list(range(len(y)))
            self.graphs[var_type].setData(x, y)

    def actualizar_asistente_ia(self):
        while True:
            if self.temperatura is not None and self.ruido is not None:
                respuesta = evaluar_ambiente_rest(self.temperatura, self.ruido)
                self.ia_label.setText(f"Asistente IA:\n{respuesta}")
            time.sleep(10)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    vis = Visualizador()
    vis.show()
    sys.exit(app.exec_())
