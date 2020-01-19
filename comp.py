
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
debug = 1

def begin(str):
    if debug == 1:
        return "##BEGIN " + str + "\n"
    else:
        return ""


def end(str):
    if debug == 1:
        return "##END " + str + "\n"
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
    declare_array(p[3], p[5], p[7], str(p.lineno))


def p_declaring_variable(p):
    ''' declarations : declarations COMMA ID  '''    #ok
    declare_value(p[3], str(p.lineno))

def p_declaring_array_end(p):
    ''' declarations :  ID LBR NUM COLON NUM RBR  '''          #ok
    declare_array(p[1], p[3], p[5], str(p.lineno))


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
    id,lineno=p[2],str(p.lineno)
    p[0] = begin("READ") +\
           load_value_addr(id, lineno) +\
           "GET \n" +\
           "STOREI 4  \n" +\
           end("READ")
    initializations[id[1]] = True;

def p_write_command(p):
    ''' command : WRITE value SEMICOLON '''
    value, lineno = p[2], str(p.lineno)
    p[0] = begin("WRITE") +\
            str(load_value(value, 0, lineno)) +\
            "PUT \n" + \
           end("WRITE")
# Stream in and out END #
# ASSIGN
def p_assigning_command(p):  # chcę mieć w 3 komórce liczbę
    ''' command : identifier ASSIGN expression SEMICOLON '''
    identifier, expression, lineno = p[1], p[3], str(p.lineno(1))
    p[0] = begin("ASSIGN") + \
           expression + \
           str(load_value_addr(identifier, lineno)) + \
           "LOAD 20\n" + \
           "STOREI 4\n" + \
           end("ASSIGN")
    initializations[identifier[1]] = True

def p_ifelse_command(p):
    '''command: IF condition THEN commands ELSE commands ENDIF '''
    condition, commands_if, commands_else, lineno = p[2], p[4], p[6], str(p.lineno(1))
    labels, jumps = add_comments_for_jumps(1)
    p[0] =	begin("IF_ELSE") +\
			condition[0] +\
			commands_if +\
			"JUMP " + jumps[0] + "\n" +\
			condition[1] +\
			commands_else +\
			labels[0] +\
			end("IF_ELSE")

def p_if_command(p):
    '''command: IF condition THEN commands ENDIF'''
    condition, commands_if, lineno = p[2], p[4], str(p.lineno(1))
    p[0] =	begin("IF") +\
			condition[0] +\
			commands_if +\
			condition[1] +\
			end("IF")

def p_whiledo_command(p):
    '''command: WHILE condition DO commands ENDWHILE'''
    condition, commands, lineno = p[2], p[4], str(p.lineno(1))
    here, jump = add_comments_for_jumps(1)
    p[0] = begin("WHILEDO") +\
        here[0] +\
        condition[0] +\
        commands +\
        "JUMP" +jump[0] + "\n" +\
        condition[1] +\
        end("WHILEDO")


def p_dowhile_command(p):
    '''command: DO commands WHILE condition ENDDO'''
    commands, condition,  lineno = p[2], p[4], str(p.lineno(1))
    here, jump = add_comments_for_jumps(1)
    p[0] = begin("WHILEDO") + \
        here[0] + \
        commands +\
        condition[0] + \
        "JUMP" + jump[0] + "\n" + \
        condition[1] + \
        end("WHILEDO")


def p_for_command(p):
    '''command: FOR ID FROM value TO value DO commands ENDFOR'''


