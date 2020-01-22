
import sys
import ply.yacc as yacc
from lex import tokens
import re
import operator


# class array(tuple):
#     def __new__(self, position, start,stop):
#       return tuple.__new__(array, (position, start, stop))


# class value(tuple):
#     def __new__(self, t, num,val):
#         return tuple.__new__(value,(t, num,()))
#
#     def __new__(self, t, num):
#         return tuple.__new__(value, (t, num))
# value.type = property(operator.itemgetter(0))
# value.num = property(operator.itemgetter(1))
#
# array.position = property(operator.itemgetter(0))
# array.start = property(operator.itemgetter(1))
# array.stop =property(operator.itemgetter(2))
#


### FUNKCJE I STRUKTURY DANYCH używane przez kompilator ###

memory_count = 30
values_declared = {}
arrays_declared = {}
initializations = {}
labels_val =[]

one = "SUB 0 \n INC \n STORE 1 \n"
negone = "SUB 0 \n DEC \n STORE 2 \n"

# 1 2 - jedynka i -1
# 3-10 - rejestry
# 0 - komórka ALU

#debug
debug = 0

def where():
    if debug == 1:
        return "PUT "  + "\n"
    else:
        return ""

def declare_value(id,lineno):
    if id in values_declared:
        raise Exception("deklaracja " + id +" już istnieje linia - "+lineno)
    global memory_count
    memory_count += 1
    values_declared[id] = memory_count



def declare_array(id,start,last, lineno):                                       #ok
    if start > last:
        raise Exception("nieprawidłowy zakres linia - " + lineno)
    global memory_count
    posinmem = memory_count+1
    arrays_declared[id] = (posinmem, start, last)
    memory_count += (last - start + 1)


## jeśli 2gi argument 0 - liczbę posiadamy w p0 jęsli nie zapisujhe do memoryplace
def generate_const_and_Store(num, memoryplace):
    comm=""
    if memoryplace != 0:
        comm = "STORE " + str(memoryplace) + "\n"
    if num != 0:
        while num > 5 or num < -5:
            if num % 2 == 0:
                num = num // 2
                comm = "SHIFT "+"1" + "\n" + comm
            else:
                num = num - 1 if num > 0 else num +1
                comm = ("INC " + "\n" + comm if num > 0 else "DEC " + "\n" + comm)
        for i in range(num-1 if num > 0 else -num -1):
            comm = ("INC " + "\n" + comm if num > 0 else "DEC " + "\n" + comm)
        comm = ("INC " + "\n" + comm if num > 0 else "DEC " + "\n" + comm)
    comm = "SUB 0 " + "\n" + comm
    return comm





def load_value(value,pos,lineno):
    if value[0] == "n":
        return str(generate_const_and_Store(int(value[1]), pos))
    if value[0] == "id"  or value[0]=="it":
        isvalueinit(value[1], lineno)
        stri=("STORE " + str(pos) + "\n") if pos != 0 else ""
        return str(load_value_addr(value, lineno)) + \
           "LOADI 4"   + "\n" + \
            stri
    if value[0] == "tab":
        isvalueinit(value[1], lineno)
        stri = ("STORE " + str(pos) + "\n") if pos != 0 else ""
        return str(load_value_addr(value, lineno)) + \
               "LOADI 4" + "\n" + \
               stri
def load_value_addr(value,lineno):
    if value[0] == "id" or value[0]=="it":

        isvaluedeclared(value[1], lineno)
        return str(generate_const_and_Store(values_declared[value[1]], 4))
    elif value[0] == "tab":
        isarraydeclared(value[1], lineno)
        tab_pos, tab_start, tab_stop = arrays_declared[value[1]]
        cell_index = value[2]
        return str(load_value(cell_index, 3, lineno)) + \
               str(generate_const_and_Store(tab_start, 5)) + \
               "SUB 0 " + "\n" + \
               "LOAD 3 " + "\n" + \
               "SUB 5" + "\n" + \
               "STORE 3" + "\n" + \
               str(generate_const_and_Store(tab_pos, 5)) + \
               "SUB 0 " + "\n" + \
               "LOAD 3" + "\n" + \
               "ADD 5" + "\n" + \
               "STORE 4" + "\n"


