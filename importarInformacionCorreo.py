import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
import json

def importar_informacion_correo():
    print("--- Iniciando proceso de importación ---")

    # 1. CONFIGURACIÓN DE CREDENCIALES
    scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    
    try:
        creds_json = os.environ.get('GOOGLE_CREDENTIALS')
        if creds_json:
            creds_dict = json.loads(creds_json)
            creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        else:
            creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
            
        client = gspread.authorize(creds)
    except Exception as e:
        print("Error con las credenciales: ", e)
        return

    # 2. DEFINIR URLS Y ID DESTINO
    url_descarga = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQu8eu2Y3wRA9YbprwNvBbrhOvFyCLF9cm0Cs9SaNwJ9lopFmsJRtwaGmcV0677J5ecLoE5PXEMKSK7/pub?output=xlsx"
    
    # --- ASEGÚRATE DE QUE ESTE ID SEA EL CORRECTO ---
    ID_HOJA_DESTINO = "1_KCf41GMXjKlVV9cjZVhy_MATxVy0qO68E6aMlC5TX4" 
    NOMBRE_PESTANA = "Retrasos_hoy"

    try:
        # 3. LEER DATOS
        print("Descargando datos...")
        df = pd.read_excel(url_descarga)
        df = df.iloc[:, :11] # Primeras 11 columnas
        df = df.fillna('')   # Rellenar vacíos

        # --- CORRECCIÓN CLAVE: CONVERTIR FECHAS A TEXTO ---
        # Esto busca columnas de fecha y las transforma a string para evitar el error JSON
        for col in df.columns:
            if pd.api.types.is_datetime64_any_dtype(df[col]):
                df[col] = df[col].astype(str)

        datos_nuevos = df.values.tolist()
        print(f"Se descargaron {len(datos_nuevos)} filas.")

        # 4. SUBIR A GOOGLE SHEETS
        sh = client.open_by_key(ID_HOJA_DESTINO)
        worksheet = sh.worksheet(NOMBRE_PESTANA)

        # Limpiar datos viejos
        last_row = len(worksheet.get_all_values())
        if last_row > 1:
            worksheet.batch_clear([f'A2:K{last_row}'])
        
        # Pegar datos nuevos
        if datos_nuevos:
            # CORRECCIÓN DE WARNING: Usamos 'range_name' y 'values' explícitamente
            worksheet.update(range_name='A2', values=datos_nuevos)
            print("¡Éxito! Datos actualizados en la nube.")
        else:
            print("No había datos nuevos para subir.")

    except Exception as e:
        print(f"Ocurrió un error en la ejecución: {e}")

if __name__ == "__main__":
    importar_informacion_correo()
