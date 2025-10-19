#!/usr/bin/env python3
"""
Script para validar sintaxe das bibliotecas principais do projeto.
Este script verifica se estamos usando a sintaxe correta das versões especificadas.
"""

import ast
import sys
from pathlib import Path
from typing import List, Dict, Any


class SyntaxValidator:
    """Validador de sintaxe para bibliotecas Python."""
    
    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []
        
    def validate_pydantic_v2(self, file_path: Path) -> None:
        """Valida sintaxe do Pydantic v2."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Verificar imports obsoletos
            if "from pydantic import BaseSettings" in content:
                self.errors.append(f"{file_path}: Use 'from pydantic_settings import BaseSettings' instead of 'from pydantic import BaseSettings'")
                
            if "Field(env=" in content:
                self.errors.append(f"{file_path}: Use 'Field(alias=' instead of 'Field(env=' for Pydantic v2")
                
            if "class Config:" in content:
                self.errors.append(f"{file_path}: Use 'model_config = SettingsConfigDict()' instead of 'class Config:' for Pydantic v2")
                
            # Verificar se está usando SettingsConfigDict
            if "BaseSettings" in content and "SettingsConfigDict" not in content:
                self.warnings.append(f"{file_path}: Consider using SettingsConfigDict for better Pydantic v2 compatibility")
                
        except Exception as e:
            self.errors.append(f"{file_path}: Error reading file - {e}")
    
    def validate_sqlalchemy_v2(self, file_path: Path) -> None:
        """Valida sintaxe do SQLAlchemy v2."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Verificar imports obsoletos
            if "from sqlalchemy.ext.declarative import declarative_base" in content:
                self.errors.append(f"{file_path}: Use 'from sqlalchemy.orm import DeclarativeBase' instead of 'from sqlalchemy.ext.declarative import declarative_base'")
                
            if "declarative_base()" in content:
                self.errors.append(f"{file_path}: Use 'class Base(DeclarativeBase): pass' instead of 'declarative_base()'")
                
        except Exception as e:
            self.errors.append(f"{file_path}: Error reading file - {e}")
    
    def validate_file(self, file_path: Path) -> None:
        """Valida um arquivo Python."""
        if not file_path.suffix == '.py':
            return
            
        # Verificar sintaxe Python básica
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                ast.parse(f.read())
        except SyntaxError as e:
            self.errors.append(f"{file_path}: Python syntax error - {e}")
            return
            
        # Validações específicas por biblioteca
        self.validate_pydantic_v2(file_path)
        self.validate_sqlalchemy_v2(file_path)
    
    def validate_directory(self, directory: Path) -> None:
        """Valida todos os arquivos Python em um diretório."""
        for py_file in directory.rglob("*.py"):
            if py_file.name.startswith('.'):
                continue
            self.validate_file(py_file)
    
    def print_results(self) -> None:
        """Imprime os resultados da validação."""
        if self.errors:
            print("❌ ERROS ENCONTRADOS:")
            for error in self.errors:
                print(f"  • {error}")
            print()
            
        if self.warnings:
            print("⚠️  AVISOS:")
            for warning in self.warnings:
                print(f"  • {warning}")
            print()
            
        if not self.errors and not self.warnings:
            print("✅ Nenhum erro de sintaxe encontrado!")
        elif not self.errors:
            print("✅ Nenhum erro crítico encontrado!")
            
        return len(self.errors) == 0


def main():
    """Função principal."""
    print("🔍 Validando sintaxe das bibliotecas...")
    print()
    
    validator = SyntaxValidator()
    
    # Validar diretório src
    src_dir = Path("src")
    if src_dir.exists():
        print(f"Validando {src_dir}...")
        validator.validate_directory(src_dir)
    
    # Validar diretório tests
    tests_dir = Path("tests")
    if tests_dir.exists():
        print(f"Validando {tests_dir}...")
        validator.validate_directory(tests_dir)
    
    print()
    success = validator.print_results()
    
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
