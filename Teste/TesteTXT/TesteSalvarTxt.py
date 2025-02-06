import sys
import serial
import serial.tools.list_ports
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QComboBox, QLabel, QMessageBox
from PyQt5.QtGui import QIcon, QPixmap
from datetime import datetime
import time

class CustomButtonApp(QWidget):
    def __init__(self):
        super().__init__()
        self.selected_com_port = None
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('App com Botão Personalizado')
        self.setGeometry(100, 100, 300, 250)

        # Criação do layout
        layout = QVBoxLayout()

        # Label e ComboBox para seleção da porta COM
        self.com_label = QLabel('Selecione a porta COM:')
        layout.addWidget(self.com_label)

        self.com_combo = QComboBox()
        self.populate_com_ports()
        layout.addWidget(self.com_combo)

        # Botão para confirmar a seleção da COM
        self.select_com_button = QPushButton('Confirmar Porta COM')
        self.select_com_button.clicked.connect(self.select_com_port)
        layout.addWidget(self.select_com_button)

        # Botão com imagem personalizada
        button = QPushButton('')  # Texto vazio
        pixmap = QPixmap('AbaTrack.png')  # Substitua pelo nome do seu arquivo
        icon = QIcon(pixmap)
        button.setIcon(icon)
        button.setIconSize(pixmap.size())

        # Ação do botão
        button.clicked.connect(self.save_serial_data)

        # Adiciona o botão ao layout
        layout.addWidget(button)
        self.setLayout(layout)

    def populate_com_ports(self):
        ports = serial.tools.list_ports.comports()
        for port in ports:
            self.com_combo.addItem(port.device)

    def select_com_port(self):
        self.selected_com_port = self.com_combo.currentText()
        QMessageBox.information(self, 'Porta COM Selecionada', f'Porta {self.selected_com_port} selecionada com sucesso!')

    def read_serial_data(self, com_port):
        try:
            with serial.Serial(com_port, 9600, timeout=5) as ser:  # Timeout aumentado para 5 segundos
                time.sleep(2)  # Espera mais tempo para garantir que os dados sejam recebidos
                if ser.in_waiting > 0:  # Verifica se há dados disponíveis na porta serial
                    data = ser.read(ser.in_waiting).decode('utf-8', errors='ignore').strip()
                    return data
                else:
                    return ''  # Retorna vazio se não houver dados
        except serial.SerialException as e:
            print(f'Erro ao ler a porta serial: {e}')
            return ''

    def save_serial_data(self):
        if not self.selected_com_port:
            QMessageBox.warning(self, 'Erro', 'Por favor, selecione uma porta COM antes de salvar.')
            return

        serial_data = self.read_serial_data(self.selected_com_port)

        if serial_data == '':
            QMessageBox.warning(self, 'Erro', 'Nenhum dado serial recebido.')
            return

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'dados_serial_{timestamp}.txt'
        with open(filename, 'w') as file:
            file.write(serial_data)

        print(f'Dados salvos em {filename}!')

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = CustomButtonApp()
    window.show()
    sys.exit(app.exec_())
