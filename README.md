Signal Hound Control - Python + sa_api.dll
Este proyecto permite controlar un analizador de espectro Signal Hound desde Python utilizando la librería oficial sa_api.dll.

📋 Requisitos de software
Sistema Operativo: Windows 10 o Windows 11

Signal Hound API: sa_api.dll (librería principal de control)

Driver USB FTDI: CDM v2.12.00 WHQL Certified.exe

FTDI DLL: ftd2xx.dll (debe estar en el mismo directorio que sa_api.dll)

Python: 3.x



⚙️ Instalación
Instalar driver USB FTDI
Ejecuta el instalador CDM v2.12.00 WHQL Certified.exe desde la carpeta /drivers.

Colocar librerías DLL
Asegúrate de que sa_api.dll y ftd2xx.dll estén en la misma carpeta donde se ejecutará main.py.
También puedes colocarlos en una carpeta incluida en la variable de entorno PATH de Windows.

Instalar dependencias de Python

bash
Copiar
Editar
pip install numpy
Conectar el Signal Hound
Conecta el dispositivo por USB y verifica que el driver esté correctamente instalado.

▶️ Uso
Ejecutar el script principal:

bash
Copiar
Editar
python main.py
El script abrirá la comunicación con el Signal Hound y ejecutará las funciones configuradas en main.py.

📌 Notas importantes
Este proyecto solo funciona en Windows, ya que sa_api.dll no tiene versión nativa para Linux.

Debes tener los drivers oficiales de Signal Hound y FTDI instalados.

Si el programa no detecta el dispositivo, revisa:

Que el driver esté instalado en el Administrador de Dispositivos.

Que sa_api.dll y ftd2xx.dll estén accesibles por el script.

📚 Documentación oficial
Signal Hound API Documentation