def p_command_for_to(p):
    '''command: FOR ID FROM value TO value DO commands ENDFOR'''
    labels, jumps = add_multi_labels(3)
    temp_var = add_temp_variable()
    id_, start_val, stop_val, commands, lineno = p[2], p[4], p[6], p[8], str(p.lineno(1))
    add_variable(id, lineno)
    inits[id] = True
    p[0] = begin("FOR") + \
           load_value(stop_val, "G", lineno) + \
           load_value_addr(("id", temp_var), lineno) + \
           "STORE G\n" + \
           load_value(start_val, "H", lineno) + \
           load_value_addr(("id", iterator), lineno) + \
           "STORE H\n" + \
           labels[2] + \
           load_value(("id", temp_var), "G", lineno) + \
           load_value(("id", iterator), "H", lineno) + \
           "SUB H G\n" + \
           "JZERO H " + jumps[0] + "\n" + \
           "JUMP " + jumps[1] + "\n" + \
           labels[0] + commands + \
           load_value(("id", iterator), "H", lineno) + \
           "INC H\n" + \
           load_value_addr(("id", iterator), lineno) + \
           "STORE H\n" + \
           "JUMP " + jumps[2] + "\n" + \
           labels[1] + \
           end("FOR")

    del_variable(iterator)


def p_fordownto_command(p):
    '''command: FOR ID FROM value DOWNTO value DO commands ENDFOR'''



#                 KONIEC Pętli           ###
# END command#
#     expression -> Big Production Set #
def p_expression_value(p):
    ''' expression : value '''
    value, lineno = p[1], str(p.lineno(1))
    p[0] =	begin("SIMPLE_EXP") +\
        str(load_value(value, 20, lineno)) +\
        end("SIMPLE_EXP")

def p_expression_plus(p):
    ''' expression : value PLUS value '''
    value1, value2, lineno = p[1], p[3], str(p.lineno(1))
    p[0] = begin("PLUS") + \
           load_value(value1, 6, lineno) + \
           load_value(value2, 0, lineno) + \
           "ADD 6 \n" + \
           "STORE 20\n" + \
           end("PLUS")

def p_expression_minus(p):
        '''expression : value MINUS value'''
        value1, value2, lineno = p[1], p[3], str(p.lineno(1))
        p[0] = begin("MINUS") + \
               load_value(value1, 6, lineno) + \
               load_value(value2, 0, lineno) + \
               "SUB 6 \n" + \
                "STORE 20\n" + \
               end("MINUS")

def p_expression_times(p):
    '''expression : value TIMES value'''
    # 6,7 wartosci ,
    # 8 czy ujemna ,
    # 9 10 na sprawdzanie mod 2
    # 20- wyniczek- chyba można usunąć
    here = add_placestojump(6)
    jump = add_jumps(6)
    val1, val2, lineno = p[1],p[3], str(p.lineno)
    p[0] = begin("TIMES") + \
        "SUB 0 " + " \n" + \
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
        "" + here[1] +\
        end("TIMES")

