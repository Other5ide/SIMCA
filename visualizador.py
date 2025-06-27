import sys
import socketio
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QLabel, QHBoxLayout
import pyqtgraph as pg
import threading
from collections import deque

class Visualizador(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Visualizador Ambiental")
        self.resize(1000, 800)

        # Layout principal
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Tabla estática
        self.table = QTableWidget(2, 2)
        self.table.setHorizontalHeaderLabels(["Variable", "Valor actual"])
        variables = ["Temperatura", "Decibeles"]
        for i, var in enumerate(variables):
            self.table.setItem(i, 0, QTableWidgetItem(var))
            self.table.setItem(i, 1, QTableWidgetItem("..."))
        layout.addWidget(QLabel("Lecturas actuales:"))
        layout.addWidget(self.table)

        # Layout horizontal para 3 gráficos
        graphs_layout = QHBoxLayout()

        # Crear tres gráficas separadas
        self.graphs = {}
        self.data_buffers = {}
        for key in ["temperature", "noise"]:
            graph = pg.PlotWidget(title=key.capitalize())
            graph.setYRange(0, 100)
            graph.showGrid(x=True, y=True)
            curve = graph.plot(pen='g')
            self.graphs[key] = curve
            self.data_buffers[key] = deque(maxlen=100)
            graphs_layout.addWidget(graph)

        layout.addLayout(graphs_layout)

        # Socket.IO client
        self.sio = socketio.Client()
        self.sio.on("new_data", self.on_new_data)
        threading.Thread(target=self.connect_socket, daemon=True).start()

    def connect_socket(self):
        try:
            self.sio.connect("http://3.221.0.222:8081/")
        except Exception as e:
            print("Error de conexión:", e)

    def on_new_data(self, data):
        var_type = data["type"]
        value = data["value"]

        # Actualiza tabla
        if var_type == "temperature":
            self.table.setItem(0, 1, QTableWidgetItem(f"{value} °C"))
        elif var_type == "noise":
            self.table.setItem(2, 1, QTableWidgetItem(f"{value} dB"))

        # Actualiza gráfica
        if var_type in self.graphs:
            self.data_buffers[var_type].append(value)
            y = list(self.data_buffers[var_type])
            x = list(range(len(y)))
            self.graphs[var_type].setData(x, y)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    vis = Visualizador()
    vis.show()
    sys.exit(app.exec_())
