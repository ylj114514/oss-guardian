#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
污点分析
追踪污染源（sys.argv、input 等）流向危险函数（os.system、eval 等）。
"""

import ast
from typing import List, Dict, Any, Set, Optional


class TaintAnalyzer(ast.NodeVisitor):
    """用于污点传播分析的 AST 访问器。"""
    
    def __init__(self):
        self.taint_sources = []  # List of (source, line_no)
        self.taint_sinks = []  # List of (sink, line_no, func_name)
        self.taint_flows = []  # List of detected taint flows
        self.current_tainted_vars = set()  # Variables currently tainted
        self.var_assignments = {}  # Map variable name to assignment line
    
    def _is_taint_source(self, node: ast.AST) -> bool:
        """判断节点是否为污染源。"""
        # sys.argv 访问
        if isinstance(node, ast.Subscript):
            if isinstance(node.value, ast.Attribute):
                if isinstance(node.value.value, ast.Name) and node.value.value.id == 'sys':
                    if node.value.attr == 'argv':
                        return True
        
        # input/raw_input 调用
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                if node.func.id in ('input', 'raw_input'):
                    return True
        
        return False
    
    def _is_taint_sink(self, node: ast.Call) -> Optional[str]:
        """判断调用是否为危险汇点，命中则返回函数名。"""
        if isinstance(node.func, ast.Attribute):
            # os.system / os.popen 等
            if isinstance(node.func.value, ast.Name):
                if node.func.value.id == 'os':
                    if node.func.attr in ('system', 'popen'):
                        return f"os.{node.func.attr}"
                elif node.func.value.id == 'subprocess':
                    if node.func.attr in ('call', 'run', 'Popen'):
                        return f"subprocess.{node.func.attr}"
        
        # eval/exec 调用
        if isinstance(node.func, ast.Name):
            if node.func.id in ('eval', 'exec'):
                return node.func.id
        
        return None
    
    def _get_variable_name(self, node: ast.AST) -> Optional[str]:
        """从节点中提取变量名或属性路径。"""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            # 对属性返回完整路径
            if isinstance(node.value, ast.Name):
                return f"{node.value.id}.{node.attr}"
        return None
    
    def visit_Assign(self, node: ast.Assign):
        """记录赋值语句并跟踪污点传播。"""
        # 赋值右侧是否为污染源
        is_tainted = self._is_taint_source(node.value)
        
        # 右侧是否引用了已污染变量
        if not is_tainted:
            var_name = self._get_variable_name(node.value)
            if var_name and var_name in self.current_tainted_vars:
                is_tainted = True
        
        # 标记左侧变量为污染
        if is_tainted:
            for target in node.targets:
                var_name = self._get_variable_name(target)
                if var_name:
                    self.current_tainted_vars.add(var_name)
                    self.var_assignments[var_name] = node.lineno
                    
                    # 记录污染源
                    source_repr = self._get_node_repr(node.value)
                    self.taint_sources.append({
                        'source': source_repr,
                        'line': node.lineno,
                        'tainted_var': var_name
                    })
        
        self.generic_visit(node)
    
    def visit_Call(self, node: ast.Call):
        """识别危险调用并判断是否发生污点流入。"""
        sink_name = self._is_taint_sink(node)
        
        if sink_name:
            # 记录危险汇点
            self.taint_sinks.append({
                'sink': sink_name,
                'line': node.lineno,
                'args': [self._get_node_repr(arg) for arg in node.args]
            })
            
            # 检查参数是否带污点
            for arg in node.args:
                arg_repr = self._get_node_repr(arg)
                var_name = self._get_variable_name(arg)
                
                # 参数本身是污染源
                if self._is_taint_source(arg):
                    self.taint_flows.append({
                        'source': arg_repr,
                        'sink': sink_name,
                        'source_line': node.lineno,
                        'sink_line': node.lineno,
                        'severity': 'critical',
                        'type': 'direct'
                    })
                # 参数引用了已污染变量
                elif var_name and var_name in self.current_tainted_vars:
                    source_line = self.var_assignments.get(var_name, node.lineno)
                    self.taint_flows.append({
                        'source': arg_repr,
                        'sink': sink_name,
                        'source_line': source_line,
                        'sink_line': node.lineno,
                        'severity': 'critical',
                        'type': 'variable_flow',
                        'tainted_var': var_name
                    })
        
        self.generic_visit(node)
    
    def _get_node_repr(self, node: ast.AST) -> str:
        """生成节点的简化字符串表示。"""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            if isinstance(node.value, ast.Name):
                return f"{node.value.id}.{node.attr}"
        elif isinstance(node, ast.Subscript):
            if isinstance(node.value, ast.Attribute):
                if isinstance(node.value.value, ast.Name):
                    return f"{node.value.value.id}.{node.value.attr}[...]"
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                return f"{node.func.id}(...)"
        elif isinstance(node, ast.BinOp):
            # 处理字符串拼接等二元表达式
            left = self._get_node_repr(node.left)
            right = self._get_node_repr(node.right)
            return f"{left} + {right}"
        elif isinstance(node, ast.Constant):
            return repr(node.value)
        elif isinstance(node, ast.Str):  # Python < 3.8
            return repr(node.s)
        
        return ast.dump(node)


def analyze(ast_tree: ast.AST) -> List[Dict[str, Any]]:
    """
    对 AST 执行污点分析并返回污点流列表。

    ??:
        ast_tree: AST 根节点

    ??:
        List[Dict]: 污点流信息，包含 source/sink/行号/严重级别等
    """
    if ast_tree is None:
        return []
    
    analyzer = TaintAnalyzer()
    analyzer.visit(ast_tree)
    
    return analyzer.taint_flows
