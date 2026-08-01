"""
Formula Parser Module.

This module handles the tokenization, parsing, and evaluation of logical formulas
in a Paraconsistent Modal Logic context (Twist Structures).

Definitions & Abbreviations:
- &   : Weak Meet (Conjunction)
- |   : Weak Join (Disjunction)
- ->  : Material Implication defined as ~A | B
- <-> : Material Equivalence defined as (A -> B) & (B -> A)
- []  : Box defined as ~<a>~A
- <>  : Diamond (Weighted)
- 1/TOP : Top (True) (1, 0)
- 0/BOT : Bottom (False) (0, 1)
"""

from abc import ABC, abstractmethod
from typing import Optional, Set, Any, Tuple
from ast import literal_eval
from services.logging_service import get_logger

logger = get_logger("FormulaParser")

class Lexer:
    def __init__(self, text: str):
        self.text = text
        self.pos = 0
        self.current_char: Optional[str] = self.text[0] if self.text else None

    def advance(self) -> None:
        self.pos += 1
        self.current_char = self.text[self.pos] if self.pos < len(self.text) else None

    def skip_whitespace(self) -> None:
        while self.current_char is not None and self.current_char.isspace():
            self.advance()

    def get_identifier(self) -> str:
        result = ''
        while self.current_char is not None and (self.current_char.isalnum() or self.current_char == '_'):
            result += self.current_char
            self.advance()
        return result

    def get_next_token(self) -> Tuple[str, Optional[str], int]:
        """Returns (Token Type, Token Value, Start Position)"""
        while self.current_char is not None:
            if self.current_char.isspace():
                self.skip_whitespace()
                continue
            
            start_pos = self.pos

            if self.current_char == '[':
                self.advance()
                if self.current_char == ']':
                    raise ValueError(f"Syntax Error at index {start_pos}: Box operator '[]' requires an action identifier.")
                action = self.get_identifier()
                if not action:
                    raise ValueError(f"Syntax Error at index {start_pos}: Invalid action identifier inside Box operator.")
                if self.current_char == ']':
                    self.advance()
                    return ('BOX', action, start_pos)
                raise ValueError(f"Syntax Error at index {self.pos}: Expected ']' to close Box operator.")

            if self.current_char == '<':
                self.advance()
                
                if self.current_char == '-':
                    self.advance()
                    if self.current_char == '>':
                        self.advance()
                        return ('MAT_IFF', '<->', start_pos)
                    raise ValueError(f"Syntax Error at index {start_pos}: Expected '>' after '<-'.")

                if self.current_char == '>':
                    raise ValueError(f"Syntax Error at index {start_pos}: Diamond operator '<>' requires an action identifier.")

                action = self.get_identifier()
                if not action:
                     raise ValueError(f"Syntax Error at index {start_pos}: Invalid action identifier inside Diamond operator.")

                if self.current_char == '>':
                    self.advance()
                    return ('DIAMOND', action, start_pos)
                raise ValueError(f"Syntax Error at index {self.pos}: Expected '>' to close Diamond operator.")
            
            if self.current_char.isalnum():
                val = self.get_identifier()
                if val in ('1', '0'):
                    return ('ATOM', 'TOP' if val == '1' else 'BOT', start_pos)
                if val.upper() in ('TOP', 'BOT'):
                    return ('ATOM', val.upper(), start_pos)
                return ('ATOM', val, start_pos)

            char_map = {
                '~': 'NOT',
                '&': 'AND', 
                '|': 'OR',  
                '(': 'LPAREN',
                ')': 'RPAREN'
            }

            if self.current_char in char_map:
                token_type = char_map[self.current_char]
                val = self.current_char
                self.advance()
                return (token_type, val, start_pos)
            
            if self.current_char == '-':
                self.advance()
                if self.current_char == '>':
                    self.advance()
                    return ('MAT_IMPLIES', '->', start_pos)
                raise ValueError(f"Syntax Error at index {start_pos}: Expected '>' after '-'.")
            
            raise ValueError(f"Lexical Error at index {start_pos}: Unexpected character '{self.current_char}'")
        
        return ('EOF', None, self.pos)