# Program ->
def p_program_with_declarations(p):
    ''' program : DECLARE declarations BEGIN commands END '''
    str1 = one+negone+p[4]+"HALT"
    p[0] = replace_jumps(str1)


def p_program_without_declarations(p):          #ok
    ''' program : BEGIN commands END '''
    p[0] =  replace_jumps(one+negone+p[2] + "HALT")


# declarations ->

def p_declaring_array(p):
    ''' declarations : declarations COMMA ID LBR NUM COLON NUM RBR  '''          #ok
    declare_array(p[3], p[5], p[7], str(p.lineno(1)))


def p_declaring_variable(p):
    ''' declarations : declarations COMMA ID  '''    #ok
    declare_value(p[3], str(p.lineno(1)))

def p_declaring_array_end(p):
    ''' declarations :  ID LBR NUM COLON NUM RBR  '''          #ok
    declare_array(p[1], p[3], p[5], str(p.lineno(1)))


def p_declaring_variable_end(p):
    ''' declarations :   ID  '''    #ok
    declare_value(p[1], str(p.lineno))

# commands ->

def p_commands_multi(p):
    ''' commands : commands command '''
    p[0] = p[1] + p[2]


def p_commands_single(p):
    ''' commands : command '''
    p[0] = p[1]


#  command -> Big Production Set           #
# Stream in and out parser initialization #

def p_read_command(p):             #ok
    ''' command : READ identifier SEMICOLON '''
    id,lineno=p[2],str(p.lineno(1))
    p[0] = load_value_addr(id, lineno) +\
           "GET \n" +\
           "STOREI 4  \n"
    initializations[id[1]] = True;

def p_write_command(p):         #ok
    ''' command : WRITE value SEMICOLON '''
    value, lineno = p[2], str(p.lineno(1))
    p[0] = str(load_value(value, 0, lineno)) +\
            "PUT \n"

# Stream in and out END #
# ASSIGN
def p_assigning_command(p):  # chcę mieć w 20 komórce liczbę
    ''' command : identifier ASSIGN expression SEMICOLON '''
    identifier, expression, lineno = p[1], p[3], str(p.lineno(1))
    p[0] = expression + \
           str(load_value_addr(identifier, lineno)) + \
           "LOAD 20\n" + \
           "STOREI 4\n"
    initializations[identifier[1]] = True

def p_ifelse_command(p):
    '''command : IF condition THEN commands ELSE commands ENDIF '''
    condition, commands_if, commands_else, lineno = p[2], p[4], p[6], str(p.lineno(1))
    here,jump = add_placestojump(1)

    p[0] =	condition[0] +\
			commands_if +\
			"JUMP " + jump[0] + "\n" +\
			condition[1] +\
			commands_else +\
			here[0]

def p_if_command(p):
    '''command : IF condition THEN commands ENDIF'''
    condition, commands_if, lineno = p[2], p[4], str(p.lineno(1))

    p[0] =	condition[0] +\
			commands_if +\
			condition[1]

def p_whiledo_command(p):
    '''command : WHILE condition DO commands ENDWHILE'''
    condition, commands, lineno = p[2], p[4], str(p.lineno(1))
    here,jump=add_placestojump(1)
    p[0] =  here[0] +\
        condition[0] +\
        commands +\
        "JUMP" +jump[0] + "\n" +\
        condition[1]


def p_dowhile_command(p):
    '''command : DO commands WHILE condition ENDDO'''
    commands, condition,  lineno = p[2], p[4], str(p.lineno(1))
    here,jump = add_placestojump(1)
    p[0] = here[0] + \
        commands +\
        condition[0] + \
        "JUMP" + jump[0] + "\n" + \
        condition[1]


def p_seen_ID(p):
    "seen_ID :"
    declare_value(p[-1], str(p.lineno))
    initializations[p[-1]] = True
    global memory_count
    memory_count += 1
    p[0] = 1  # Assign value to seen_A

