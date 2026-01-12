import os
import json
import gspread

# 1. Obtenemos la llave de la "caja fuerte" de GitHub
json_credenciales = os.environ.get('GOOGLE_CREDENTIALS')

if json_credenciales:
    # Convertimos el texto JSON a un diccionario de Python
    credenciales_dict = json.loads(json_credenciales)
    
    # 2. Nos autenticamos con Google
    gc = gspread.service_account_from_dict(credenciales_dict)
    
    try:
        # 3. Abrimos la hoja de cálculo
        # ¡IMPORTANTE! Cambia "Prueba" por el nombre EXACTO de tu archivo en Google Sheets
        SHEET_ID = "1jXjLgupXSl88dtEvU52G-5QwnBlPfD1okpHjHkmUJXU"  # <--- Pega tu ID aquí
        sh = gc.open_by_key(SHEET_ID)
        
        try:
            worksheet = sh.worksheet("Hoja 5")
        except:
            print("No encontré la pestaña 'Hoja 1'. Creando una nueva...")
            worksheet = sh.add_worksheet(title="Hoja 1", rows=100, cols=20)   
        
        # 4. Escribimos algo para probar
        # Esto escribirá en la primera fila disponible o en A1
        worksheet.append_row(["¡Hola!", "Esto fue escrito por GitHub Actions", "🤖"])
        
        print("¡Éxito! Se escribieron datos en la hoja de cálculo.")
        
    except Exception as e:
        print(f"Error al conectar con la hoja: {e}")
        print("¿Aseguraste compartir la hoja con el email del robot?")
else:
    print("No encontré las credenciales GOOGLE_CREDENTIALS.")