class ASTNode(ABC):
    @abstractmethod
    def evaluate(self, model: Any, world: Any, twist: Any) -> Tuple[str, str]:
        pass

    @abstractmethod
    def get_atoms(self) -> Set[str]:
        pass


class Atom(ASTNode):
    def __init__(self, name: str):
        self.name = name

    def get_atoms(self) -> Set[str]:
        if self.name in ['TOP', 'BOT', '1', '0']:
            return set()
        return {self.name}

    def evaluate(self, model: Any, world: Any, twist: Any) -> Tuple[str, str]:
        if self.name in ('BOT', '0'):
            return (twist.lattice.bottom, twist.lattice.top)
        
        if self.name in ('TOP', '1'):
            return (twist.lattice.top, twist.lattice.bottom)
            
        if self.name in world.assignments:
            val_str = world.assignments[self.name]
            try:
                if val_str.strip().startswith('('): 
                    val = literal_eval(val_str)
                    if not isinstance(val, tuple) or len(val) != 2:
                        raise ValueError(f"Atom '{self.name}' has invalid structure '{val}'. Expected a pair (t, f).")
                    return val
                
                return (val_str, val_str)
            except (ValueError, SyntaxError) as e:
                logger.error(f"Data Error: Assignment for Atom '{self.name}' is malformed: {str(e)}")
                raise ValueError(f"Atom '{self.name}' has an invalid assignment format.")
                
        raise ValueError(f"Undefined Atom: '{self.name}' is not assigned in state '{world.name_short}'.")


class Not(ASTNode):
    def __init__(self, child: ASTNode):
        self.child = child
    def get_atoms(self) -> Set[str]: return self.child.get_atoms()

    def evaluate(self, model: Any, world: Any, twist: Any) -> Tuple[str, str]:
        return twist.negation(self.child.evaluate(model, world, twist))


class And(ASTNode): 
    def __init__(self, left: ASTNode, right: ASTNode):
        self.left, self.right = left, right
    def get_atoms(self) -> Set[str]: return self.left.get_atoms().union(self.right.get_atoms())

    def evaluate(self, model: Any, world: Any, twist: Any) -> Tuple[str, str]:
        return twist.weak_meet(self.left.evaluate(model, world, twist), self.right.evaluate(model, world, twist))


class Or(ASTNode):
    def __init__(self, left: ASTNode, right: ASTNode):
        self.left, self.right = left, right
    def get_atoms(self) -> Set[str]: return self.left.get_atoms().union(self.right.get_atoms())

    def evaluate(self, model: Any, world: Any, twist: Any) -> Tuple[str, str]:
        return twist.weak_join(self.left.evaluate(model, world, twist), self.right.evaluate(model, world, twist))


class MaterialImplies(ASTNode):
    def __init__(self, left: ASTNode, right: ASTNode):
        self.left, self.right = left, right
    def get_atoms(self) -> Set[str]: return self.left.get_atoms().union(self.right.get_atoms())

    def evaluate(self, model: Any, world: Any, twist: Any) -> Tuple[str, str]:
        val_l = self.left.evaluate(model, world, twist)
        not_l = twist.negation(val_l)
        val_r = self.right.evaluate(model, world, twist)
        return twist.weak_join(not_l, val_r)


class MaterialIff(ASTNode):
    def __init__(self, left: ASTNode, right: ASTNode):
        self.left, self.right = left, right
    def get_atoms(self) -> Set[str]: return self.left.get_atoms().union(self.right.get_atoms())

    def evaluate(self, model: Any, world: Any, twist: Any) -> Tuple[str, str]:
        val_l = self.left.evaluate(model, world, twist)
        val_r = self.right.evaluate(model, world, twist)
        
        not_l = twist.negation(val_l)
        not_r = twist.negation(val_r)
        
        imp_lr = twist.weak_join(not_l, val_r)
        imp_rl = twist.weak_join(not_r, val_l)
        
        return twist.weak_meet(imp_lr, imp_rl)