def p_for_command(p):
    '''command : FOR ID seen_ID FROM value TO value DO commands ENDFOR'''
    id, val1,val2,commands,lineno=p[2],p[5],p[7],p[9],str(p.lineno(1))
    here,jump=add_placestojump(3)

    p[0]=load_value(val2,14,lineno)+\
        load_value_addr(("it",id),lineno)+\
        "INC"+ "\n" + \
         "STORE 4" + "\n" + \
         "LOAD 14" + "\n" + \
        "STOREI 4" + "\n" + \
        load_value(val1,13,lineno)+\
        load_value_addr(("it",id),lineno)+\
        "LOAD 13" + "\n" + \
        "STOREI 4"+ "\n" + \
        here[0] +load_value(("it", id), 13, lineno) + \
         "LOAD 4" + "\n" + \
         "INC" + "\n" + \
         "STORE 4" + "\n" + \
        "LOADI 4"+"\n"+\
         "SUB 13" + "\n"+\
        "JPOS" +jump[1] +"\n"+\
        "JZERO" +jump[1] +"\n"+\
        "JUMP"+ jump[2] +"\n"+\
        here[1] + commands + \
        load_value(("it", id),0, lineno) + \
        "INC \n" + \
        "STOREI 4 \n" + \
        "JUMP" +jump[0]+"\n"+\
        here[2]
    values_declared.pop(id)

def p_fordownto_command(p):
    '''command : FOR ID seen_ID FROM value DOWNTO value DO commands ENDFOR'''
    id, val1,val2,commands,lineno=p[2],p[5],p[7],p[9],str(p.lineno(1))
    here,jump=add_placestojump(3)

    p[0]=load_value(val2,14,lineno)+\
        load_value_addr(("it",id),lineno)+\
        "INC"+ "\n" + \
         "STORE 4" + "\n" + \
         "LOAD 14" + "\n" + \
        "STOREI 4" + "\n" + \
        load_value(val1,13,lineno)+\
        load_value_addr(("it",id),lineno)+\
        "LOAD 13" + "\n" + \
        "STOREI 4"+ "\n" + \
        here[0] +load_value(("it", id), 13, lineno) + \
         "LOAD 4" + "\n" + \
         "INC" + "\n" + \
         "STORE 4" + "\n" + \
        "LOADI 4"+"\n"+\
         "SUB 13" + "\n"+\
        "JNEG" +jump[1] +"\n"+ \
         "JZERO" + jump[1] + "\n" + \
        "JUMP"+ jump[2] +"\n"+\
        here[1] + commands + \
        load_value(("it", id),0, lineno) + \
        "DEC \n" + \
        "STOREI 4 \n" + \
        "JUMP" +jump[0]+"\n"+\
        here[2]
    values_declared.pop(id)


#                 KONIEC Pętli           ###
# END command#
#     expression -> Big Production Set #
def p_expression_value(p):
    ''' expression : value '''
    value, lineno = p[1], str(p.lineno(1))
    p[0] =	 str(load_value(value, 20, lineno))

def p_expression_plus(p):
    ''' expression : value PLUS value '''
    value1, value2, lineno = p[1], p[3], str(p.lineno(1))
    p[0] = load_value(value1, 6, lineno) + \
           load_value(value2, 0, lineno) + \
           "ADD 6 \n" + \
           "STORE 20\n"

def p_expression_minus(p):
        '''expression : value MINUS value'''
        value1, value2, lineno = p[1], p[3], str(p.lineno(1))
        p[0] = load_value(value2, 6, lineno) + \
               load_value(value1, 0, lineno) + \
               "SUB 6 \n" + \
                "STORE 20\n"

