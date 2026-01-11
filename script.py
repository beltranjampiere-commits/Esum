import os
print("¡Hola! Si estás leyendo esto, la automatización funciona exitosamente.")

# Este pequeño truco imprime cualquier "Secret" que configuremos después (de forma segura, mostrando asteriscos en los logs si es real)
if "MI_VARIABLE_SECRETA" in os.environ:
    print("He detectado una variable secreta configurada.")
else:
    print("No hay variables secretas configuradas todavía.")
