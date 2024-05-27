# Retorna el numero del ultimo índice de un string
def ultimo_index(str: str) -> str:
    return len(str) - 1


# Parte la cadena en 2 partes, en el index indicado.
# Luego vuelve a armarla colocando entre ellas la cadena a insertar
def insertar_en_string(str: str, app: str, pos: int) -> str:
    # > Queriendo agregar "-" en la quinta posición del string "20198466"
    # > str = "2019" + "-" + "8466"
    # > str = "2019-8466"
    return str[:pos] + app + str[pos:]


def dividir_lista(lista: list, sep: str, maxsplit=-1):
    pre_split = lista.split(sep=sep, maxsplit=maxsplit)
    return [c for c in pre_split if c != ""]  # Limpia items vacíos de la lista