def p_expression_times(p):
    '''expression : value TIMES value'''
    # 6,7 wartosci ,
    # 8 czy ujemna ,
    # 9 10 na sprawdzanie mod 2
    # 20- wyniczek- chyba można usunąć
    here,jump = add_placestojump(6)
    val1, val2, lineno = p[1],p[3], str(p.lineno(1))
    p[0] = "SUB 0 " + " \n" + \
        "STORE 8 " + "\n" + \
        "STORE 20 " + "\n" + \
        load_value(val1, 6, lineno) + \
        "JZERO " + jump[1]  +" \n" + \
        "JPOS " + jump[2] + " \n" +\
        "SUB 6 "+ " \n" + \
        "SUB 6 " + " \n" + \
        "STORE 6 " + " \n" + \
        "SUB 0 " + " \n" + \
        "INC " + " \n" + \
        "STORE 8 " + " \n" + \
        here[2] +  load_value(val2, 7, lineno) + \
        "JZERO " + jump[1] + " \n" + \
        "JPOS " + jump[4] + " \n" + \
        "SUB 7 " + " \n" + \
        "SUB 7 " + " \n" + \
        "STORE 7 " + " \n" + \
        "LOAD 8 " + " \n" + \
        "INC " + " \n" + \
        "STORE 8 " + " \n" + \
        "LOAD 7 " + " \n" + \
        ""+here[4] + "JZERO " + jump[5] +" \n" + \
        "SHIFT 2" + " \n" + \
        "SHIFT 1 " + " \n" + \
        "SUB 7" + " \n"+\
        "JZERO " + jump[0] +" \n" + \
        "LOAD 7 " + " \n" + \
        "DEC \n" + \
        "STORE 7 " + " \n" + \
        "LOAD 20 " + " \n" + \
        "ADD 6 " + " \n" + \
        "STORE 20 " + " \n" + \
        "LOAD 7 " + " \n" + \
        "JUMP " + jump[4] + " \n" + \
        here[0] + "LOAD 6 " + " \n" +\
        "SHIFT 1" + " \n" + \
        "STORE 6 " + " \n" + \
        "LOAD 7 " + " \n" + \
        "SHIFT 2" + " \n" + \
        "STORE 7 " + " \n" + \
        "JUMP " + jump[4] + " \n"+\
        here[5] + " LOAD 8 " + " \n" + \
        "DEC \n" +\
        "JZERO " + jump[3] +" \n" +\
        "LOAD 20 " + " \n" + \
        "JUMP " + jump[1] + " \n" + \
        ""+here[3]+  " LOAD 20" + " \n" + \
        "SUB 0 " + " \n" + \
        "SUB 20 " + " \n" + \
        "" + here[1]
