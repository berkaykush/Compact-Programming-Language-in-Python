from .abstract_syntax_tree import AssignmentStatementNode
from .error import InterpreterError
from .tokens import Token
from .visit_ast_node import ASTNodeVisitor
from .program_stack import ProgramStack, StackFrame


class Interpreter(ASTNodeVisitor):
    PROGRAM_STACK = ProgramStack()

    def __init__(self, ast):
        self.__ast = ast
        self.__zero_token = None  # Used for reporting errors.

    def interpret(self):
        if self.__ast is None:
            return ""

        return self.visit(self.__ast)

    def visitVarNode(self, ast_node):
        curr_stack_frame = Interpreter.PROGRAM_STACK.peek()

        var_name = ast_node.val
        var_val = curr_stack_frame.get(var_name)

        if var_val is None:
            self.__error(
                f'Variable "{var_name}" is not defined',
                ast_node.token,
            )

        return curr_stack_frame.get(ast_node.val)

    def visitNumberNode(self, ast_node):
        if ast_node.val == 0:
            self.__zero_token = ast_node.token

        return ast_node.val

    def visitBoolNode(self, ast_node):
        if ast_node.val == "true":
            return True

        return False

    def visitStrNode(self, ast_node):
        return ast_node.val

    def visitUnaryOpNode(self, ast_node):
        match (ast_node.op_token.type_):
            case Token.PLUS:
                return +self.visit(ast_node.child_node)
            case Token.MINUS:
                return -self.visit(ast_node.child_node)
            case Token.K_NOT:
                return not self.visit(ast_node.child_node)

    def visitBinaryOpNode(self, ast_node):
        match (ast_node.op_token.type_):
            case Token.PLUS:
                return self.visit(ast_node.left_node) + self.visit(ast_node.right_node)
            case Token.MINUS:
                return self.visit(ast_node.left_node) - self.visit(ast_node.right_node)
            case Token.MULTIPLICATION:
                return self.visit(ast_node.left_node) * self.visit(ast_node.right_node)
            case Token.INT_DIVISION:
                right_val = self.visit(ast_node.right_node)

                if right_val == 0:
                    self.__error(InterpreterError.DIVISION_BY_ZERO, self.__zero_token)

                return self.visit(ast_node.left_node) // right_val
            case Token.FLOAT_DIVISION:
                right_val = self.visit(ast_node.right_node)

                if right_val == 0:
                    self.__error(InterpreterError.DIVISION_BY_ZERO, self.__zero_token)

                return self.visit(ast_node.left_node) / right_val
            case Token.MODULO:
                right_val = self.visit(ast_node.right_node)

                if right_val == 0:
                    self.__error(InterpreterError.MODULO_BY_ZERO, self.__zero_token)

                return self.visit(ast_node.left_node) % right_val
            case Token.EQUALS:
                return self.visit(ast_node.left_node) == self.visit(ast_node.right_node)
            case Token.NOT_EQUALS:
                return self.visit(ast_node.left_node) != self.visit(ast_node.right_node)
            case Token.LESS_THAN:
                return self.visit(ast_node.left_node) < self.visit(ast_node.right_node)
            case Token.LESS_THAN_OR_EQUALS:
                return self.visit(ast_node.left_node) <= self.visit(ast_node.right_node)
            case Token.GREATER_THAN:
                return self.visit(ast_node.left_node) > self.visit(ast_node.right_node)
            case Token.GREATER_THAN_OR_EQUALS:
                return self.visit(ast_node.left_node) >= self.visit(ast_node.right_node)
            case Token.K_AND:
                return self.visit(ast_node.left_node) and self.visit(
                    ast_node.right_node
                )
            case Token.K_OR:
                return self.visit(ast_node.left_node) or self.visit(ast_node.right_node)

    def visitEmptyStatementNode(self, ast_node):
        pass

    def visitAssignmentStatementNode(self, ast_node):
        curr_stack_frame = Interpreter.PROGRAM_STACK.peek()
        curr_stack_frame.set(
            ast_node.left_node.val, val=self.visit(ast_node.right_node)
        )

    def visitConditionalStatementNode(self, ast_node):
        for i, (condition, statement) in enumerate(ast_node.if_cases):
            condition_result = self.visit(condition)

            if condition_result:
                stack_frame_name = "if statement" if i == 0 else "elseif statement"

                # Create a new stack frame for the if statements here.
                Interpreter.PROGRAM_STACK.push(
                    StackFrame(
                        stack_frame_name,
                        StackFrame.CONDITIONAL_STATEMENT,
                        scope_level=Interpreter.PROGRAM_STACK.peek().scope_level + 1,
                        outer_scope=Interpreter.PROGRAM_STACK.peek(),
                    )
                )

                print("Entering", stack_frame_name, "scope")
                print(Interpreter.PROGRAM_STACK)
                self.visit(statement)
                print("Exiting", stack_frame_name, "scope")
                print(Interpreter.PROGRAM_STACK)
                Interpreter.PROGRAM_STACK.pop()
                return

        if ast_node.else_case is not None:
            # Create a new stack frame for the else statement here.
            Interpreter.PROGRAM_STACK.push(
                StackFrame(
                    "else statement",
                    StackFrame.CONDITIONAL_STATEMENT,
                    scope_level=Interpreter.PROGRAM_STACK.peek().scope_level + 1,
                    outer_scope=Interpreter.PROGRAM_STACK.peek(),
                )
            )

            print("Entering", "else statement", "scope")
            print(Interpreter.PROGRAM_STACK)
            self.visit(ast_node.else_case)
            print("Exiting", "else statement", "scope")
            print(Interpreter.PROGRAM_STACK)
            Interpreter.PROGRAM_STACK.pop()

    def visitWhileStatementNode(self, ast_node):
        # Create a new stack frame for the while statement here.
        Interpreter.PROGRAM_STACK.push(
            StackFrame(
                "while statement",
                StackFrame.WHILE_STATEMENT,
                scope_level=Interpreter.PROGRAM_STACK.peek().scope_level + 1,
                outer_scope=Interpreter.PROGRAM_STACK.peek(),
            )
        )

        while True:
            condition_result = self.visit(ast_node.condition)

            if not condition_result:
                break

            print("Entering", "while statement", "scope")
            print(Interpreter.PROGRAM_STACK)
            self.visit(ast_node.statement_list_node)
            print("Exiting", "while statement", "scope")

        Interpreter.PROGRAM_STACK.pop()

    def visitRangeExprNode(self, ast_node):
        start = self.visit(ast_node.start_node)
        end = self.visit(ast_node.end_node)

        return (
            range(start, end)
            if ast_node.step_node is None
            else range(start, end, self.visit(ast_node.step_node))
        )

    def visitForStatementNode(self, ast_node):
        iterable = self.visit(ast_node.iterable)

        # Create a new stack frame for the for statement here.
        Interpreter.PROGRAM_STACK.push(
            StackFrame(
                "for statement",
                StackFrame.FOR_STATEMENT,
                scope_level=Interpreter.PROGRAM_STACK.peek().scope_level + 1,
                outer_scope=Interpreter.PROGRAM_STACK.peek(),
            )
        )

        print("Entering", "for statement", "scope")
        print(Interpreter.PROGRAM_STACK)

        self.visit(ast_node.var_decl_statement_node)
        var_node = ast_node.var_decl_statement_node.variables[0]

        curr_stack_frame = Interpreter.PROGRAM_STACK.peek()

        for val in iterable:
            curr_stack_frame.set(var_node.val, val=val)
            print(Interpreter.PROGRAM_STACK)
            self.visit(ast_node.statement_list_node)

        print("Exiting", "for statement", "scope")
        Interpreter.PROGRAM_STACK.pop()

    def visitVarTypeNode(self, ast_node):
        pass

    def visitVarDeclStatementNode(self, ast_node):
        curr_stack_frame = Interpreter.PROGRAM_STACK.peek()

        for variable in ast_node.variables:
            if isinstance(variable, AssignmentStatementNode):
                var_val = self.visit(variable.right_node)
                curr_stack_frame[variable.left_node.val] = var_val

            else:
                curr_stack_frame[variable.val] = None

    def visitReturnTypeNode(self, ast_node):
        pass

    def visitFuncDeclStatementNode(self, ast_node):
        pass

    def visitStatementListNode(self, ast_node):
        for statement in ast_node.statements:
            self.visit(statement)

    def visitProgramNode(self, ast_node):
        Interpreter.PROGRAM_STACK.push(
            StackFrame("global", StackFrame.GLOBAL, scope_level=1)
        )
        self.visit(ast_node.statement_list_node)
        print(Interpreter.PROGRAM_STACK)
        Interpreter.PROGRAM_STACK.pop()

    def __error(self, error_message, token):
        raise InterpreterError(
            error_message + f" on line: {token.line}, column: {token.col}",
        )