# def p_expression_div(p):
#     ''' expression : value DIV value'''
#     valuedividing,divider, lineno= p[1],p[3], p.lineno
#     here, jump = add_comments_for_jumps(6)
#     #8 -znak a 9 znak b 10 mnożenie reszty
#     p[0]=begin("TIMES") + \
#     "SUB 0 " + " \n" + \
#     "STORE 8 " + "\n" + \
#     "STORE 9 " + "\n" + \
#     "STORE 20 " + "\n" + \
#     load_value(valuedividing, 6, lineno) + \
#     "JZERO " + jump[1]  +" \n" + \
#     "JPOS " + jump[2] + " \n" +\
#     "SUB 6 "+ " \n" + \
#     "SUB 6 " + " \n" + \
#     "STORE 6 " + " \n" + \
#     "SUB 0 " + " \n" + \
#     "INC " + " \n" + \
#     "STORE 8 " + " \n" + \
#     here[2] +  load_value(divider, 7, lineno) + \
#     "JZERO " + jump[1] + " \n" + \
#     "JPOS " + jump[4] + " \n" + \
#     "SUB 7 " + " \n" + \
#     "SUB 7 " + " \n" + \
#     "STORE 7 " + " \n" + \
#     "SUB 0 " + " \n" + \
#     "INC " + " \n" + \
#     "STORE 9" + " \n" + \
#     here[4] + "LOAD 7 " + " \n" + \
#     "SHIFT 2" + " \n" + \
#     "SHIFT 1 " + " \n" + \
#     "SUB 7" + " \n" + \
#     "STORE 9 " + " \n" + \
#     "LOAD 6 " + " \n" + \
#     "SHIFT 2" + " \n" + \
#     "SHIFT 1 " + " \n" + \
#     "SUB 6" + " \n" + \
#     "ADD 9" + " \n" + \
#     "JZERO " + jump[3] + " \n" + \
#     "JZERO " + jump[5] + " \n" + \
#     here[3] + "LOAD 7 " + " \n" + \
#     "SHIFT 2" + " \n" + \
#     "STORE 7" + " \n" + \
#     "LOAD 6" + " \n" + \
#     "SHIFT 2" + " \n" + \
#     "STORE 6" + " \n" + \
#     "SUB 0 " + " \n" + \
#     "INC " + " \n" + \
#     "STORE 10" + " \n"
#
# def p_expression_mod(p):
#                 ''' expression : value MOD value'''
#                 valuedividing, divider, lineno = p[1], p[3], p.lineno
#                 here, jump = add_comments_for_jumps(6)
#                 # 8 -znak a 9 znak b 10 mnożenie reszty
#                 p[0] = begin("TIMES") + \
#                        "SUB 0 " + " \n" + \
#                        "STORE 8 " + "\n" + \
#                        "STORE 9 " + "\n" + \
#                        "STORE 20 " + "\n" + \
#                        load_value(valuedividing, 6, lineno) + \
#                        "JZERO " + jump[1] + " \n" + \
#                        "JPOS " + jump[2] + " \n" + \
#                        "SUB 6 " + " \n" + \
#                        "SUB 6 " + " \n" + \
#                        "STORE 6 " + " \n" + \
#                        "SUB 0 " + " \n" + \
#                        "INC " + " \n" + \
#                        "STORE 8 " + " \n" + \
#                        here[2] + load_value(divider, 7, lineno) + \
#                        "JZERO " + jump[1] + " \n" + \
#                        "JPOS " + jump[4] + " \n" + \
#                        "SUB 7 " + " \n" + \
#                        "SUB 7 " + " \n" + \
#                        "STORE 7 " + " \n" + \
#                        "SUB 0 " + " \n" + \
#                        "INC " + " \n" + \
#                        "STORE 9" + " \n" + \
#                        here[4] + "LOAD 7 " + " \n" + \
#                        "SHIFT 2" + " \n" + \
#                        "SHIFT 1 " + " \n" + \
#                        "SUB 7" + " \n" + \
#                        "STORE 9 " + " \n" + \
#                        "LOAD 6 " + " \n" + \
#                        "SHIFT 2" + " \n" + \
#                        "SHIFT 1 " + " \n" + \
#                        "SUB 6" + " \n" + \
#                        "ADD 9" + " \n" + \
#                        "JZERO " + jump[3] + " \n" + \
#                        "JZERO " + jump[5] + " \n" + \
#                        here[3] + "LOAD 7 " + " \n" + \
#                        "SHIFT 2" + " \n" + \
#                        "STORE 7" + " \n" + \
#                        "LOAD 6" + " \n" + \
#                        "SHIFT 2" + " \n" + \
#                        "STORE 6" + " \n" + \
#                        "SUB 0 " + " \n" + \
#                        "INC " + " \n" + \
#                        "STORE 10" + " \n"
#  \
#                     # End #
#
#                 # condition jest tylko we WHILE oraz IF, chyba mogę tutaj ładować


### CONDITIONS ###
def p_condition_equal(p):
    '''condition	: value EQ value'''
    value1, value2, lineno = p[1], p[3], str(p.lineno(1))
    here = add_placestojump(2)
    jump = add_jumps(2)
    firstpart=begin("EQ1") + \
        load_value(value1, 6, lineno) + \
        load_value(value2, 7, lineno) + \
        "SUB  6\n" + \
        "JZERO  " + jump[1] + "\n" + \
        "JUMP" + jump[0] +"\n" +\
        here[1] +\
        end("EQ1")

    secondpart=begin("EQ2") + \
        here[0] + \
        end("EQ2")
    p[0] = (firstpart,
            secondpart)



