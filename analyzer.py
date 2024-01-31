from lexer import *
from error import Error
from ast_module import *


class Analyzer():
    """Takes sequenced tokens and turns them into AST objects, sending them to Interpreter"""

    def __init__(self, code):
        """Creates an instance of Analyzer

        Arguments:
            code {str} -- All the code written by the user
        """
        self.code = code
        self.lexer = Lexer(code)        # Sends code to the Lexer
        self.current_token = self.lexer.next_token()        # Fetches the next token

    def block(self, end_block):
        """Returns a code block. Wraps entire code into this object

        Arguments:
            end_block {str} -- The block at which statements will no longer be added to this block

        Returns:
            Block -- Contains a list of Statement in it
        """
        statement_list = []
        while self.current_token.value not in end_block:
            statement_list.append(self.statement())

        block = Block(statement_list)
        return block

    def statement(self):
        """Checks for the first token in each statement and dives into the appropriate function

        Returns:
            Class(AST) -- Class is the type of Statement that stores all tokens of the statement in it
        """
        token = self.current_token
        value = token.value
        if token.type == 'KEYWORD':
            if value == 'PROCEDURE':
                node = self.procedure()
            elif value == 'FUNCTION':
                node = self.function()
            elif value == 'CALL':
                node = self.call()
            elif value == 'RETURN':
                node = self.return_value()
            elif value == 'INPUT':
                node = self.input()
            elif value == 'OUTPUT':
                node = self.output()
            elif value == 'DECLARE':
                node = self.declarations()
            elif value == 'CONSTANT':
                node = self.constant()
            elif value == 'IF':
                node = self.selection()
            elif value == 'CASE':
                node = self.case()
            elif value == 'FOR':
                node = self.iteration()
            elif value == 'REPEAT':
                node = self.post_condition_loop()
            elif value == 'WHILE':
                node = self.pre_condition_loop()
            elif value == 'OPENFILE':
                node = self.open_file()
            elif value == 'READFILE':
                node = self.read_file()
            elif value == 'WRITEFILE':
                node = self.write_file()
            elif value == 'CLOSEFILE':
                node = self.close_file()
            elif value == 'TYPE':
                node = self.declare_type()
        elif token.type == 'EOF':
            Error().eof_error('Unexpected EOF')
        elif token.type == 'VARIABLE':
            node = self.assignment()
        else:
            Error().syntax_error(self.current_token.value, self.lexer.line_number)

        return Statement(node)

    def check_token_type(self, token_type):
        """Checks whether the current token is semantically correct

        Arguments:
            token_type {str} -- The type of the token to be checked
        """
        if self.current_token.type == token_type:
            token = self.current_token

            # Take out the next token from Lexer
            self.current_token = self.lexer.next_token()
        else:
            Error().syntax_error(self.current_token.value, self.lexer.line_number)

    def check_token_value(self, token_value):
        """Checks whether the current token is semantically correct

        Arguments:
            token_value {str} -- The value of the token to be checked
        """
        if self.current_token.value == token_value:
            token = self.current_token

            # Take out the next token from Lexer
            self.current_token = self.lexer.next_token()
        else:
            Error().token_error(self.current_token.value, self.lexer.line_number, token_value)

    # START: Operation Handling

    def output(self):
        """Verifies and returns an output statement

        Returns:
            Output -- Constains the expression to be outputted
        """
        self.check_token_value('OUTPUT')
        return Output(self.expression())

    def expression(self):
        """Verifies an expression and maintains order of precedence

        Returns:
            BinaryOperation -- The left and right part of the operation followed by the operator itself
        """
        node = self.term()

        while self.current_token.value in ('+', '-'):
            operator = Operator(self.current_token)
            self.check_token_type('OPERATION')

            node = BinaryOperation(node, operator, self.term())

        return node

    def term(self):
        """Verifies a term within an expression and maintains order of precedence

        Returns:
            BinaryOperation -- The left and right part of the operation followed by the operator itself
        """
        node = self.factor()

        while self.current_token.value in ('*', '/', 'DIV', 'MOD', '^'):
            operator = Operator(self.current_token)
            self.check_token_type('OPERATION')

            node = BinaryOperation(node, operator, self.factor())

        return node

    def factor(self):
        """Verifies a factor within a term

        Returns:
            node (of any class) -- the value of the factor encapsulated in its respective AST class
        """
        token = self.current_token
        if token.type == 'OPERATION':
            if token.value == '+':
                self.check_token_type('OPERATION')
                node = UnaryOperation(token, self.factor())
            elif token.value == '-':
                self.check_token_type('OPERATION')
                node = UnaryOperation(token, self.factor())
        elif token.type == 'INTEGER':
            self.check_token_type('INTEGER')
            node = Value(token)
        elif token.type == 'REAL':
            self.check_token_type('REAL')
            node = Value(token)
        elif token.type == 'BOOLEAN':
            if token.value == 'TRUE':
                token.value = True
            elif token.value == 'FALSE':
                token.value = False
            self.check_token_type('BOOLEAN')
            node = Value(token)
        elif token.type == 'STRING':
            self.check_token_type('STRING')
            node =  Value(token)
        elif token.type == 'BUILTIN_FUNCTION':
            node = self.builtin_function()
        elif token.value == 'CALL':
            node = self.call()
        elif token.type == 'PARENTHESIS':
            if self.current_token.value == '(':
                self.check_token_value('(')
                node = self.expression()
                self.check_token_value(')')
            else:

                elements = []

                self.check_token_value('[')
                elements.append(self.expression())

                while self.current_token.type == 'COMMA':
                    self.check_token_type('COMMA')
                    elements.append(self.expression())

                self.check_token_value(']')
                print(elements)
                node = AssignArray(elements)
        elif token.type == 'VARIABLE':
            node = self.variable_value()

            if self.current_token.value == '.':
                self.check_token_type('PERIOD')
                node = TypeValue(node, self.variable_name())
        else:
            raise Error().syntax_error(self.lexer.current_char, self.lexer.line_number)
        return node

    # END: Operation Handling

    # START: Constants

    def constant(self):
        """Verifies the declaration for a CONSTANT declaration

        Returns:
            ConstantDeclaration -- The name and value of CONSTANT encapsulated in the ConstantDeclaration AST class
        """

        # CONSTANT constant <- expression
        self.check_token_value('CONSTANT')
        constant = VariableName(self.current_token)
        self.check_token_type('VARIABLE')
        self.check_token_type('ASSIGNMENT')
        value = self.expression()

        return ConstantDeclaration(constant, value)

    # END: Constants

    # START: Declaration

    def declarations(self):
        """Verifies the declarations within a statement

        Returns:
            Declarations -- The declarations made within a statement
        """

        # DECLARE variable_declarations COLON type
        self.check_token_value('DECLARE')
        return Declarations(self.variable_declarations())

    def variable_declarations(self):
        """Verifies the declaration

        Returns:
            list{Declaration} -- A list of all declarations with their data type
        """
        # variable_declaration COMMA (variable_declaration)*
        variables = [VariableName(self.current_token)]
        self.check_token_type('VARIABLE')

        while self.current_token.type == 'COMMA':
            self.check_token_type('COMMA')
            variables.append(VariableName(self.current_token))
            self.check_token_type('VARIABLE')

        self.check_token_value(':')

        data_type = self.data_type()

        declarations = [
            Declaration(variable, data_type)
            for variable in variables
        ]

        return declarations

    def data_type(self):
        """Verifies the data type for declarations

        Returns:
            DataType/Array -- The data type (and dimensions in case of ARRAY)
        """
        token = self.current_token
        self.check_token_type('VARIABLE')

        if token.value != 'ARRAY':
            data_type = DataType(token)
            return data_type
        else:
            # ARRAY PARENTHESIS dimensions PARENTHESIS OF type
            self.check_token_value('[')
            dimensions = self.dimensions()
            self.check_token_value(']')
            self.check_token_value('OF')
            data_type = self.data_type()
            return Array(dimensions, data_type)


    # START: Array Declaration

    def dimensions(self):
        """Verifies the dimensions used in declaring an ARRAY

        Returns:
            Dimensions -- A list of upper and lower bounds of an ARRAY
        """
        # expression COLON expression (COMMA expression COLON expression)*
        dimensions = []
        lower_bound = self.bound()
        self.check_token_value(':')
        upper_bound = self.bound()
        dimensions.append(Dimension(lower_bound, upper_bound))

        while self.current_token.type == 'COMMA':
            self.check_token_type('COMMA')
            lower_bound = self.bound()
            self.check_token_value(':')
            upper_bound = self.bound()
            dimensions.append(Dimension(lower_bound, upper_bound))

        return Dimensions(dimensions)

    def bound(self):
        """
        Returns:
            Bound -- The bound of an ARRAY
        """
        return Bound(self.expression())

    # END: Array Declaration

    # END: Declaration

    # START: Variable Assignment

    def assignment(self):
        """Verifies the proper assignment to an instance

        Returns:
            Assignment -- Contains the name of the instance to be assigned to and the value
        """

        # variable_name ASSIGNMENT expression
        left = self.variable_name()
        self.check_token_type('ASSIGNMENT')
        right = self.expression()
        assignment = Assignment(left, right)

        return assignment

    def variable_name(self):
        """Verifies the syntax of the name of various types of instances

        Returns:
            VariableName/ElementName/TypeName -- The name of the instance
        """

        # variable (indexes)*
        object_ = VariableName(self.current_token)
        self.check_token_type('VARIABLE')

        indexes = []

        if self.current_token.value == '[':
           self.check_token_value('[')
           indexes.append(self.index())
           while self.current_token.type == 'COMMA':
               self.check_token_type('COMMA')
               indexes.append(self.index())
           self.check_token_value(']')

           object_ = ElementName(object_, indexes)

        if self.current_token.value == '.':
            self.check_token_type('PERIOD')
            object_ = TypeName(object_, self.variable_name())

        return object_

    def index(self):
        """Verifies an index that is within [ and ]

        Returns:
            Index -- The expression that will make up the index
        """
        return Index(self.expression())

    def variable_value(self):
        """Verifies the syntax of the value of various types of instances

        Returns:
            VariableValue/ElementValue/TypeValue -- The value of the instance
        """
        object_ = VariableValue(self.current_token)
        self.check_token_type('VARIABLE')

        indexes = []

        if self.current_token.value == '[':
           self.check_token_value('[')
           indexes.append(self.index())
           while self.current_token.type == 'COMMA':
               self.check_token_type('COMMA')
               indexes.append(self.index())
           self.check_token_value(']')

           object_ = ElementValue(object_, indexes)

        if self.current_token.value == '.':
            self.check_token_type('PERIOD')

            object_ = TypeValue(VariableName(object_), self.variable_name())

        return object_

    # END: Variable Assignment

    # START: Input

    def input(self):
        """Verifies the string given and the instance it will be stored in

        Returns:
            Input -- The string to be displayed on the console and the instance where the value entered will be stored
        """

        # INPUT (STRING) VARIABLE
        self.check_token_value('INPUT')
        if self.current_token.type == 'STRING':
            input_string = self.current_token.value
            self.check_token_type('STRING')
            var_node = VariableName(self.current_token)
            self.check_token_type('VARIABLE')
        else:
            input_string = '> '
            var_node = VariableName(self.current_token)
            self.check_token_type('VARIABLE')

        indexes = []

        if self.current_token.value == '[':
           self.check_token_value('[')
           indexes.append(self.index())
           while self.current_token.type == 'COMMA':
               self.check_token_type('COMMA')
               indexes.append(self.index())
           self.check_token_value(']')

           var_node = ElementName(var_node, indexes)


        return Input(input_string, var_node)

    # END: Input

    def logical_expression(self):
        """Verifies the syntax for a binary logical operation while maintaining the order of precedence

        Returns:
            BinaryLogicalOperation -- The operator and operations on its left and right
        """
        node = self.logical_term()
        while self.current_token.value == 'OR':
            token = Operator(self.current_token)
            self.check_token_type('LOGICAL')

            node = BinaryLogicalOperation(node, token, self.logical_term())

        return node

    def logical_term(self):
        """Verifies the syntax for a binary logical operation

        Returns:
            BinaryLogicalOperation -- The operator and operations on its left and right
        """
        node = self.logical_factor()

        while self.current_token.value == 'AND':
            token = Operator(self.current_token)
            self.check_token_type('LOGICAL')

            node = BinaryLogicalOperation(node, token, self.logical_factor())

        return node

    def logical_factor(self):
        """Verifies a factor within a binary logical operation

        Returns:
            node (of any class) -- The value of a logical factor encapsulated in its respective AST class
        """
        token = self.current_token
        if token.value == 'NOT':
            self.check_token_type('LOGICAL')
            node = UnaryLogicalOperation(Operator(token), self.logical_factor())
        elif token.type == 'PARENTHESIS':
            self.check_token_value('(')
            node = self.logical_expression()
            self.check_token_value(')')
        elif token.value == 'CALL':
            node = self.call()
        elif token.type == 'BOOLEAN':
            node = self.factor()
        elif token.type == 'BUILTIN_FUNCTION':
            node = self.builtin_function()
        else:
            node = self.condition()

        return node

    def condition(self):
        """Verifies the syntax for a conditional statement

        Returns:
            Condition -- The left and right side of a condition with the conditional operator
        """
        # expression COMPARISON expression
        left = self.expression()
        comparison = self.current_token
        self.check_token_type('COMPARISON')
        right = self.expression()

        condition = Condition(left, comparison, right)
        return condition

    # START: Selection

    def selection(self):
        """Verifies the syntax for a selection statement

        Returns:
            Selection -- A list of all selections within a block
        """
        #   (selection_statement)*
        # ENDIF
        selection_list = []

        while self.current_token.value != 'ENDIF':
            selection_list.append(self.selection_statement())

        self.check_token_value('ENDIF')

        selection = Selection(selection_list)
        return selection

    def selection_statement(self):
        """Verifies a statement within a selection block

        Returns:
            SelectionStatement -- The conditional statement and block of code within the selection statement
        """
        # (IF|ELSEIF condition THEN
        #   block) | ELSE block
        if self.current_token.value != 'ELSE':
            self.check_token_type('KEYWORD')
            condition = self.logical_expression()
            self.check_token_value('THEN')
            block = self.block(['ELSE', 'ELSEIF', 'ENDIF'])
        else:
            self.check_token_type('KEYWORD')
            condition = None
            block = self.block(['ENDIF'])

        selection_statement = SelectionStatement(condition, block)
        return selection_statement

    # END: Selection

    # START: Case

    def case(self):
        """Verifies the variable and ENDCASE of a CASE statement

        Returns:
            Case -- A list of statements within the CASE block
        """
        # CASE OF variable
        # CASE expression COLON block
        case_list = []

        self.check_token_type('KEYWORD')
        self.check_token_value('OF')
        left = self.variable_value()

        while self.current_token.value != 'ENDCASE':
            case_list.append(self.case_statement(left))

        self.check_token_value('ENDCASE')

        return Case(case_list)


    def case_statement(self, left):
        """Verifies a CASE statement

        Arguments:
            left {VariableValue} -- The value to be checked against

        Returns:
            SelectionStatement -- The condition and block on the statement
        """
        if self.current_token.value != 'OTHERWISE':
            self.check_token_value('CASE')
            condition = self.case_condition(left)

            block = self.block(['CASE', 'OTHERWISE', 'ENDCASE'])
        else:
            condition = None
            self.check_token_type('KEYWORD')
            block = self.block(['ENDCASE'])

        return SelectionStatement(condition, block)

    def case_condition(self, left):
        """Verifies the types of conditions used for CASE statements

        Arguments:
            left {VariableValue} -- The value to be checked against

        Returns:
            Condition -- The left and right side of a condition with the conditional operator
        """

        # variable (TO, .., ,) expression
        options = []
        options.append(self.expression())

        # FIXME October 25, 2019: Does not work for ASCII ranges
        if self.current_token.value == 'TO' or self.current_token.value == '..':
            if self.current_token.value == 'TO':
                self.check_token_value('TO')
            else:
                self.check_token_value('..')
            start = options[-1]
            del options[-1]
            right = Range(start, self.expression())
        else:
            while self.current_token.type != 'COLON':
                if self.current_token.type == 'COMMA':
                    self.check_token_type('COMMA')
                    options.append(self.expression())

            right = Options(options)


        self.check_token_type('COLON')

        comparison = Token('COMPARISON', '=')

        condition = Condition(left, comparison, right)
        return condition

    # END: Case

    # START: Iteration

    def iteration(self):
        """Verifies the syntax of a FOR loop

        Returns:
            Iteration -- All components needed for an iterative block
        """
        # FOR VARIABLE ASSIGNMENT INTEGER TO INTEGER (STEP INTEGER)
        #   block
        # ENDFOR
        self.check_token_type('KEYWORD')
        variable = self.variable_name()
        self.check_token_value('<-')
        start = self.expression()
        assignment = Assignment(variable, start)
        self.check_token_value('TO')
        end = self.expression()

        if self.current_token.value == 'STEP':
            self.check_token_type('KEYWORD')
            step = self.expression()
        else:
            step = Value(Token('INTEGER', 1))

        block = self.block(['ENDFOR'])
        self.check_token_type('KEYWORD')

        return Iteration(variable, assignment, end, step, block)

    # END: Iteration

    # START: Post-condition Loop

    def post_condition_loop(self):
        """Verifies the syntax for a DO..UNTIL loop

        Returns:
            Loop -- The condition and code block of the loop
        """

        # REPEAT
        #   block
        # UNTIL condition
        self.check_token_type('KEYWORD')
        block = self.block(['UNTIL'])
        self.check_token_type('KEYWORD')
        condition = self.logical_expression()
        loop = Loop(condition, block, False)

        return loop

    # END: Post-Condition Loop

    # START: Pre-condition Loop

    def pre_condition_loop(self):
        """Verifies the syntax for a WHILE..ENDWHILE loop

        Returns:
            Loop -- The condition and code block of the loop
        """

        # WHILE condition
        #   block
        # ENDWHILE
        self.check_token_type('KEYWORD')
        condition = self.logical_expression()
        block = self.block(['ENDWHILE'])
        self.check_token_type('KEYWORD')
        loop = Loop(condition, block, True)

        return loop

    # END: Pre-Condition Loop

    # START: Built-in Function

    def builtin_function(self):
        """Verifies the syntax of built-in functions

        Returns:
            BuiltInFunction -- name and parameters of the function
        """
        name = self.current_token
        self.check_token_type('BUILTIN_FUNCTION')
        self.check_token_value('(')

        parameters = []

        while self.current_token.value != ')':
            parameters.append(self.expression())
            if self.current_token.type == 'COMMA':
                self.check_token_type('COMMA')
            else:
                break

        self.check_token_value(')')

        return BuiltInFunction(name, parameters)

    # END: Built-in Function

    def parameter(self):
        """Verifies the parameters used when declaring a procedure/function

        Returns:
            Parameter -- The metadata of the parameter
        """

        # VARIABLE : DATA_TYPE
        reference_type = self.current_token
        if self.current_token.value in ['BYREF', 'BYVAL']:
            self.check_token_type('KEYWORD')
        variable = VariableName(self.current_token)
        self.check_token_type('VARIABLE')
        self.check_token_type('COLON')
        data_type = self.data_type()

        return Parameter(variable, data_type, reference_type)


    def call(self):
        """Verifies the syntax of a call to a procedure/function

        Returns:
            FunctionCall -- The name and parameters passed into the procedure/function
        """

        # CALL value((parameter)*)
        self.check_token_type('KEYWORD')
        name = Value(self.current_token)
        self.check_token_type('VARIABLE')
        self.check_token_value('(')

        parameters = []

        while self.current_token.value != ')':
            parameters.append(self.expression())
            if self.current_token.type == 'COMMA':
                self.check_token_type('COMMA')
            else:
                break

        self.check_token_value(')')

        return FunctionCall(name, parameters)


    # START: Procedure

    def procedure(self):
        """Verifies the declaration of a procedure

        Returns:
            Function -- The metadata of the procedure being declared
        """

        # PROCEDURE variable(parameters)
        #   block
        # ENDPROCEDURE
        self.check_token_type('KEYWORD')
        name = Value(self.current_token)
        self.check_token_type('VARIABLE')
        self.check_token_value('(')

        parameters = []

        while self.current_token.value != ')':
            parameters.append(self.parameter())
            if self.current_token.type == 'COMMA':
                self.check_token_type('COMMA')
            else:
                break

        self.check_token_value(')')
        node = Function(name, parameters, self.block(['ENDPROCEDURE']), None)
        self.check_token_type('KEYWORD')

        return node

    # END: Procedure

    # START: Function

    def function(self):
        """Verifies the declaration of a function

        Returns:
            Function -- The metadata of the function being declared
        """

        # FUNCTION variable(parameters) : data_type
        #   block
        # ENDFUNCTION
        self.check_token_type('KEYWORD')
        name = Value(self.current_token)
        self.check_token_type('VARIABLE')
        self.check_token_value('(')

        parameters = []

        while self.current_token.value != ')':
            parameters.append(self.parameter())
            if self.current_token.type == 'COMMA':
                self.check_token_type('COMMA')
            else:
                break

        self.check_token_value(')')
        self.check_token_type('COLON')

        return_type = self.data_type()

        node = Function(name, parameters, self.block(['ENDFUNCTION']), return_type)
        self.check_token_type('KEYWORD')

        return node

    def return_value(self):
        self.check_token_type('KEYWORD')
        return self.expression()

    # END: Function

    # START: File

    def open_file(self):
        """Verifies the syntax of opening a file

        Returns:
            File -- The name and access type of a file
        """

        self.check_token_type('KEYWORD')
        file_name = Value(self.current_token)
        self.check_token_type('STRING')
        self.check_token_value('FOR')
        file_mode = FileMode(self.current_token)
        self.check_token_type('FILE_MODE')

        return File(file_name, file_mode)

    def read_file(self):
        """Verifies the syntax of reading from a file

        Returns:
            ReadFile -- The name and instance for storing line of a file
        """

        self.check_token_type('KEYWORD')
        file_name = VariableValue(self.current_token)
        self.check_token_type('STRING')
        self.check_token_type('COMMA')
        variable = VariableName(self.current_token)
        self.check_token_type('VARIABLE')

        return ReadFile(file_name, variable)

    def write_file(self):
        """Verifies the syntax of writing to a file

        Returns:
            WriteFile -- The name and value to write to a file
        """
        self.check_token_type('KEYWORD')
        file_name = VariableValue(self.current_token)
        self.check_token_type('STRING')
        self.check_token_type('COMMA')
        line = self.expression()

        return WriteFile(file_name, line)

    def close_file(self):
        """Verifies the syntax of closing file

        Returns:
            CloseFile -- The name of the file to close
        """
        self.check_token_type('KEYWORD')
        file_name = VariableValue(self.current_token)
        self.check_token_type('STRING')

        return CloseFile(file_name)

    # END: File

    # START: Type

    def declare_type(self):
        """Verifies the declaration of TYPE

        Returns:
            TypeDeclaration -- Name and code block of the TYPE declaration
        """
        self.check_token_type('KEYWORD')
        type_name = Value(self.current_token)
        self.check_token_type('VARIABLE')
        block = self.block(['ENDTYPE'])
        self.check_token_type('KEYWORD')

        return TypeDeclaration(type_name, block)

    # END: Type