class Diamond(ASTNode):
    """
    Modal Diamond: <a>phi
    """
    def __init__(self, child: ASTNode, action: str):
        self.child, self.action = child, action

    def get_atoms(self) -> Set[str]: return self.child.get_atoms()


    def evaluate(self, model: Any, world: Any, twist: Any) -> Tuple[str, str]:
        if self.action not in model.actions:
            raise ValueError(f"Action '{self.action}' is not defined in PLTS '{model.name_model}'.")
        
        targets_map = model.accessibility_relations.get(self.action, {}).get(world, {})
        
        if not targets_map:
            logger.warning(f"No relations found for Action '{self.action}' in State '{world.name_long}' of model '{model.name_model}'.")
            return (twist.lattice.bottom, twist.lattice.top)
            
        results = []
        for target, rel_weight in targets_map.items():
            try:
                val_succ = self.child.evaluate(model, target, twist)
                residue_val = twist.residue_meet(rel_weight, val_succ)
                results.append(residue_val)
            except Exception as e:
                logger.error(f"Error evaluating successor '{target.name_long}' for action '{self.action}': {str(e)}")
                raise

        return twist.weak_join_set(results)


class Box(ASTNode):
    """
    Modal Box: [action]A
    Derived from Diamond: ~<action>~A
    """
    def __init__(self, child: ASTNode, action: str):
        self.child, self.action = child, action

    def get_atoms(self) -> Set[str]: return self.child.get_atoms()

    def evaluate(self, model: Any, world: Any, twist: Any) -> Tuple[str, str]:
        not_phi = Not(self.child)
        diamond = Diamond(not_phi, self.action)
        return twist.negation(diamond.evaluate(model, world, twist))


class FormulaParser:
    def __init__(self, text: str):
        self.lexer = Lexer(text)
        self.current_token = self.lexer.get_next_token()

    def eat(self, token_type: str) -> None:
        """Consumes the current token if it matches the expected type, otherwise raises a descriptive error."""
        if self.current_token[0] == token_type:
            self.current_token = self.lexer.get_next_token()
        else:
            token_type_found, token_val_found, pos = self.current_token
            raise ValueError(
                f"Syntax Error at index {pos}: Expected '{token_type}', "
                f"but found '{token_type_found}' (value: '{token_val_found}')."
            )

    def parse(self) -> ASTNode:
        res = self.iff()
        if self.current_token[0] != 'EOF': 
            pos = self.current_token[2]
            raise ValueError(f"Syntax Error at index {pos}: Unexpected characters at end of formula.")
        return res

    def iff(self) -> ASTNode:
        node = self.implies()
        while self.current_token[0] == 'MAT_IFF':
            self.eat('MAT_IFF')
            right = self.implies()
            node = MaterialIff(node, right)
        return node

    def implies(self) -> ASTNode:
        node = self.expr_sum()
        while self.current_token[0] == 'MAT_IMPLIES':
            self.eat('MAT_IMPLIES')
            right = self.expr_sum()
            node = MaterialImplies(node, right)
        return node

    def expr_sum(self) -> ASTNode:
        node = self.expr_prod()
        while self.current_token[0] == 'OR':
            self.eat('OR')
            node = Or(node, self.expr_prod())
        return node

    def expr_prod(self) -> ASTNode: 
        node = self.unary()
        while self.current_token[0] == 'AND':
            self.eat('AND')
            node = And(node, self.unary())
        return node

    def unary(self) -> ASTNode:
        token, val, start_pos = self.current_token

        if token == 'NOT':
            self.eat('NOT')
            return Not(self.unary())
        elif token == 'BOX':
            self.eat('BOX')
            return Box(self.unary(), val)
        elif token == 'DIAMOND':
            self.eat('DIAMOND')
            return Diamond(self.unary(), val)
        elif token == 'LPAREN':
            self.eat('LPAREN')
            node = self.iff()
            if self.current_token[0] != 'RPAREN':
                raise ValueError(f"Syntax Error at index {self.current_token[2]}: Missing closing parenthesis ')' for expression starting at index {start_pos}.")
            self.eat('RPAREN')
            return node
        elif token == 'ATOM':
            self.eat('ATOM')
            return Atom(val)
        elif token == 'EOF':
            raise ValueError(f"Syntax Error at index {start_pos}: Unexpected end of formula. It seems like an operator is missing an operand.")
        else:
            raise ValueError(f"Syntax Error at index {start_pos}: Unexpected token '{token}' found where an Atom, '(', '~', or modal operator was expected.")