def p_condition_notequal(p):
    '''condition	: value NEQ value'''
    v1, v2, lineno = p[1], p[3], str(p.lineno(1))
    here = add_placestojump(1)
    jump = add_jumps(1)
    firstpart=begin("NEQ1") + \
            load_value(v1, 6, lineno) + \
            load_value(v2, 7, lineno) + \
            "SUB  6\n" + \
            "JZERO  " + jump[0] + "\n" + \
            end("NEQ1")
    secondpart=begin("NEQ2") + \
            here[0] + \
            end("NEQ2")
    p[0] = (firstpart,
            secondpart)



def p_condition_less(p):
    '''condition	: value LE value'''
    value1, value2, lineno = p[1], p[3], str(p.lineno(1))
    here = add_placestojump(1)
    jump = add_jumps(1)
    firstpart=begin("Less1st") + \
            load_value(value1, 6, lineno) + \
            load_value(value2, 7, lineno) + \
            "SUB 6 \n" +\
            "JZERO  " + jump[0] + "\n" + \
            "JNEG " + jump[0] + "\n" + \
            end("Less1st")
    secondpart= begin("Less2nd") +\
                here[0] +\
                end("Less2nd")
    p[0] = ( firstpart
            ,secondpart)
def p_condition_greater(p):
    '''condition	: value GE value'''
    value1, value2, lineno = p[1], p[3], str(p.lineno(1))
    here = add_placestojump(1)
    jump = add_jumps(1)
    firstpart=begin("greater1st") + \
            load_value(value1, 6, lineno) + \
            load_value(value2, 7, lineno) + \
            "SUB 6 \n" +\
            "JZERO  " + jump[0] + "\n" + \
            "JPOS " + jump[0] + "\n" + \
              end("greater1s")
    secondpart= begin("greater2nd") +\
                here[0] +\
                end("greater2nd")

    p[0] = ( firstpart
            ,secondpart)

def p_condition_lessoreq(p):
    '''condition	: value LEQ value'''
    value1, value2, lineno = p[1], p[3], str(p.lineno(1))
    here = add_placestojump(1)
    jump = add_jumps(1)
    firstpart = begin("Lesseq1st") + \
                load_value(value1, 6, lineno) + \
                load_value(value2, 7, lineno) + \
                "SUB 6 \n" + \
                "JNEG " + jump[0] + "\n" + \
                end("Lesseq1st")
    secondpart = begin("Lesseq2nd") + \
                 here[0] + \
                 end("Lesseq2nd")

    p[0] = (firstpart
            , secondpart)

def p_condition_greateroreq(p):
     '''condition	: value GEQ value'''
     value1, value2, lineno = p[1], p[3], str(p.lineno(1))
     here = add_placestojump(1)
     jump = add_jumps(1)
     firstpart=begin("greater1st") + \
            load_value(value1, 6, lineno) + \
            load_value(value2, 7, lineno) + \
            "SUB 6 \n" +\
            "JPOS " + jump[0] + "\n" + \
              end("greater1s")
     secondpart= begin("greater2nd") +\
                here[0] +\
                end("greater2nd")
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


# end #






def p_error(p):
    raise Exception("błąd  " + str(p.lineno) + ' linia, użycie nierozpoznawalnego znaku-  ' + str(p.value))

def isarraydeclared(id, lineno):
    if id not in arrays_declared:
        raise Exception("błąd linia " + lineno + ': użycie niezainicjowanej zmiennej tablicowej' + str(id))


def isvaluedeclared(id, lineno):
    if id not in values_declared:
            raise Exception("błąd linia " + lineno + ': niezadeklarowana zmienna ' + str(id))