def p_expression_div(p):
     ''' expression : value DIV value '''
     valuedividing,divider, lineno= p[1],p[3], str(p.lineno(1))
     here, jump = add_placestojump(14)
     p[0]="SUB 0 " + " \n" + \
    "STORE 8 " + "\n" + \
    "STORE 9 " + "\n" + \
    "STORE 12 " + "\n" + \
    "STORE 20 " + "\n" + \
    load_value(valuedividing, 6, lineno) + \
    "JZERO " + jump[1]  +" \n" + \
    "JPOS " + jump[2] + " \n" +\
    "SUB 6 "+ " \n" + \
    "SUB 6 " + " \n" + \
    "STORE 6 " + " \n" + \
    "SUB 0 " + " \n" + \
    "INC " + " \n" + \
    "STORE 8 " + " \n" + \
    here[2] +  load_value(divider, 7, lineno) + \
    "JZERO " + jump[1] + " \n" + \
    "JPOS " + jump[4] + " \n" + \
    "SUB 7 " + " \n" + \
    "SUB 7 " + " \n" + \
    "STORE 7 " + " \n" + \
    "SUB 0 " + " \n" + \
    "INC " + " \n" + \
    "STORE 9" + " \n"  +\
    here[4] + "LOAD 7 " + " \n" + \
    "JNEG"+ jump[5]+ " \n" + \
    "JZERO" +jump[5]+ " \n" + \
    "SUB 6 " + " \n" + \
    "JPOS " + jump[5] + " \n" + \
    "LOAD 7" + " \n" + \
    "SHIFT 1"+ " \n" + \
    "STORE 7"+ " \n" + \
    "LOAD 12"+ " \n" + \
    "INC"+ " \n" + \
    "STORE 12"+ " \n" + \
    "JUMP"+ jump[4]+ " \n" + \
    here[5] +"LOAD 12"+ " \n" + \
    "JZERO"+ jump[3]+ " \n" + \
    "DEC"+ " \n" + \
    "STORE 12" +"\n" +\
    "LOAD 7"+ " \n" + \
    "SHIFT 2"+ " \n" + \
    "STORE 7"+ " \n" + \
    "SUB 6"+ " \n" + \
    "JPOS "+jump[6]+ " \n" + \
    "LOAD 6"+ " \n" + \
    "SUB  7"+ " \n" + \
    "STORE 6"+ " \n" + \
    "LOAD 20"+ " \n" + \
    "SHIFT 1"+ " \n" + \
    "INC"+ " \n" + \
    "STORE 20"+ " \n" + \
    "JUMP"+ jump[5]+ " \n" + \
    here[6]+ "LOAD 20"+ " \n" + \
    "SHIFT 1" + " \n" + \
    "STORE 20" + " \n" + \
    "JUMP"+ jump[5]+ " \n" + \
    here[3]+"LOAD 6"+ " \n" + \
    "JZERO"+ jump[7]+ " \n" + \
    "LOAD 9"+ " \n" + \
    "JZERO"+ jump[11]+ " \n" + \
    "ADD 8"+ " \n" + \
    "DEC"+ " \n" + \
    "JZERO"+ jump[12]+ " \n" + \
    "LOAD 20" + " \n" + \
    "JUMP"+ jump[1]+ " \n" + \
    here[12] +"LOAD 20"+ " \n" + \
    "SUB 0"+ " \n" + \
    "SUB 20"+ " \n" + \
    "DEC"+ " \n" + \
    "STORE 20"+ " \n" + \
    "JUMP"+ jump[10]+ " \n" + \
    here[11] + "LOAD 8" + " \n" + \
    "JZERO " +jump[13]+ " \n" + \
    "LOAD 20" + " \n" + \
    "SUB 0" + " \n" + \
    "SUB 20" + " \n" + \
    "DEC"+ " \n" + \
    "STORE 20"+ " \n" + \
    "JUMP" +jump[10]+ " \n" + \
    here[13] +     "LOAD 20" + " \n" + \
    "JUMP" +jump[10] + " \n" + \
    here[7] +  "LOAD 9"+ " \n" + \
    "ADD 8"+ " \n" + \
    "DEC"+ " \n" + \
    "JZERO" +jump[9] + " \n" + \
    "LOAD 20" + " \n" + \
    "JUMP "+jump[10]+ " \n" + \
    here[9]+"LOAD 20"+ " \n" + \
    "SUB 0"+ " \n" + \
    "SUB 20"+ " \n" + \
    here[1]+"STORE 20"+ " \n" + \
    here[10]


