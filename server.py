from fastapi import FastAPI
from models.FuncionLineal import Input_FuncionLinear, EcuacionLinear

app = FastAPI(title="Dangos.dev solver", description="Realizado por métodos educativos. \
              El objetivo principal es poder realizar algoritmos de cálculo complejos y demostraciones a base de código",)


@app.post("/resolver/linear/simple", 
          tags=["Resolver ecuaciones"], 
          name="Resolver ecuación lineal conociendo las variables", 
          description="Teniendo ya las soluciones a las variables del miembro independiente, determina el valor del miembro dependiente",

             )
async def resolver_funcion_linear(input: Input_FuncionLinear):
    ecuacion = EcuacionLinear(input)
    return ecuacion.resolver()
