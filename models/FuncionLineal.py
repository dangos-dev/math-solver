from pydantic import BaseModel
from sympy import Symbol, solve, sympify
from assets.utils import dividir_lista, insertar_en_string, ultimo_index

SEPARADOR_MIEMBROS = '='
SEPARADOR_PARAMETROS = ';'
SEPARADOR_SOLUCIONES = ','
VARIABLE_MIEMBRO_DEPENDIENTE = 'y'
VARIABLE_MIEMBRO_INDEPENDIENTE = 'X'
CARACTERES_PERMITIDOS_NOMBRE_VARIABLE = "abcdefghijklmnopqrstuvwxyz"


class Input_FuncionLinear(BaseModel):
    ecuacion: str

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "ecuacion": "y=ax+b+0; a=0, b=0, x=0",
                }
            ]
        }
    }


class Miembro(BaseModel):
    variable: str = ''
    expresion: str = ''
    generado: bool = False


class Solucion(BaseModel):
    variable: str = ''
    valor: float = 0


# Teniendo una ecuación lineal del tipo [f(x_1, x_2, ..., x_n) = (a_1)(x_1) + (a_2)(x_2) ... (a_n)(x_n), x_n={x_n}]
# POR AHORA SOLO SE ADMITEN ECUACIONES DE UNA SOLA VARIABLE DEL TIPO [f(x) = ax + b, {a, b, x}]
class EcuacionLinear:

    ecuacion = ""
    miembro_independiente: Miembro = {}
    miembro_dependiente: Miembro = {}
    soluciones: Solucion = []

    def __init__(self, input: Input_FuncionLinear):
        # Se eliminan todos los espacios en blanco del input
        self.ecuacion = ''.join(
            filter(lambda x: not x.isspace(), input.ecuacion))

        self.__obtener_soluciones__()
        self.__separar_miembros__()
        self.__formatear_funcion__()

    def __obtener_soluciones__(self):
        lista_soluciones = []

        split_ecuacion = dividir_lista(
            lista=self.ecuacion, sep=SEPARADOR_PARAMETROS, maxsplit=1)

        if len(split_ecuacion) == 2:
            self.ecuacion = split_ecuacion[0]
            lista_soluciones = dividir_lista(
                lista=split_ecuacion[1], sep=SEPARADOR_SOLUCIONES, maxsplit=2)

        self.soluciones = lista_soluciones

    def __separar_miembros__(self):

        # Se debe agregar el signo de multiplicación (*) entre los términos que no lo tengan
        # >  Para cada paso valúa el caracter actual y el siguiente.
        # >> Si el caracter actual no es alfanumérico (es un signo) entonces hace skip
        # >> Si si esl alfanumérico y el siguiente también alfanumérico (a-z, 0-9), entonces agrega el signo
        # >> Para agregar el signo en la posición indicada, se debe romper en dos partes y volver a armar.
        # >> También se debe sumar 1 al index para mantener la secuencia
        ###################################################################################################
        #                                         Evaluando [y=ax+2*b]
        # >  [y] es alfanumérico pero [=] no lo es, así que no agrega el signo                       >> [y=ax+2*b]
        # >  [=] no es alfanumérico, por lo que no agrega el signo                                   >> [y=ax+2*b]
        # >  [a] es alfanumérico, y [x] también lo es, así que agrega el signo                       >> [y=a*x+2*b]
        # >>     Al agregar el signo, pasa del index 2 al 4 para no leer innecesariamente el (*)
        # >  [x] es alfanumérico, pero [=] no, asi que hace skip                                     >> [y=a*x+2*b]
        # >  Y asi sucesivamente hasta llegar al último item.
        # >> El item que le sigue al último es el primero, por lo tanto no se evalúa y ahi termina.

        i = 0
        for caracter in self.ecuacion:
            len_eq = len(self.ecuacion)  # Tamaño del string de la ecuación

            # Guarda el index actual, viene acarreado del step anterior
            idx_actual = i
            # Se recalcula el index siguiente. Se hace módulo para evitar que sobrepase el tamaño del array
            i = (i + 1) % len(self.ecuacion)
            idx_proximo = i                     # Guarda el index siguiente

            if not caracter.isalpha():          # Skip si el caracter actual no es (a-z, 0-9)
                continue

            # Skip si el index actual coindide con el último.
            # En este paso el idx_proximo se pone como 0, retornando al incio del array, lol
            if idx_actual == ultimo_index(self.ecuacion):
                continue

            # Guarda el caracter siguiente al actual
            char_adjacente = self.ecuacion[idx_proximo]

            if char_adjacente.isalnum():
                self.ecuacion = insertar_en_string(
                    str=self.ecuacion, app='*', pos=idx_proximo)
                i += 1

        # Se identifican los miembros de la ecuación
        # Estos están separados por el signo de igual
        # Teniendo [y = ax + b] :
        #   El primer será [y]
        #   El segundo miembro será todo lo demas

        split_ecuacion = dividir_lista(
            lista=self.ecuacion, sep=SEPARADOR_MIEMBROS, maxsplit=1)

        match len(split_ecuacion):
            # No tiene miembros o la ecuación esta vacía. Por lo tanto completo la ecuacion con [x = 0]
            case 0:
                self.miembro_independiente = Miembro(
                    expresion='0',
                    generado=True)

                self.miembro_dependiente = Miembro(
                    variable=VARIABLE_MIEMBRO_DEPENDIENTE,
                    expresion='y',
                    generado=True)

                # Se genera la función igualada a cero manualmente
                self.ecuacion = "y=0"

            # Solo tiene un miembro, por defecto se asume que se ha indicado el indepentente igualado a 0 [ax + b = 0]
            case 1:
                self.miembro_independiente = Miembro(
                    expresion=split_ecuacion[0],
                    generado=True)

                self.miembro_dependiente = Miembro(
                    variable=VARIABLE_MIEMBRO_DEPENDIENTE,
                    expresion='0',
                    generado=True)

                # Se agrega el miembro dependiente manualmente
                self.ecuacion = VARIABLE_MIEMBRO_DEPENDIENTE + "=" + self.ecuacion

            case 2:
                caracter_variable_dependiente = self.__determinar_variable__(
                    split_ecuacion[0])

                self.miembro_independiente = Miembro(
                    variable=split_ecuacion[1][0],
                    expresion=split_ecuacion[1])

                self.miembro_dependiente = Miembro(
                    variable=caracter_variable_dependiente,
                    expresion=split_ecuacion[0])

    def __determinar_variable__(self, expresion: str):
        # Toma en cuenta solo las letras que pudieran ser variables, ignora números y signos
        # Recorre el string [expresion] y valida si el caracter se encuentra en la constante de caracteres permitidos
        # Si existe, lo agrega al array

        split_variables = []

        # split_variables = [caracter for caracter in expresion if caracter in CARACTERES_PERMITIDOS_NOMBRE_VARIABLE]
        for caracter in expresion:
            if caracter in CARACTERES_PERMITIDOS_NOMBRE_VARIABLE:
                split_variables.append(caracter)

            # Reemplacé el inline method de arriba por este for ya que
            #   Esta rutina se entiende mejor, lol
            #   Puedo evitar memory leaks con esta validación. Inmediatamente hayan mas de dos variables en un miembro
            if len(split_variables) == 2:
                break

        # Devuelve la ultima variable, teniendo en cuenta que se sigue la estructura [a * x] donde a es una constante
        return split_variables[-1]

    def __formatear_funcion__(self):
        # Sustituye las soluciones en las variables correspondientes
        # Le agrega parentesis para preservar la ley de signos y números negativos

        for solucion in self.soluciones:
            miembros_solucion = dividir_lista(
                lista=solucion, sep=SEPARADOR_MIEMBROS, maxsplit=1)

            if len(miembros_solucion) != 2:
                break

            try:
                variable = miembros_solucion[0]
                valor = float(miembros_solucion[1])
            except ValueError:
                break

            format_variable = "(" + str(valor) + ")"
            self.ecuacion = self.ecuacion.replace(variable, format_variable)

    def resolver(self):
        # Esto mientras tanto
        # Pendiente de implementar lo dictado por este documento
        # https://miscelaneamatematica.org/download/tbl_articulos.pdf2.81c98dc7db46818b.4d5f4d61647269645f612e706466.pdf
        sympy_eq = sympify("Eq(" + self.ecuacion.replace("=", ",") + ")")
        return str(solve(sympy_eq, Symbol(self.miembro_dependiente.variable), dict=True))