def p_expression_mod(p):
    ''' expression : value MOD value'''
    valuedividing, divider, lineno = p[1], p[3], str(p.lineno(1))
    here, jump = add_placestojump(15)
    p[0]="SUB 0 " + " \n" + \
    "STORE 8 " + "\n" + \
    "STORE 9 " + "\n" + \
    "STORE 12 " + "\n" + \
    "STORE 10 " + "\n" + \
    "STORE 20 " + "\n" + \
    load_value(valuedividing, 6, lineno) + \
    "JZERO " + jump[1]  +" \n" + \
    "JPOS " + jump[2] + " \n" +\
    "SUB 6 "+ " \n" + \
    "SUB 6 " + " \n" + \
    "STORE 6 " + " \n" + \
    "SUB 0 " + " \n" + \
    "INC " + " \n" + \
    "STORE 8 " + " \n" + \
    here[2] +  load_value(divider, 7, lineno) + \
    "JZERO " + jump[1] + " \n" + \
    "JPOS " + jump[4] + " \n" + \
    "SUB 7 " + " \n" + \
    "SUB 7 " + " \n" + \
    "STORE 7 " + " \n" + \
    "SUB 0 " + " \n" + \
    "INC " + " \n" + \
    "STORE 9" + " \n"  +\
     "LOAD 7 " + " \n" + \
    here[4]+"STORE 10 " + " \n" + \
    here[14] + "LOAD 7 " + " \n" + \
    "JNEG"+ jump[5]+ " \n" + \
    "JZERO" +jump[5]+ " \n" + \
    "SUB 6 " + " \n" + \
    "JPOS " + jump[5] + " \n" + \
    "LOAD 7" + " \n" + \
    "SHIFT 1"+ " \n" + \
    "STORE 7"+ " \n" + \
    "LOAD 12"+ " \n" + \
    "INC"+ " \n" + \
    "STORE 12"+ " \n" + \
    "JUMP"+ jump[14]+ " \n" + \
    here[5] +"LOAD 12"+ " \n" + \
    "JZERO"+ jump[3]+ " \n" + \
    "DEC"+ " \n" + \
    "STORE 12" +"\n" +\
    "LOAD 7"+ " \n" + \
    "SHIFT 2"+ " \n" + \
    "STORE 7"+ " \n" + \
    "SUB 6"+ " \n" + \
    "JPOS "+jump[6]+ " \n" + \
    "LOAD 6"+ " \n" + \
    "SUB  7"+ " \n" + \
    "STORE 6"+ " \n" + \
    here[6]+ "JUMP"+ jump[5]+ " \n" + \
    here[3]+"LOAD 6"+ " \n" + \
    "JZERO"+ jump[1]+ " \n" + \
    "LOAD 9"+ " \n" + \
    "JZERO"+ jump[11]+ " \n" + \
    "LOAD 8"+ " \n" + \
    "JZERO"+ jump[12]+ " \n" + \
     "LOAD 6" + " \n" + \
     "SUB 0"+ " \n" + \
     "SUB 6" + " \n" + \
     "JUMP"+ jump[1]+ " \n" + \
    here[12] +"LOAD 6"+ " \n" + \
    "SUB 10"+ " \n" + \
    "JUMP"+ jump[1]+ " \n" + \
     here[11] + "LOAD 8" + " \n" + \
    "JZERO " +jump[13]+ " \n" + \
    "LOAD 6" + " \n" + \
    "SUB 10"+ " \n" + \
    "STORE 6" + " \n" + \
    "SUB 0"+ " \n" + \
     "SUB 6" + " \n" + \
    "JUMP" +jump[1]+ " \n" + \
     here[13] + "LOAD 6" + " \n" + \
     here[1]+"STORE 20"+ " \n"


### CONDITIONS ###
def p_condition_equal(p):
    '''condition	: value EQ value'''
    value1, value2, lineno = p[1], p[3], str(p.lineno(1))
    here,jump = add_placestojump(2)
    firstpart = load_value(value1, 6, lineno) + \
        load_value(value2, 7, lineno) + \
        "SUB  6\n" + \
        "JZERO  " + jump[1] + "\n" + \
        "JUMP" + jump[0] +"\n" +\
        here[1]
    secondpart=here[0]
    p[0] = (firstpart,
            secondpart)



def p_condition_notequal(p):
    '''condition	: value NEQ value'''
    v1, v2, lineno = p[1], p[3], str(p.lineno(1))
    here,jump = add_placestojump(1)
    firstpart = load_value(v1, 6, lineno) + \
            load_value(v2, 7, lineno) + \
            "SUB  6\n" + \
            "JZERO  " + jump[0] + "\n"
    secondpart=here[0]
    p[0] = (firstpart,
            secondpart)



def p_condition_less(p):
    '''condition	: value LE value'''
    value1, value2, lineno = p[1], p[3], str(p.lineno(1))
    here,jump = add_placestojump(1)
    firstpart = load_value(value1, 6, lineno) + \
            load_value(value2, 7, lineno) + \
            "SUB 6 \n" +\
            "JZERO  " + jump[0] + "\n" + \
            "JNEG " + jump[0] + "\n"
    secondpart = here[0]
    p[0] = ( firstpart
            ,secondpart)
