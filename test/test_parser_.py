import unittest

from project_code.tokens import Token
from project_code.lexer import Lexer
from project_code.parser_ import Parser
from project_code.abstract_syntax_tree import (
    VarNode,
    NumberNode,
    BoolNode,
    UnaryOpNode,
    BinaryOpNode,
    EmptyStatementNode,
    AssignStatementNode,
    ConditionalStatementNode,
    VarTypeNode,
    VarDeclStatementNode,
    StatementListNode,
    ProgramNode,
)


class TestParser(unittest.TestCase):
    def test_parse_with_empty_text(self):
        lexer = Lexer("")
        parser = Parser(lexer)
        tree = parser.parse()

        self.assertIsInstance(tree, ProgramNode)

    def test_parse_with_variable_declaration(self):
        lexer = Lexer("var(int) x;")
        parser = Parser(lexer)
        tree = parser.parse()

        self.assertIsInstance(tree, ProgramNode)
        self.assertIsInstance(tree.statement_list_node, StatementListNode)

        self.assertIsInstance(
            tree.statement_list_node.statements[0], VarDeclStatementNode
        )
        self.assertIsInstance(
            tree.statement_list_node.statements[0].var_type_node, VarTypeNode
        )
        self.assertEqual(
            tree.statement_list_node.statements[0].var_type_node.value, "int"
        )
