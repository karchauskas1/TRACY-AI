"""
Telegram Proxy для обработки запросов из Mini App.
Позволяет Mini App делать HTTP запросы через бота.
"""
import logging
import json
import httpx
from typing import Dict, Any, Optional
from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

# Базовый URL API сервера
API_BASE_URL = "http://localhost:8080"


class TelegramProxy:
    """Прокси для обработки запросов из Telegram Mini App."""
    
    def __init__(self, api_base_url: str = API_BASE_URL):
        self.api_base_url = api_base_url.rstrip('/')
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def close(self):
        """Закрывает HTTP клиент."""
        await self.client.aclose()
    
    async def handle_request(
        self, 
        endpoint: str,
        method: str = "GET",
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Выполняет HTTP запрос к API серверу.
        
        Args:
            endpoint: API эндпоинт (например, "/api/events")
            method: HTTP метод (GET, POST, PUT, DELETE)
            params: Query параметры
            data: Тело запроса (для POST/PUT)
        
        Returns:
            Dict с результатом запроса
        """
        try:
            url = f"{self.api_base_url}{endpoint}"
            logger.info(f"📡 Proxy request: {method} {url} params={params}")
            
            if method.upper() == "GET":
                response = await self.client.get(url, params=params)
            elif method.upper() == "POST":
                response = await self.client.post(url, params=params, json=data)
            elif method.upper() == "PUT":
                response = await self.client.put(url, params=params, json=data)
            elif method.upper() == "DELETE":
                response = await self.client.delete(url, params=params)
            else:
                return {
                    "success": False,
                    "error": f"Unsupported HTTP method: {method}"
                }
            
            # Обрабатываем ответ
            if response.status_code == 200:
                try:
                    result = response.json()
                    logger.info(f"✅ Proxy response: {response.status_code}")
                    return {
                        "success": True,
                        "data": result,
                        "status": response.status_code
                    }
                except json.JSONDecodeError:
                    return {
                        "success": True,
                        "data": response.text,
                        "status": response.status_code
                    }
            else:
                logger.error(f"❌ Proxy error: {response.status_code} {response.text}")
                try:
                    error_data = response.json()
                except:
                    error_data = {"error": response.text}
                
                return {
                    "success": False,
                    "error": error_data,
                    "status": response.status_code
                }
        
        except httpx.TimeoutException:
            logger.error("❌ Proxy timeout")
            return {
                "success": False,
                "error": "Request timeout"
            }
        except Exception as e:
            logger.error(f"❌ Proxy exception: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }


# Глобальный экземпляр прокси
telegram_proxy = TelegramProxy()


async def web_app_data_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработчик данных от Telegram Mini App.
    
    Mini App отправляет JSON через Telegram.WebApp.sendData():
    {
        "type": "api_request",
        "request_id": "uuid",
        "endpoint": "/api/events",
        "method": "GET",
        "params": {"user_id": 123},
        "data": null
    }
    
    Бот выполняет запрос к API и отправляет ответ обратно.
    """
    try:
        # Получаем данные от Mini App
        if not update.message or not update.message.web_app_data:
            logger.warning("❌ No web_app_data in update")
            return
        
        raw_data = update.message.web_app_data.data
        logger.info(f"📥 Received Mini App data: {raw_data[:200]}...")
        
        try:
            request_data = json.loads(raw_data)
        except json.JSONDecodeError as e:
            logger.error(f"❌ Invalid JSON from Mini App: {e}")
            await update.message.reply_text(
                f"❌ Ошибка: неверный формат данных\n{str(e)}"
            )
            return
        
        # Проверяем тип запроса
        if request_data.get("type") != "api_request":
            logger.warning(f"❌ Unknown request type: {request_data.get('type')}")
            await update.message.reply_text(
                f"❌ Неизвестный тип запроса: {request_data.get('type')}"
            )
            return
        
        # Извлекаем параметры запроса
        request_id = request_data.get("request_id", "unknown")
        endpoint = request_data.get("endpoint")
        method = request_data.get("method", "GET")
        params = request_data.get("params")
        data = request_data.get("data")
        
        if not endpoint:
            await update.message.reply_text("❌ Не указан endpoint")
            return
        
        logger.info(f"🔄 Processing API request: {method} {endpoint}")
        
        # Выполняем запрос через прокси
        result = await telegram_proxy.handle_request(
            endpoint=endpoint,
            method=method,
            params=params,
            data=data
        )
        
        # Формируем ответ
        response = {
            "type": "api_response",
            "request_id": request_id,
            "result": result
        }
        
        # Отправляем ответ обратно в Mini App
        # ВАЖНО: Telegram не поддерживает прямую отправку данных обратно в Mini App
        # Поэтому используем альтернативный подход - сохраняем в context.bot_data
        # и Mini App будет делать polling или использовать другой механизм
        
        # Для демонстрации отправляем как текстовое сообщение
        response_text = json.dumps(response, ensure_ascii=False, indent=2)
        
        # Ограничиваем размер (Telegram лимит 4096 символов)
        if len(response_text) > 4000:
            response_text = response_text[:4000] + "\n..."
        
        await update.message.reply_text(
            f"✅ Результат запроса:\n```json\n{response_text}\n```",
            parse_mode="Markdown"
        )
        
        logger.info(f"✅ Response sent for request {request_id}")
    
    except Exception as e:
        logger.error(f"❌ Error in web_app_data_handler: {e}", exc_info=True)
        await update.message.reply_text(
            f"❌ Ошибка обработки запроса:\n{str(e)}"
        )


async def cleanup_proxy():
    """Очистка ресурсов прокси."""
    await telegram_proxy.close()

