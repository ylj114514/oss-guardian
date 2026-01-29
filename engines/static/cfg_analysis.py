#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
控制流结构分析（CFG）
识别 if/for/while/try 等结构并记录行号范围与分支信息。
"""

import ast
from typing import List, Dict, Any


class CFGAnalyzer(ast.NodeVisitor):
    """用于控制流结构抽取的 AST 访问器。"""
    
    def __init__(self):
        self.cfg_structures = []
    
    def _get_node_repr(self, node: ast.AST) -> str:
        """获取节点的简化字符串表示，便于在报告中展示条件/表达式。"""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            if isinstance(node.value, ast.Name):
                return f"{node.value.id}.{node.attr}"
        elif isinstance(node, ast.Compare):
            # 简化比较表达式
            if len(node.ops) > 0 and len(node.comparators) > 0:
                left = self._get_node_repr(node.left)
                right = self._get_node_repr(node.comparators[0])
                op = type(node.ops[0]).__name__
                return f"{left} {op} {right}"
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                return f"{node.func.id}(...)"
            elif isinstance(node.func, ast.Attribute):
                if isinstance(node.func.value, ast.Name):
                    return f"{node.func.value.id}.{node.func.attr}(...)"
        elif isinstance(node, ast.Constant):
            return repr(node.value)
        elif isinstance(node, ast.Str):  # Python < 3.8
            return repr(node.s)
        elif isinstance(node, ast.Num):  # Python < 3.8
            return repr(node.n)
        
        return ast.dump(node)[:50]  # 限制长度，避免过长
    
    def _get_body_lines(self, body: List[ast.AST]) -> List[int]:
        """提取语句块内涉及的行号列表。"""
        lines = []
        for stmt in body:
            if hasattr(stmt, 'lineno'):
                lines.append(stmt.lineno)
            # 递归提取嵌套结构中的行号
            if isinstance(stmt, (ast.If, ast.For, ast.While, ast.Try)):
                lines.extend(self._get_body_lines(stmt.body))
                if isinstance(stmt, ast.If) and stmt.orelse:
                    lines.extend(self._get_body_lines(stmt.orelse))
                elif isinstance(stmt, (ast.For, ast.While)) and stmt.orelse:
                    lines.extend(self._get_body_lines(stmt.orelse))
                elif isinstance(stmt, ast.Try):
                    for handler in stmt.handlers:
                        lines.extend(self._get_body_lines(handler.body))
                    if stmt.orelse:
                        lines.extend(self._get_body_lines(stmt.orelse))
                    if stmt.finalbody:
                        lines.extend(self._get_body_lines(stmt.finalbody))
        return sorted(set(lines))  # 去重并排序
    
    def _get_end_line(self, node: ast.AST) -> int:
        """估算结构的结束行号，取结构体内的最大行号。"""
        max_line = node.lineno
        if hasattr(node, 'body'):
            for stmt in node.body:
                if hasattr(stmt, 'lineno'):
                    max_line = max(max_line, stmt.lineno)
                # 递归检查嵌套结构
                if isinstance(stmt, (ast.If, ast.For, ast.While, ast.Try)):
                    max_line = max(max_line, self._get_end_line(stmt))
        if hasattr(node, 'orelse') and node.orelse:
            for stmt in node.orelse:
                if hasattr(stmt, 'lineno'):
                    max_line = max(max_line, stmt.lineno)
        if hasattr(node, 'finalbody') and node.finalbody:
            for stmt in node.finalbody:
                if hasattr(stmt, 'lineno'):
                    max_line = max(max_line, stmt.lineno)
        return max_line
    
    def visit_If(self, node: ast.If):
        """抽取 if 结构的条件与行号范围。"""
        condition = self._get_node_repr(node.test)
        body_lines = self._get_body_lines(node.body)
        else_lines = self._get_body_lines(node.orelse) if node.orelse else []
        end_line = self._get_end_line(node)
        
        self.cfg_structures.append({
            'type': 'if',
            'start_line': node.lineno,
            'end_line': end_line,
            'condition': condition,
            'body_lines': body_lines,
            'else_lines': else_lines
        })
        self.generic_visit(node)
    
    def visit_For(self, node: ast.For):
        """抽取 for 结构的遍历对象与行号范围。"""
        target = self._get_node_repr(node.target)
        iter_expr = self._get_node_repr(node.iter)
        body_lines = self._get_body_lines(node.body)
        else_lines = self._get_body_lines(node.orelse) if node.orelse else []
        end_line = self._get_end_line(node)
        
        self.cfg_structures.append({
            'type': 'for',
            'start_line': node.lineno,
            'end_line': end_line,
            'target': target,
            'iter': iter_expr,
            'body_lines': body_lines,
            'else_lines': else_lines
        })
        self.generic_visit(node)
    
    def visit_While(self, node: ast.While):
        """抽取 while 结构的条件与行号范围。"""
        condition = self._get_node_repr(node.test)
        body_lines = self._get_body_lines(node.body)
        else_lines = self._get_body_lines(node.orelse) if node.orelse else []
        end_line = self._get_end_line(node)
        
        self.cfg_structures.append({
            'type': 'while',
            'start_line': node.lineno,
            'end_line': end_line,
            'condition': condition,
            'body_lines': body_lines,
            'else_lines': else_lines
        })
        self.generic_visit(node)
    
    def visit_Try(self, node: ast.Try):
        """抽取 try/except/else/finally 结构的行号范围。"""
        body_lines = self._get_body_lines(node.body)
        except_lines = []
        for handler in node.handlers:
            except_lines.extend(self._get_body_lines(handler.body))
        else_lines = self._get_body_lines(node.orelse) if node.orelse else []
        finally_lines = self._get_body_lines(node.finalbody) if node.finalbody else []
        end_line = self._get_end_line(node)
        
        self.cfg_structures.append({
            'type': 'try',
            'start_line': node.lineno,
            'end_line': end_line,
            'body_lines': body_lines,
            'except_lines': except_lines,
            'else_lines': else_lines,
            'finally_lines': finally_lines
        })
        self.generic_visit(node)


def analyze(ast_tree: ast.AST) -> List[Dict[str, Any]]:
    """
    分析 AST 中的控制流结构并返回结构化结果。

    ??:
        ast_tree: AST 根节点

    ??:
        List[Dict]: 控制流结构列表，包含类型/起止行/主体行等信息
    """
    if ast_tree is None:
        return []
    
    analyzer = CFGAnalyzer()
    analyzer.visit(ast_tree)
    
    return analyzer.cfg_structures
