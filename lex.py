import ply.lex as lex

tokens = (
	'DECLARE', 'BEGIN', 'END', 'COMMA', 'SEMICOLON',			# 0 program
	'NUM', 										# 1 liczby
	'PLUS', 'MINUS', 'TIMES', 'DIV', 'MOD',		# 2 operatory
	'EQ', 'NEQ', 'LEQ', 'GEQ', 'LE', 'GE',		# 3 relacje
	'ASSIGN',									# 4 przypisania
	'LBR', 'RBR', 'COLON',						# 5 tablice
	'IF', 'THEN', 'ELSE', 'ENDIF',				# 6 warunki IF
	'DO',										# 7 petle
	'FOR', 'FROM', 'TO', 'DOWNTO', 'ENDFOR',    # 7a FOR
	'WHILE', 'ENDDO', 'ENDWHILE',				# 7b WHILE
	'READ', 'WRITE', 							# 8 odczyt zapis
	'ID'										# 9 identyfikatory
)

# 0 PROGRAM
t_ignore_COM = r'\[[^\]]*\]'
t_DECLARE = r'DECLARE'
t_BEGIN = r'BEGIN'
t_END = r'END'
t_COMMA = r','
t_SEMICOLON = r';'

# 1 LICZBY


def t_NUM(t):
	r'0|-?[1-9][0-9]*'
	t.value = int(t.value)
	return t


# 2 OPERATORY
t_PLUS = r'PLUS'
t_MINUS = r'MINUS'
t_TIMES = r'TIMES'
t_DIV = r'DIV'
t_MOD = r'MOD'
# 3 RELACJE
t_EQ = r'EQ'
t_NEQ = r'NEQ'
t_LEQ = r'LEQ'
t_GEQ = r'GEQ'
t_LE = r'LE'
t_GE = r'GE'
# 4 PRZYPISANIA
t_ASSIGN = r'ASSIGN'
# 5 TABLICE
t_LBR = r'\('
t_RBR = r'\)'
t_COLON = r':'
# 6 WARUNKI IF
t_IF = r'IF'
t_THEN = r'THEN'
t_ELSE = r'ELSE'
t_ENDIF = r'ENDIF'
# 7 PETLE
t_DO = r'DO'
t_FOR = r'FOR'
t_FROM = r'FROM'
t_TO = r'TO'
t_DOWNTO = r'DOWNTO'
t_ENDFOR = r'ENDFOR'
t_WHILE = r'WHILE'
t_ENDDO = r'ENDDO'
t_ENDWHILE = r'ENDWHILE'
# 8 ODCZYT ZAPIS
t_READ = r'READ'
t_WRITE = r'WRITE'
# 9 IDENTYFIKATORY
t_ID = r'[_a-z]+'


def t_newline(t):
	r'\n+'
	t.lexer.lineno += t.value.count("\n")
# Define a rule so we can track line NUMs


t_ignore = ' \t'
# A string containing ignored characters (spaces and tabs)


def t_error(t):
	print("Illegal character '%s'" % t.value[0])
	t.lexer.skip(1)
# Error handling rule


lexer = lex.lex()
# Build the lexer
