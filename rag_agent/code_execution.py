"""
Safe code execution environment for RAG Agent.
Provides sandboxed Python execution with security controls.
"""

import ast
import sys
import io
import time
import subprocess
import tempfile
import os
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
import logging
from contextlib import redirect_stdout, redirect_stderr
import traceback
import signal

logger = logging.getLogger(__name__)

class CodeExecutionResult:
    """Result of code execution."""
    
    def __init__(self):
        self.success: bool = False
        self.output: str = ""
        self.error: str = ""
        self.execution_time: float = 0.0
        self.return_value: Any = None
        self.warnings: List[str] = []

class SecurityValidator:
    """Validates code for security before execution."""
    
    DANGEROUS_IMPORTS = {
        'os', 'subprocess', 'sys', 'eval', 'exec', 'compile', 
        'open', '__import__', 'importlib', 'socket', 'urllib',
        'requests', 'http', 'ftplib', 'smtplib', 'telnetlib',
        'webbrowser', 'ctypes', 'multiprocessing', 'threading',
        'asyncio', 'concurrent', 'shutil', 'tempfile', 'pickle'
    }
    
    DANGEROUS_FUNCTIONS = {
        'eval', 'exec', 'compile', 'open', '__import__', 'globals',
        'locals', 'vars', 'dir', 'getattr', 'setattr', 'delattr',
        'hasattr', 'callable', 'isinstance', 'issubclass'
    }
    
    DANGEROUS_ATTRIBUTES = {
        '__class__', '__bases__', '__subclasses__', '__mro__',
        '__globals__', '__locals__', '__dict__', '__code__',
        '__func__', '__self__', '__module__'
    }
    
    @classmethod
    def validate_code(cls, code: str) -> Tuple[bool, List[str]]:
        """Validate code for security issues."""
        warnings = []
        
        try:
            # Parse the code into AST
            tree = ast.parse(code)
            
            # Check for dangerous patterns
            for node in ast.walk(tree):
                # Check imports
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name in cls.DANGEROUS_IMPORTS:
                            warnings.append(f"Dangerous import detected: {alias.name}")
                
                elif isinstance(node, ast.ImportFrom):
                    if node.module in cls.DANGEROUS_IMPORTS:
                        warnings.append(f"Dangerous import detected: {node.module}")
                
                # Check function calls
                elif isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name):
                        if node.func.id in cls.DANGEROUS_FUNCTIONS:
                            warnings.append(f"Dangerous function call: {node.func.id}")
                
                # Check attribute access
                elif isinstance(node, ast.Attribute):
                    if node.attr in cls.DANGEROUS_ATTRIBUTES:
                        warnings.append(f"Dangerous attribute access: {node.attr}")
                
                # Check for infinite loops (simple heuristic)
                elif isinstance(node, ast.While):
                    if isinstance(node.test, ast.Constant) and node.test.value is True:
                        warnings.append("Potential infinite loop detected (while True)")
            
            # Additional string-based checks
            code_lower = code.lower()
            if 'while true:' in code_lower and 'break' not in code_lower:
                warnings.append("Potential infinite loop without break condition")
            
            if 'import os' in code or 'from os' in code:
                warnings.append("OS module usage detected")
            
            # Check for very long loops
            for line in code.split('\n'):
                if 'for' in line and 'range(' in line:
                    try:
                        # Extract range parameter
                        range_match = line.split('range(')[1].split(')')[0]
                        if range_match.isdigit() and int(range_match) > 100000:
                            warnings.append(f"Large loop detected: range({range_match})")
                    except:
                        pass
            
            # If there are critical warnings, reject the code
            critical_warnings = [w for w in warnings if any(danger in w.lower() for danger in ['import', 'infinite', 'dangerous'])]
            
            return len(critical_warnings) == 0, warnings
            
        except SyntaxError as e:
            warnings.append(f"Syntax error: {str(e)}")
            return False, warnings
        except Exception as e:
            warnings.append(f"Code validation error: {str(e)}")
            return False, warnings