def p_condition_greater(p):
    '''condition	: value GE value'''
    value1, value2, lineno = p[1], p[3], str(p.lineno(1))
    here,jump = add_placestojump(1)
    firstpart = load_value(value1, 6, lineno) + \
            load_value(value2, 7, lineno) + \
            "SUB 6 \n" +\
            "JZERO  " + jump[0] + "\n" + \
            "JPOS " + jump[0] + "\n"
    secondpart = here[0]

    p[0] = ( firstpart
            ,secondpart)

def p_condition_lessoreq(p):
    '''condition	: value LEQ value'''
    value1, value2, lineno = p[1], p[3], str(p.lineno(1))
    here,jump = add_placestojump(1)
    firstpart =  load_value(value1, 6, lineno) + \
                load_value(value2, 7, lineno) + \
                "SUB 6 \n" + \
                "JNEG " + jump[0] + "\n"
    secondpart = here[0]
    p[0] = (firstpart
            , secondpart)

def p_condition_greateroreq(p):
     '''condition	: value GEQ value'''
     value1, value2, lineno = p[1], p[3], str(p.lineno(1))
     here,jump = add_placestojump(1)
     firstpart=load_value(value1, 6, lineno) + \
            load_value(value2, 7, lineno) + \
            "SUB 6 \n" +\
            "JPOS " + jump[0] + "\n"
     secondpart= here[0]
     p[0] = ( firstpart
            ,secondpart)

### CONDITIONS ###

# value ->  . . . #
def p_value(p):
    ''' value : NUM '''
    p[0] = ("n", p[1])


def p_value_id(p):
    ''' value : identifier '''
    p[0] = (p[1])


# end #
# identifier ->  . . . #

def p_identifier_id(p):
    ''' identifier	: ID '''

    p[0] = ("id", p[1])

def p_identifier_id_in_arr(p):
    ''' identifier	: ID LBR ID RBR '''
    p[0] = ("tab", p[1], ("id", p[3]))


def p_identifier_arr(p):
    ''' identifier	: ID LBR NUM RBR '''
    p[0] = ("tab", p[1], ("n", p[3]))








def p_error(p):
    raise Exception("błąd  " + str(p.lineno) + ' linia, użycie nierozpoznawalnego znaku-  ' + str(p.value))

def isarraydeclared(id, lineno):
    if id not in arrays_declared:
        raise Exception("błąd linia " + lineno + ': użycie niezainicjowanej zmiennej tablicowej' + str(id))
    return True;

def isvaluedeclared(id, lineno):
    if id not in values_declared:
            raise Exception("błąd linia " + lineno + ': niezadeklarowana zmienna ' + str(id))


def isvalueinit(id, lineno):
    if id not in initializations:
        raise Exception("błąd linia " + lineno + ': użycie niezainicjowanej zmiennej  ' + str(id))


## PRZETWARZANIE KOMENTARZY DLA JUMPÓW ##


def add_placestojump(count):
    jumphere = []
    jumps = []
    for i in range(0, count):
        labels_val.append(-1)
        num = str(len(labels_val) - 1)
        jumphere.append(" #H" + num + "# ")
        jumps.append(" #J" + num + "# ")

    return (jumphere,jumps)


def replace_jumps(program):
    line_num = 0
    removed_labels = []
    for line in program.split("\n"):

        for matched in re.finditer("#H[0-9]+#", line):
            label_id = int(matched.group()[2:-1])
            labels_val[label_id] = line_num
        line = re.sub("#H[0-9]+#", "", line)
        removed_labels.append(line)
        line_num += 1

    removed_jumps = ""
    for line in removed_labels:
        match = re.search("#J[0-9]+#", line)
        if match is not None:
            jump_id = int(match.group()[2:-1])
            jump_line = labels_val[jump_id]
            line = re.sub("#J[0-9]+#", str(jump_line), line)
        removed_jumps += line + "\n"
    return removed_jumps

parser = yacc.yacc()
f = open(sys.argv[1], "r")
parsed = ""
try:
    parsed = parser.parse(f.read())
except Exception as e:
    print(e)
    fw = open(sys.argv[2], "w")
    fw.write(parsed)
    exit()
fw = open(sys.argv[2], "w")
fw.write(parsed)
# end #



