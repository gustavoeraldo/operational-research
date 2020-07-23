'''
Dupla : Gustavo Eraldo e Marismar Costa
Trabalho parte 2 - Implementação do Branch And Bound

'''
from docplex.mp.model import Model
import numpy as np
import os


class BB_tree():
    def __init__(self, nb_var, nb_constraints, ObjectiveFunc, Subjetcto):
        self.nb_var = nb_var                    # representa o número de variáveis no sistema
        self.nb_constraints = nb_constraints    # representa o número de restrições
        self.ObjectiveFunc = ObjectiveFunc      # guarda o valor das constantes das variáveis na função objetivo
        self.Subjetcto = Subjetcto      #guarda as constantes de cada variável do problema de cada restrição 
        self.last_constraint = []       # guarda as novas restrições adicionadas
        self.best_result = 0   # guarda a melhor solução objetivo
        self.best_node = 0     # guarda o nó que possui a melhor solução
        self.count_nodes = 0   # conta quantos nós foram visitados  


    def create_model(self, flag, min_idx, t): 
        # Criação do modelo
        mdl = Model(name='Modelo', log_output=True)
        
        # Adicionando variáveis do modelo
        qty = {f: mdl.continuous_var(name='x'+str(f)) for f in range(self.nb_var)}  

        for i in range(self.nb_var):
            mdl.add_constraints([qty[i] <=1, qty[i] >=0])# limitação das variáveis

        bound = [] # limites inferiores do modelo

        for lb, key in enumerate(self.Subjetcto):
            bound.append(self.Subjetcto[key][-1])
            self.Subjetcto[key][-1] = 0
            # Construção da expressão de cada restrição         
            mdl.add_constraint(sum(qty[key2] * ( self.Subjetcto[key][i] if i< len(self.Subjetcto[key]) else 0) for i, key2 in enumerate(qty)) >= bound[lb])     
            self.Subjetcto[key][-1] = bound[lb]

        # Criação da função objetivo do Primal
        mdl.minimize( mdl.sum(qty[key] * self.ObjectiveFunc[i] for i, key in enumerate(qty)) )
        #print(mdl.export_to_string())
        
        return mdl, qty  # retorna o modelo e as variáveis do sistema


    def branch(self,model, variables):
        
        self.count_nodes += 1
        solution = model.solve()
        if not model.solve(url=None, key=None):
            print('Solução inviável, este nó deve ser podado !')
            # retira-se a restrição que chegou nesse nó
            model.remove_constraint(self.last_constraint.pop())
            return

        else: # Caso não seja inviável, verica se tem solução ótima
            print(f'Reultado = { model.solution.get_objective_value() }')

            if self.is_integer(model, variables):
                # em caso da solução ser inteira, é realizada uma poda por integralidade
                self.best_result = solution
                self.best_node = model
                # a poda é realizada retirando a restrição adicionada 
                model.remove_constraint(self.last_constraint.pop())
                return

            else: # Caso não seja inteira, realiza-se uma nova ramificação
                min_val, min_index = 1, 0

                # guarda os valores da solução de cada variável
                val = [model.solution.get_value(variables[key].get_name()) for key, i in enumerate(variables)]

                # verificação que em qual variável deve ser criar o novo ramo
                for i in range(len(val)):
                    if abs(val[i] - 0.5) < min_val:
                        min_val = abs(val[i] - 0.5)
                        min_index = i

                if min_val == 0.5:
                    return

                # Cria-se sempre duas ramificações xj=0 e xj=1
                model.add_constraint(variables[min_index] == 0, ctname = 'b'+str(min_index))
                self.last_constraint.append('b'+str(min_index))
                self.branch(model, variables)

                model.add_constraint(variables[min_index] == 1, ctname = 'b'+str())
                self.last_constraint.append('b'+str(min_index))
                self.branch(model, variables)

        return self.best_result, self.best_node, self.count_nodes


    def is_integer(self, model, vars):
        val = [model.solution.get_value(vars[key].get_name()) for key, i in enumerate(vars)]
        print(val)
        return all([abs(i - 1) <= 1e-3 or abs(i - 0) <= 1e-3 for i in val])
    
# Função para leitura e tratamento do arquivo de entrada
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


if __name__ == '__main__':

    # separa as variáveis necessárias
    nb_var, nb_constraints, ObjectiveFunc, Subjetcto = Read_file()
    # root irá conter o modelo inicial
    root = BB_tree(nb_var, nb_constraints, ObjectiveFunc, Subjetcto)
    model, variables = root.create_model(flag=False, min_idx=0, t=0)

    print(model.export_to_string())
    
    solution = model.solve()
    res = model.solution.get_objective_value()
    print(f'Resultado inicial = {variables}')

    # guardano o valor da melhor solução
    bestres, bestnode , nd_count = root.branch(model, variables)
    
    print(f'\n \033[33m Número de nós visitados = {nd_count} \033[37m \n')
    print(f'\n\n\n\033[32m Resultado final :\033[37m\n{bestnode.export_to_string()}')