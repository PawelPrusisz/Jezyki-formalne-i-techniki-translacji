#Paweł Prusisz

from sly import Lexer, Parser
from symbol_table import SymbolTable, Array, Variable
from code_generator import CodeGenerator
import sys


class ImpLexer(Lexer):
    tokens = {VAR, BEGIN, END, PID, NUM, IF, THEN, ELSE, ENDIF, WHILE, DO, ENDWHILE, REPEAT, UNTIL, FOR, FROM, TO,
              DOWNTO, ENDFOR, READ, WRITE, EQ, NEQ, GE, LE, GEQ, LEQ, ASSIGN, PLUS, MINUS, TIMES, DIV, MOD}
    literals = {',', ':', ';', '[', ']', '-'}
    ignore = ' \t'

    @_(r'\([^\)]*\)')
    def ignore_comment(self, t):
        self.lineno += t.value.count('\n')

    @_(r'\n+')
    def ignore_newline(self, t):
        self.lineno += len(t.value)

    VAR = r"VAR"
    BEGIN = r"BEGIN"

    ENDWHILE = r"ENDWHILE"
    ENDFOR = r"ENDFOR"
    ENDIF = r"ENDIF"
    END = r"END"

    WHILE = r"WHILE"
    FOR = r"FOR"
    IF = r"IF"

    THEN = r"THEN"
    ELSE = r"ELSE"

    DOWNTO = r"DOWNTO"
    DO = r"DO"
    TO = r"TO"

    FROM = r"FROM"
    REPEAT = r"REPEAT"
    UNTIL = r"UNTIL"

    READ = r"READ"
    WRITE = r"WRITE"

    PLUS = r"PLUS"
    MINUS = r"MINUS"
    TIMES = r"TIMES"
    DIV = r"DIV"
    MOD = r"MOD"


    ASSIGN = r"ASSIGN"
    NEQ = r"NEQ"
    GEQ = r"GEQ"
    LEQ = r"LEQ"
    EQ = r"EQ"
    GE = r"GE"  
    LE = r"LE"
    PID = r"[_a-z]+"

    @_(r'\d+')
    def NUM(self, t):
        t.value = int(t.value)
        return t

    def error(self, t):
        raise Exception(f"Illegal character '{t.value[0]}'")


