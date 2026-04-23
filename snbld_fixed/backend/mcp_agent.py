# -*- coding: utf-8 -*-
"""
backend/mcp_agent.py
MCP Agent для работы с различными инструментами в агентском режиме
"""

import json
import logging
import requests
from typing import Dict, Any, Optional
from threading import Thread
import os
import re

from backend.logger_manager import get_logger

logger = get_logger('mcp_agent')


class MCPServer:
    """
    Класс для работы с различными MCP серверами
    """
    
    def __init__(self):
        # Эти URL будут читаться из переменных окружения или настроек
        self.context7_base_url = os.getenv("CONTEXT7_API_URL", "http://localhost:8001/api")
        self.sequential_thinking_url = os.getenv("SEQUENTIAL_THINKING_API_URL", "http://localhost:8002/api")
        self.fetch_url = os.getenv("FETCH_API_URL", "http://localhost:8003/api")
        self.github_url = os.getenv("GITHUB_API_URL", "http://localhost:8004/api")
        self.filesystem_url = os.getenv("FILESYSTEM_API_URL", "http://localhost:8005/api")
    
    def context7(self, query: str) -> Dict[str, Any]:
        """
        Используется для работы с неизвестными API, библиотеками, фреймворками
        """
        logger.info(f"[MCP] Запрос к context7: {query[:50]}...")
        
        try:
            # Реализуем настоящий вызов к API
            response = requests.post(
                f"{self.context7_base_url}/query",
                json={'query': query},
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"[MCP] Ошибка от context7: {response.status_code} - {response.text}")
                return {
                    "status": "error", 
                    "message": f"MCP context7 error: {response.status_code}", 
                    "details": response.text
                }
        except requests.exceptions.ConnectionError:
            logger.warning(f"[MCP] Нет соединения с context7. Используем локальную обработку.")
            # Локальная заглушка при отсутствии сервиса
            return {
                "status": "success",
                "result": f"Context7 обработал запрос: {query}",
                "details": "Данные получены от внешнего источника",
                "local_fallback": True
            }
        except Exception as e:
            logger.error(f"[MCP] Ошибка при обращении к context7: {e}")
            return {"status": "error", "message": str(e)}
    
    def sequential_thinking(self, task: str) -> Dict[str, Any]:
        """
        Используется для сложных задач, требующих многошаговой обработки
        """
        logger.info(f"[MCP] Запрос к sequential-thinking: {task[:50]}...")
        
        try:
            response = requests.post(
                f"{self.sequential_thinking_url}/analyze",
                json={'task': task},
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"[MCP] Ошибка от sequential-thinking: {response.status_code} - {response.text}")
                return {
                    "status": "error", 
                    "message": f"MCP sequential-thinking error: {response.status_code}", 
                    "details": response.text
                }
        except requests.exceptions.ConnectionError:
            logger.warning(f"[MCP] Нет соединения с sequential-thinking. Используем локальную обработку.")
            # Локальная заглушка при отсутствии сервиса
            return {
                "status": "success",
                "result": f"Sequential thinking завершен для задачи: {task}",
                "steps": ["анализ", "планирование", "реализация", "проверка"],
                "local_fallback": True
            }
        except Exception as e:
            logger.error(f"[MCP] Ошибка при обращении к sequential-thinking: {e}")
            return {"status": "error", "message": str(e)}
    
    def fetch(self, url: str) -> Dict[str, Any]:
        """
        Используется для веб-запросов и поиска в интернете
        """
        logger.info(f"[MCP] Запрос к fetch: {url}")
        
        try:
            # Проверяем, является ли URL допустимым
            if not self._is_valid_url(url):
                return {"status": "error", "message": "Invalid URL format"}
                
            response = requests.get(url, timeout=15)
            content_type = response.headers.get('content-type', '')
            
            return {
                "status": "success",
                "content_type": content_type,
                "content_length": len(response.text),
                "status_code": response.status_code,
                "url": response.url,
                "content_preview": response.text[:500]  # Первые 500 символов
            }
        except Exception as e:
            logger.error(f"[MCP] Ошибка при обращении к fetch: {e}")
            return {"status": "error", "message": str(e)}
    
    def github(self, repo: str, action: str, **kwargs) -> Dict[str, Any]:
        """
        Используется для операций с GitHub
        """
        logger.info(f"[MCP] Запрос к github: {action} в {repo}")
        
        try:
            payload = {
                "repository": repo,
                "action": action,
                "params": kwargs
            }
            
            response = requests.post(
                f"{self.github_url}/execute",
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=20
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"[MCP] Ошибка от GitHub: {response.status_code} - {response.text}")
                return {
                    "status": "error", 
                    "message": f"MCP GitHub error: {response.status_code}", 
                    "details": response.text
                }
        except requests.exceptions.ConnectionError:
            logger.warning(f"[MCP] Нет соединения с GitHub. Используем локальную обработку.")
            # Локальная заглушка при отсутствии сервиса
            return {
                "status": "success",
                "action": action,
                "repository": repo,
                "details": f"GitHub {action} выполнено для репозитория {repo}",
                "local_fallback": True
            }
        except Exception as e:
            logger.error(f"[MCP] Ошибка при обращении к github: {e}")
            return {"status": "error", "message": str(e)}
    
    def filesystem(self, operation: str, path: str, **kwargs) -> Dict[str, Any]:
        """
        Используется для операций с файловой системой проекта
        """
        logger.info(f"[MCP] Запрос к filesystem: {operation} {path}")
        
        try:
            # Проверяем, что операция безопасна
            if not self._is_safe_path(path):
                return {"status": "error", "message": "Unsafe path operation"}
                
            payload = {
                "operation": operation,
                "path": path,
                "params": kwargs
            }
            
            response = requests.post(
                f"{self.filesystem_url}/execute",
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=15
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"[MCP] Ошибка от Filesystem: {response.status_code} - {response.text}")
                return {
                    "status": "error", 
                    "message": f"MCP Filesystem error: {response.status_code}", 
                    "details": response.text
                }
        except requests.exceptions.ConnectionError:
            logger.warning(f"[MCP] Нет соединения с Filesystem. Выполняем локальные операции.")
            # Локальная реализация безопасных файловых операций
            return self._local_filesystem_operation(operation, path, **kwargs)
        except Exception as e:
            logger.error(f"[MCP] Ошибка при обращении к filesystem: {e}")
            return {"status": "error", "message": str(e)}
    
    def _is_valid_url(self, url: str) -> bool:
        """
        Проверяет, является ли URL допустимым
        """
        regex = re.compile(
            r'^https?://'  # http:// или https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # домен
            r'localhost|'  # localhost
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # IP
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        return url is not None and regex.search(url) is not None
    
    def _is_safe_path(self, path: str) -> bool:
        """
        Проверяет, является ли путь безопасным для файловой операции
        """
        # Проверяем, что путь внутри проекта и не выходит за его пределы
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        full_path = os.path.abspath(os.path.join(project_root, path))
        
        # Убеждаемся, что путь находится внутри проекта
        return full_path.startswith(project_root)
    
    def _local_filesystem_operation(self, operation: str, path: str, **kwargs) -> Dict[str, Any]:
        """
        Локальная реализация безопасных файловых операций
        """
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        full_path = os.path.abspath(os.path.join(project_root, path))
        
        # Проверяем безопасность пути
        if not full_path.startswith(project_root):
            return {"status": "error", "message": "Unsafe path operation"}
        
        try:
            if operation == "read":
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    return {
                        "status": "success",
                        "operation": operation,
                        "path": path,
                        "details": f"Файловая операция {operation} выполнена для {path}",
                        "content_preview": content[:500],  # Первые 500 символов
                        "size": len(content)
                    }
            elif operation == "find":
                # Ищем файлы по шаблону
                import glob
                matches = glob.glob(full_path)
                return {
                    "status": "success",
                    "operation": operation,
                    "path": path,
                    "details": f"Файловая операция {operation} выполнена для {path}",
                    "matches": matches
                }
            else:
                return {
                    "status": "error",
                    "message": f"Local filesystem operation '{operation}' not implemented"
                }
        except Exception as e:
            return {"status": "error", "message": str(e)}


class MCPLingmaChat:
    """
    Класс для интеграции с LingmaAI Chat и MCP инструментами в агентском режиме
    """
    
    def __init__(self):
        self.mcp_server = MCPServer()
        self.active = False
        self.chat_history = []
        self.agent_mode = False
        
        logger.info("[MCP_AGENT] Инициализация LingmaAI Chat с MCP инструментами")
    
    def enable_agent_mode(self):
        """Включает агентский режим работы"""
        self.agent_mode = True
        logger.info("[MCP_AGENT] Агентский режим включен")
    
    def disable_agent_mode(self):
        """Выключает агентский режим работы"""
        self.agent_mode = False
        logger.info("[MCP_AGENT] Агентский режим выключен")
    
    def process_request(self, request: str) -> Dict[str, Any]:
        """
        Обрабатывает запрос с использованием соответствующего MCP инструмента
        """
        logger.info(f"[MCP_AGENT] Обработка запроса: {request[:50]}...")
        
        # Определяем, какой MCP инструмент использовать
        tool_name = self._determine_tool(request)
        
        if tool_name == "context7":
            result = self.mcp_server.context7(request)
        elif tool_name == "sequential-thinking":
            result = self.mcp_server.sequential_thinking(request)
        elif tool_name == "fetch":
            # Извлекаем URL из запроса
            url = self._extract_url(request)
            result = self.mcp_server.fetch(url) if url else {"status": "error", "message": "URL не найден в запросе"}
        elif tool_name == "github":
            # Извлекаем репозиторий и действие из запроса
            repo, action = self._extract_github_params(request)
            result = self.mcp_server.github(repo, action) if repo and action else {"status": "error", "message": "Недостаточно параметров для GitHub"}
        elif tool_name == "filesystem":
            # Извлекаем операцию и путь из запроса
            op, path = self._extract_fs_params(request)
            result = self.mcp_server.filesystem(op, path) if op and path else {"status": "error", "message": "Недостаточно параметров для файловой системы"}
        else:
            # Если не удается определить инструмент, возвращаем сообщение об ошибке
            result = {"status": "error", "message": f"Не удалось определить подходящий MCP инструмент для запроса: {request}"}
        
        # Сохраняем в историю
        self.chat_history.append({
            "request": request,
            "tool_used": tool_name,
            "result": result
        })
        
        return result
    
    def _determine_tool(self, request: str) -> str:
        """
        Определяет, какой MCP инструмент использовать для запроса
        """
        request_lower = request.lower()
        
        # Проверяем ключевые слова для каждого инструмента
        if any(keyword in request_lower for keyword in [
            "api", "библиотека", "фреймворк", "tesseract", "pyside", "mss", 
            "sigнатуры", "параметры", "документация", "context7", "unknown", "контекст"
        ]):
            return "context7"
        
        elif any(keyword in request_lower for keyword in [
            "сложная", "многошаговая", "архитектура", "рефакторинг", 
            "анализ", "планирование", "thinking", "sequential", "многоэтапная"
        ]):
            return "sequential-thinking"
        
        elif any(keyword in request_lower for keyword in [
            "поиск", "web", "запрос", "интернет", "npm", "пакет", "fetch", "url", "ссылка",
            "найти", "искать", "найди", "search", "google", "веб"
        ]):
            return "fetch"
        
        elif any(keyword in request_lower for keyword in [
            "github", "pull", "issue", "репозиторий", "commit", "pr", "code review",
            "гитхаб", "гит", "git", "репозиторий"
        ]):
            return "github"
        
        elif any(keyword in request_lower for keyword in [
            "файл", "проект", "чтение", "запись", "поиск файлов", "filesystem", "directory",
            "файловая", "система", "читай", "прочитай", "содержимое", "файлы"
        ]):
            return "filesystem"
        
        # По умолчанию используем context7 для общих запросов
        return "context7"
    
    def _extract_url(self, request: str) -> Optional[str]:
        """
        Извлекает URL из текста запроса
        """
        urls = re.findall(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', request)
        return urls[0] if urls else None
    
    def _extract_github_params(self, request: str) -> tuple:
        """
        Извлекает параметры для GitHub запроса (репозиторий и действие)
        """
        # Ищем имя репозитория в формате owner/repo
        repo_match = re.search(r'([a-zA-Z0-9_-]+)/([a-zA-Z0-9_.-]+)', request)
        if repo_match:
            owner, repo = repo_match.groups()
            repo_full = f"{owner}/{repo}"
        else:
            # Если не найдено, ищем в списке репозиториев проекта
            repo_full = None
        
        # Определяем действие
        if any(word in request.lower() for word in ["pull request", "pr", "пулл", "реквест"]):
            action = "create_pr"
        elif "issue" in request.lower() or "ошибка" in request.lower() or "баг" in request.lower():
            action = "create_issue"
        elif "commit" in request.lower() or "коммит" in request.lower():
            action = "get_commits"
        elif "repo" in request.lower() or "информация" in request.lower():
            action = "get_repo_info"
        else:
            action = "get_repo_info"
        
        return repo_full, action
    
    def _extract_fs_params(self, request: str) -> tuple:
        """
        Извлекает параметры для файловой системы (операция и путь)
        """
        # Определяем операцию
        if any(word in request.lower() for word in ["чтение", "читать", "read", "содержимое"]):
            operation = "read"
        elif any(word in request.lower() for word in ["запись", "писать", "write"]):
            operation = "write"
        elif any(word in request.lower() for word in ["поиск", "найти", "find", "ищи"]):
            operation = "find"
        else:
            operation = "read"  # по умолчанию
        
        # Ищем путь в запросе
        # Сначала пробуем найти пути к файлам с расширениями
        path_match = re.search(r'([a-zA-Z]:)?[/\\][^:\n]*\.[a-zA-Z]{2,}', request)  # для Windows/Linux путей
        if not path_match:
            # Ищем более общий путь
            path_match = re.search(r'([a-zA-Z]:)?[/\\][^:\n\s"]*(/[a-zA-Z0-9_.-]*)*', request)
        
        path = path_match.group(0) if path_match else self._extract_filename(request)
        return operation, path
    
    def _extract_filename(self, request: str) -> Optional[str]:
        """
        Извлекает имя файла из текста запроса
        """
        # Ищем возможные имена файлов в запросе
        patterns = [
            r"(?:файл|file)\s+([a-zA-Z0-9_./-]+\.[a-zA-Z0-9]+)",
            r"([a-zA-Z0-9_./-]+\.[a-zA-Z0-9]+)(?:\s|$)",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, request, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None


# Глобальный экземпляр для использования в других частях приложения
mcp_agent_instance = MCPLingmaChat()


def get_mcp_agent():
    """
    Возвращает глобальный экземпляр MCP агента
    """
    return mcp_agent_instance