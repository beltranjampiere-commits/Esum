import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
import json

def importar_informacion_correo():
    print("--- Iniciando proceso de importación ---")

    # 1. CONFIGURACIÓN DE CREDENCIALES
    # Esto busca una "variable de entorno" o un archivo local. 
    # (Te enseñaré a configurar esto seguro en el siguiente paso)
    scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    
    # Aquí intentamos leer las credenciales de manera segura
    try:
        # Opción A: Si usas GitHub Actions (Variable de entorno)
        creds_json = os.environ.get('GOOGLE_CREDENTIALS')
        if creds_json:
            creds_dict = json.loads(creds_json)
            creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        else:
            # Opción B: Si lo pruebas en tu PC (Archivo local)
            creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
            
        client = gspread.authorize(creds)
    except Exception as e:
        print("Error con las credenciales. Asegúrate de tener el archivo .json o el secreto configurado.")
        print(f"Detalle: {e}")
        return

    # 2. DEFINIR URLS Y ID DESTINO
    url_descarga = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQu8eu2Y3wRA9YbprwNvBbrhOvFyCLF9cm0Cs9SaNwJ9lopFmsJRtwaGmcV0677J5ecLoE5PXEMKSK7/pub?output=xlsx"
    
    # --- OJO: CAMBIA ESTO POR EL ID REAL DE TU HOJA DE GOOGLE ---
    ID_HOJA_DESTINO = "1_KCf41GMXjKlVV9cjZVhy_MATxVy0qO68E6aMlC5TX4" 
    NOMBRE_PESTANA = "Retrasos_hoy"

    try:
        # 3. LEER DATOS (Pandas lee directo de la URL)
        print("Descargando datos...")
        df = pd.read_excel(url_descarga)
        
        # Tomamos solo columnas A a la K (indices 0 al 10)
        df = df.iloc[:, :11]
        
        # Rellenamos vacíos para que Google Sheets no de error
        df = df.fillna('')
        
        datos_nuevos = df.values.tolist()
        print(f"Se descargaron {len(datos_nuevos)} filas.")

        # 4. SUBIR A GOOGLE SHEETS
        sh = client.open_by_key(ID_HOJA_DESTINO)
        worksheet = sh.worksheet(NOMBRE_PESTANA)

        # Limpiar datos viejos (desde la fila 2)
        last_row = len(worksheet.get_all_values())
        if last_row > 1:
            worksheet.batch_clear([f'A2:K{last_row}'])
        
        # Pegar datos nuevos
        if datos_nuevos:
            worksheet.update('A2', datos_nuevos)
            print("¡Éxito! Datos actualizados en la nube.")
        else:
            print("No había datos nuevos para subir.")

    except Exception as e:
        print(f"Ocurrió un error en la ejecución: {e}")

if __name__ == "__main__":
    importar_informacion_correo()