class ImpParser(Parser):
    tokens = ImpLexer.tokens
    symbols = SymbolTable()
    code = None
    
    consts = set()

    @_('VAR declarations BEGIN commands END', 'BEGIN commands END')
    def program(self, p):
        self.code = CodeGenerator(p.commands, self.symbols)
        return self.code

    @_('declarations "," PID', 'PID')
    def declarations(self, p):
        self.symbols.add_variable(p[-1])

    @_('declarations "," PID "[" NUM ":" NUM "]" ')
    def declarations(self, p):
        self.symbols.add_array(p[2], p[4], p[6])

    @_('declarations "," PID "[" "-" NUM ":" NUM "]" ')
    def declarations(self, p):
        self.symbols.add_array(p[2], -p[5], p[7])

    @_('PID "[" NUM ":" NUM "]"')
    def declarations(self, p):
        self.symbols.add_array(p[0], p[2], p[4])

    @_('PID "[" "-" NUM ":" NUM "]"')
    def declarations(self, p):
        self.symbols.add_array(p[0], -p[3], p[5])

    @_('commands command')
    def commands(self, p):
        return p[0] + [p[1]]

    @_('command')
    def commands(self, p):
        return [p[0]]

    @_('identifier ASSIGN expression ";"')
    def command(self, p):
        return "assign", p[0], p[2]

    @_('IF condition THEN commands ELSE commands ENDIF')
    def command(self, p):
        resp = "ifelse", p[1], p[3], p[5], self.consts.copy()
        self.consts.clear()
        return resp

    @_('IF condition THEN commands ENDIF')
    def command(self, p):
        resp = "if", p[1], p[3], self.consts.copy()
        self.consts.clear()
        return resp

    @_('WHILE condition DO commands ENDWHILE')
    def command(self, p):
        resp = "while", p[1], p[3], self.consts.copy()
        self.consts.clear()
        return resp

    @_('REPEAT commands UNTIL condition ";"')
    def command(self, p):
        return "until", p[3], p[1]

    @_('FOR PID FROM value TO value DO commands ENDFOR')
    def command(self, p):
        resp = "forup", p[1], p[3], p[5], p[7], self.consts.copy()
        self.consts.clear()
        return resp

    @_('FOR PID FROM value DOWNTO value DO commands ENDFOR')
    def command(self, p):
        resp = "fordown", p[1], p[3], p[5], p[7], self.consts.copy()
        self.consts.clear()
        return resp

    @_('READ identifier ";"')
    def command(self, p):
        return "read", p[1]

    @_('WRITE value ";"')
    def command(self, p):
        if p[1][0] == "const":
            self.consts.add(int(p[1][1]))
        return "write", p[1]

    @_('value')
    def expression(self, p):
        return p[0]

    @_('value PLUS value')
    def expression(self, p):
        return "add", p[0], p[2]

    @_('value MINUS value')
    def expression(self, p):
        return "sub", p[0], p[2]

    @_('value TIMES value')
    def expression(self, p):
        return "mul", p[0], p[2]

    @_('value DIV value')
    def expression(self, p):
        return "div", p[0], p[2]

    @_('value MOD value')
    def expression(self, p):
        return "mod", p[0], p[2]

    @_('value EQ value')
    def condition(self, p):
        return "eq", p[0], p[2]

    @_('value NEQ value')
    def condition(self, p):
        return "neq", p[0], p[2]

    @_('value LE value')
    def condition(self, p):
        return "le", p[0], p[2]

    @_('value GE value')
    def condition(self, p):
        return "ge", p[0], p[2]

    @_('value LEQ value')
    def condition(self, p):
        return "leq", p[0], p[2]

    @_('value GEQ value')
    def condition(self, p):
        return "geq", p[0], p[2]

    @_('NUM')
    def value(self, p):
        return "const", p[0]

    @_('"-" NUM')
    def value(self, p):
        return "const", -p[1]

    @_('identifier')
    def value(self, p):
        return "load", p[0]

    @_('PID')
    def identifier(self, p):
        if p[0] in self.symbols:
            return p[0]
        else:
            return "unVARd", p[0]

    @_('PID "[" PID "]"')
    def identifier(self, p):
        if p[0] in self.symbols and type(self.symbols[p[0]]) == Array:
            if p[2] in self.symbols and type(self.symbols[p[2]]) == Variable:
                return "array", p[0], ("load", p[2])
            else:
                return "array", p[0], ("load", ("unVARd", p[2]))
        else:
            raise Exception(f"UnVARd array {p[0]}")

    @_('PID "[" "-" PID "]"')
    def identifier(self, p):
        if p[0] in self.symbols and type(self.symbols[p[0]]) == Array:
            if p[2] in self.symbols and type(self.symbols[p[2]]) == Variable:
                return "array", p[0], ("load", -p[3])
            else:
                return "array", p[0], ("load", ("unVARd", -p[3]))
        else:
            raise Exception(f"UnVARd array {p[0]}")

    @_('PID "[" NUM "]"')
    def identifier(self, p):
        if p[0] in self.symbols and type(self.symbols[p[0]]) == Array:
            return "array", p[0], p[2]
        else:
            raise Exception(f"UnVARd array {p[0]}")

    @_('PID "[" "-" NUM "]"')
    def identifier(self, p):
        if p[0] in self.symbols and type(self.symbols[p[0]]) == Array:
            return "array", p[0], -p[3]
        else:
            raise Exception(f"UnVARd array {p[0]}")

    def error(self, token):
        raise Exception(f"Syntax error: '{token.value}' in line {token.lineno}")


sys.tracebacklimit = 0
lex = ImpLexer()
pars = ImpParser()
with open(sys.argv[1]) as in_f:
    text = in_f.read()

pars.parse(lex.tokenize(text))
code_gen = pars.code
code_gen.gen_code()
with open(sys.argv[2], 'w') as out_f:
    for line in code_gen.code:
        print(line, file=out_f)
