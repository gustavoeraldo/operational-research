'''
@authors: Gustavo Eraldo / Marismar Costa

------------ Test samples ------------
4 2
1.5 2.0 3.0 0.8
7 8 30 6 3
550 300 400 250 50

3 2
5 10 8
3 5 2 60
4 4 4 72
'''

from docplex.mp.model import Model
import numpy as np
import os
import sys

# MULTIPLICAR O VALORES ENCONTRADOS DAS VARIÁVEIS PARA ENCONTRAR AS VARIÁVEIS DE FOLGA DE CADA RESTRIÇÃO

def Solve_Model(Model, qty, Subjetcto, bound):

    print(Model.export_to_string())
    url = None
    key = None
    String = ""

    if not Model.solve(url=url, key=key): # Identifica se o problema for inviável
        solution = Model.get_solve_status()
        String = str(solution).split("JobSolveStatus.")

        if String[1] == "INFEASIBLE_SOLUTION": 
            print("****** O problema é inviável *****")
        else:
            print("****** O problema é ilimitado *****")

        sys.exit()

    else:
        Model.solve()
        Model.float_precision = 3
        print("\n\n*********** Solução do modelo :")
        Model.print_solution()
        print('\n'*2)
        
        Objct_val = Model.solution.get_objective_value()
        Slack_values = []
 
        print(f'* Variáveis de folga do : {Model.get_name()}')

        Result_val = [] # Guarda o valor da solução das variáveis
        for index,key in enumerate(Subjetcto):
            s=0
            for i in range(0,len(qty)):
                s += (Subjetcto[key][i] * Model.solution.get_value( qty[i].get_name()) )
                
                if index < 1 :
                    Result_val.append(  Model.solution.get_value( qty[i].get_name()) )

            s = bound[index] - s
            Slack_values.append(abs(s)) 
            print(f' Variável_{index} de folga = {abs(s)}')

        print('\n\n\n')
                         
        return Objct_val, Slack_values, Result_val
    

# O dual é obtido por meio da matrix transposta do sistema que representa o primal. Tudo que seja linha torna-se coluna e vice-versa
# nb_var e nb_constraints representam o número de restrições e quantidade de variáveis no sistema respectivamente.
def Get_Dual(nb_var, nb_constraints, ObjectiveFunc, Subjetcto):

    dual = Model(name='---- Modelo Dual ----', log_output=True)
    
    bound=[] # guarda a função Objetivo, que no primal seriam os limites das restrições

    # Adicionando as variáveis do Dual
    qty2 = {f: dual.continuous_var(name='y'+str(f)) for f in range(nb_var)}

    for lb, key in enumerate(Subjetcto):
        bound.append(Subjetcto[key].pop())    
    
    aux = {}
    # Construção das restrições do modelo
    for index in range(nb_constraints):
         # Construção das equações de cada restrição
        amount = dual.sum(qty2[key2] * Subjetcto['c'+str(i)][index] for i, key2 in enumerate(qty2) )
        # Os coeficientes da função objetivo do primal agora se tornam os limites superiores das restrições do Dual
        dual.add_range(lb=0,expr=amount, ub=ObjectiveFunc[index])
    #    
    for index in range(nb_constraints):
        for i in range(0,len(qty2)):
            aux.setdefault('c'+str(index), []).append(Subjetcto['c'+str(i)][index])

    # Construção da função de maximização pela multiplicação dos coeficientes e variáveis criadas
    dual.maximize( dual.sum(qty2[key] * bound[i] for i, key in enumerate(qty2)) ) 
    
    return dual, qty2, ObjectiveFunc, aux


def Read_file():
    
    execution_path = os.getcwd()
    
    try:
        file = open(os.path.join(execution_path, "problema.txt"), encoding='UTF-8')
    except Exception as e:
        print(e)

    line1 = file.readline() # linha 1 do arquivo
    line2 = file.readline() # linha 2 do arquivo
    Constraints_values = file.readlines() # Linhas restantes contendo as restrições do problema 

    nb_var = int(line1.split()[0]) # Número de variáveis
    nb_constraints = int(line1.split()[1]) # Número de restrições

    
    a_list = line2.split()
    map_object = map(float, a_list)
    ObjectiveFunc = list(map_object) # ObjectiveFunc guarda os coeficientes da função objetivo

    Subjetcto = {}
    s = '' 

    for i in range(0,nb_constraints): 
        s = Constraints_values[i]
        a_list = s.split()
        map_object = map(float, a_list)
        list_of_integers = list(map_object)
        # Guarda os coeficientes das restrições do primal e os limites inferiores
        Subjetcto.setdefault('c'+str(i), list_of_integers) 

    file.close()
    #      número de variáveis do sistema, num de restrições, constantes da função objetivo, constantes das restrições e limites
    return nb_var, nb_constraints, ObjectiveFunc, Subjetcto


def Create_model(nb_var, nb_constraints, ObjectiveFunc, Subjetcto): 

    # Criação do modelo
    mdl = Model(name='---- Modelo Primal ----', log_output=True)

    # Adicionando variáveis do modelo
    qty = {f: mdl.continuous_var(name='x'+str(f)) for f in range(nb_var)}  

    bound = [] # limites inferiores do modelo

    for lb, key in enumerate(Subjetcto):
        bound.append(Subjetcto[key][-1])
        Subjetcto[key][-1] = 0
        # Construção da expressão de cada restrição         
        amount = mdl.sum(qty[key2] * ( Subjetcto[key][i] if i< len(Subjetcto[key]) else 0) for i, key2 in enumerate(qty))
        # Adicionando a expressão de cada restrição e com os respectivos limites
        mdl.add_range(lb=bound[lb],expr=amount, ub=10000)
        Subjetcto[key][-1] = bound[lb]

    # Criação da função objetivo do Primal
    mdl.minimize( mdl.sum(qty[key] * ObjectiveFunc[i] for i, key in enumerate(qty)) )
   
    return mdl, qty, bound, Subjetcto


if __name__ == '__main__':

    nb_var, nb_constraints, ObjectiveFunc, Subjetcto = Read_file()
    
    mdl, qty, bound, Subjetcto = Create_model(nb_var, nb_constraints, ObjectiveFunc, Subjetcto)
    Objec_val1, Slack_values1, Result_val1 = Solve_Model(mdl, qty, Subjetcto, bound) # Solving Primal

    
    print("******************** PARTE DO DUAL ***************************")
    
    dual, qty2, bound, Subjetcto = Get_Dual(nb_constraints, nb_var, ObjectiveFunc, Subjetcto)
    Objec_val2, Slack_values2, Result_val2 = Solve_Model(dual, qty2, Subjetcto, bound) # Solving Dual
    
    print("\n******************** Requisito 7 ********************")
    for i in range(0,nb_var):
        print(Result_val1[i] * Slack_values2[i])

    print("\n******************** Requisito 8 ********************")
    for i in range(0,nb_constraints):
        print(Result_val2[i] * Slack_values1[i])

    mdl.end() # Finaliza o modelo representante do primal
    dual.end() # Finaliza o modelo representante do dual      