def isvalueinit(id, lineno):
    if id not in initializations:
        raise Exception("błąd linia " + lineno + ': użycie niezainicjowanej zmiennej  ' + str(id))


## PRZETWARZANIE KOMENTARZY DLA JUMPÓW ##

def add_jumps(count):
    jumps = []
    for i in range(0, count):
        labels_val.append(-1)
        num = str(len(labels_val) - 1)
        jumps.append(" #JUMP" + num + "# ")
    return jumps
def add_placestojump(count):
    jumphere = []
    for i in range(0, count):
        labels_val.append(-1)
        num = str(len(labels_val) - 1)
        jumphere.append(" #HERE" + num + "# ")
    return jumphere


def replace_jumps(program):
    line_num = 0
    removed_labels = []
    for line in program.split("\n"):

        for matched in re.finditer("#HERE[0-9]+#", line):
            label_id = int(matched.group()[5:-1])
            labels_val[label_id] = line_num
        line = re.sub("#HERE[0-9]+#", "", line)
        removed_labels.append(line)
        line_num += 1

    removed_jumps = ""
    for line in removed_labels:
        match = re.search("#JUMP[0-9]+#", line)
        if match is not None:
            jump_id = int(match.group()[5:-1])
            jump_line = labels_val[jump_id]
            line = re.sub("#JUMP[0-9]+#", str(jump_line), line)
        removed_jumps += line + "\n"
    return removed_jumps


def clearReg(reg):
    return "SUB 0 \n" +\
            "STORE "  + str(reg) + "\n"

def   clearRegs():
    a="SUB 0 \n"
    for i in range(10):
        a = a + " STORE " + str(i+3) + " \n"
    return a



def load_value(value,pos,lineno):
    if value[0] == "n":
        return begin("LOAD_CONST") + \
               str(generate_const_and_Store(int(value[1]), pos)) + \
               end("LOAD_CONST")
    if value[0] == "id":
        isvalueinit(value[1], lineno)
        stri=("STORE " + str(pos) + "\n") if pos != 0 else ""
        return begin("LOAD_VAR") + \
           str(load_value_addr(value, lineno)) + \
           "LOADI 4"   + "\n" + \
            stri+\
           end("LOAD_VAR")
    if value[0] == "tab":
        isvalueinit(value[1], lineno)
        stri = ("STORE " + str(pos) + "\n") if pos != 0 else ""
        return begin("LOAD_VAR") + \
               str(load_value_addr(value, lineno)) + \
               "LOADI 4" + "\n" + \
               stri + \
               end("LOAD_VAR")

def load_value_addr(value,lineno):
    if value[0] == "id":
        isvaluedeclared(value[1], lineno)
        return begin("LOAD_VAR_ADDR") + \
               str(generate_const_and_Store(values_declared[value[1]], 4)) + \
               end("LOAD_VAR_ADDR")
    elif value[0] == "tab":
        isarraydeclared(value[1], lineno)
        tab_pos, tab_start, tab_stop = arrays_declared[value[1]]
        cell_index = value[2]
        return begin("LOAD_TAB_ADDR") + \
               str(load_value(cell_index, 3, lineno)) + \
               str(generate_const_and_Store(tab_start, 5)) + \
               "SUB 0 " + "\n" + \
               "LOAD 3 " + "\n" + \
               "SUB 5" + "\n" + \
               "STORE 3" + "\n" + \
               str(generate_const_and_Store(tab_pos, 5)) + \
               "SUB 0 " + "\n" + \
               "LOAD 3" + "\n" + \
               "ADD 5" + "\n" + \
               "STORE 4" + "\n" + \
               end("LOAD_TAB_ADDR")


parser = yacc.yacc()
f = open(sys.argv[1], "r")
parsed = ""
try:
    parsed = parser.parse(f.read(), tracking=True)
except Exception as e:
    print(e)
    fw = open(sys.argv[2], "w")
    fw.write(parsed)
    exit()
fw = open(sys.argv[2], "w")
fw.write(parsed)
# end #