class SafeExecutor:
    """Safe Python code executor with security controls."""
    
    def __init__(self, timeout: int = 10, max_output_length: int = 10000):
        self.timeout = timeout
        self.max_output_length = max_output_length
        self.validator = SecurityValidator()
    
    def execute_code(self, code: str, context: Optional[Dict[str, Any]] = None) -> CodeExecutionResult:
        """Execute Python code safely."""
        result = CodeExecutionResult()
        start_time = time.time()
        
        try:
            # Validate code security
            is_safe, warnings = self.validator.validate_code(code)
            result.warnings = warnings
            
            if not is_safe:
                result.error = "Code rejected due to security concerns: " + "; ".join(warnings)
                return result
            
            # Prepare execution environment
            safe_globals = self._create_safe_globals()
            
            # Add context variables if provided
            if context:
                safe_globals.update(context)
            
            # Capture output
            stdout_capture = io.StringIO()
            stderr_capture = io.StringIO()
            
            # Execute with timeout
            try:
                with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
                    # Set up timeout handler
                    def timeout_handler(signum, frame):
                        raise TimeoutError("Code execution timed out")
                    
                    signal.signal(signal.SIGALRM, timeout_handler)
                    signal.alarm(self.timeout)
                    
                    try:
                        # Execute the code
                        exec_result = exec(code, safe_globals)
                        result.return_value = exec_result
                        result.success = True
                    finally:
                        signal.alarm(0)  # Cancel timeout
            
            except TimeoutError:
                result.error = f"Code execution timed out after {self.timeout} seconds"
            except Exception as e:
                result.error = f"Execution error: {str(e)}\n{traceback.format_exc()}"
            
            # Capture outputs
            result.output = stdout_capture.getvalue()
            if stderr_capture.getvalue():
                result.error += f"\nStderr: {stderr_capture.getvalue()}"
            
            # Limit output length
            if len(result.output) > self.max_output_length:
                result.output = result.output[:self.max_output_length] + "\n[Output truncated...]"
            
            result.execution_time = time.time() - start_time
            
        except Exception as e:
            result.error = f"Executor error: {str(e)}"
            result.execution_time = time.time() - start_time
        
        return result
    
    def _create_safe_globals(self) -> Dict[str, Any]:
        """Create a safe globals dictionary for code execution."""
        # Start with basic builtins
        safe_globals = {
            '__builtins__': {
                'print': print,
                'len': len,
                'str': str,
                'int': int,
                'float': float,
                'bool': bool,
                'list': list,
                'dict': dict,
                'tuple': tuple,
                'set': set,
                'range': range,
                'enumerate': enumerate,
                'zip': zip,
                'map': map,
                'filter': filter,
                'sum': sum,
                'min': min,
                'max': max,
                'abs': abs,
                'round': round,
                'sorted': sorted,
                'reversed': reversed,
                'any': any,
                'all': all,
                'type': type,
                'isinstance': isinstance,
                'repr': repr,
                'format': format,
            }
        }
        
        # Add safe modules
        try:
            import math
            import random
            import datetime
            import json
            import re
            
            safe_globals.update({
                'math': math,
                'random': random,
                'datetime': datetime,
                'json': json,
                're': re,
            })
        except ImportError:
            pass
        
        # Add numpy and pandas if available (common for data analysis)
        try:
            import numpy as np
            import pandas as pd
            safe_globals.update({
                'np': np,
                'numpy': np,
                'pd': pd,
                'pandas': pd,
            })
        except ImportError:
            pass
        
        return safe_globals

class CodeAnalyzer:
    """Analyzes and explains code."""
    
    @staticmethod
    def analyze_code_structure(code: str) -> Dict[str, Any]:
        """Analyze the structure of code."""
        try:
            tree = ast.parse(code)
            
            analysis = {
                'functions': [],
                'classes': [],
                'imports': [],
                'variables': [],
                'complexity_score': 0,
                'lines_of_code': len([line for line in code.split('\n') if line.strip()]),
                'total_lines': len(code.split('\n'))
            }
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    analysis['functions'].append({
                        'name': node.name,
                        'args': [arg.arg for arg in node.args.args],
                        'line': node.lineno
                    })
                    analysis['complexity_score'] += 2
                
                elif isinstance(node, ast.ClassDef):
                    analysis['classes'].append({
                        'name': node.name,
                        'line': node.lineno
                    })
                    analysis['complexity_score'] += 3
                
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        analysis['imports'].append(alias.name)
                
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        analysis['imports'].append(node.module)
                
                elif isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            analysis['variables'].append(target.id)
                
                elif isinstance(node, (ast.For, ast.While)):
                    analysis['complexity_score'] += 1
                
                elif isinstance(node, ast.If):
                    analysis['complexity_score'] += 1
            
            return analysis
            
        except SyntaxError as e:
            return {'error': f'Syntax error: {str(e)}'}
        except Exception as e:
            return {'error': f'Analysis error: {str(e)}'}
    
    @staticmethod
    def suggest_improvements(code: str) -> List[str]:
        """Suggest code improvements."""
        suggestions = []
        
        try:
            tree = ast.parse(code)
            
            # Check for common issues
            has_docstrings = False
            function_count = 0
            long_functions = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    function_count += 1
                    
                    # Check for docstring
                    if (node.body and 
                        isinstance(node.body[0], ast.Expr) and 
                        isinstance(node.body[0].value, ast.Constant) and 
                        isinstance(node.body[0].value.value, str)):
                        has_docstrings = True
                    
                    # Check function length
                    if len(node.body) > 20:
                        long_functions.append(node.name)
            
            # Generate suggestions
            if function_count > 0 and not has_docstrings:
                suggestions.append("Consider adding docstrings to your functions")
            
            if long_functions:
                suggestions.append(f"Consider breaking down long functions: {', '.join(long_functions)}")
            
            # Check for hardcoded values
            if any(char.isdigit() for char in code) and 'range(' not in code:
                suggestions.append("Consider using named constants instead of magic numbers")
            
            # Check for repeated code patterns
            lines = [line.strip() for line in code.split('\n') if line.strip()]
            if len(lines) != len(set(lines)):
                suggestions.append("Consider extracting repeated code into functions")
            
        except:
            pass
        
        return suggestions

# Global code executor
safe_executor = SafeExecutor()
code_analyzer = CodeAnalyzer()
