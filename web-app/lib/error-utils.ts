/**
 * Утилиты для форматирования и отображения ошибок
 */

export interface ErrorDetails {
  code?: number | string // HTTP статус код или код ошибки
  errorNumber?: string // Номер ошибки из API
  message: string // Описание ошибки
  context?: string // Контекст (с чем связана ошибка)
  rawError?: any // Исходная ошибка для отладки
}

/**
 * Форматирует ошибку для отображения пользователю
 */
export function formatError(error: any, context: string = "Операция"): ErrorDetails {
  const details: ErrorDetails = {
    message: "Произошла неизвестная ошибка",
    context,
    rawError: error,
  }

  // Если это объект с полями error
  if (error && typeof error === "object") {
    // Проверяем наличие HTTP статуса
    if (error.status || error.statusCode) {
      details.code = error.status || error.statusCode
    }

    // Проверяем наличие номера ошибки
    if (error.errorNumber || error.error_number || error.code) {
      details.errorNumber = String(error.errorNumber || error.error_number || error.code)
    }

    // Проверяем наличие сообщения об ошибке
    if (error.error || error.message) {
      details.message = error.error || error.message
    }

    // Если есть вложенная ошибка
    if (error.data?.error) {
      details.message = error.data.error
      if (error.data.errorNumber) {
        details.errorNumber = String(error.data.errorNumber)
      }
    }
  }

  // Если это строка
  if (typeof error === "string") {
    details.message = error
  }

  // Если это Error объект
  if (error instanceof Error) {
    details.message = error.message
    if (error.name) {
      details.context = `${context} (${error.name})`
    }
  }

  return details
}

/**
 * Парсит ошибку из HTTP ответа
 */
export async function parseHttpError(response: Response, context: string = "Запрос"): Promise<ErrorDetails> {
  const details: ErrorDetails = {
    code: response.status,
    message: response.statusText || "Ошибка при выполнении запроса",
    context,
  }

  try {
    const responseText = await response.text()
    if (responseText) {
      try {
        const errorData = JSON.parse(responseText)
        
        // Извлекаем номер ошибки
        if (errorData.errorNumber || errorData.error_number || errorData.code) {
          details.errorNumber = String(errorData.errorNumber || errorData.error_number || errorData.code)
        }

        // Извлекаем сообщение об ошибке
        if (errorData.error) {
          details.message = errorData.error
        } else if (errorData.message) {
          details.message = errorData.message
        }

        // Если есть детали
        if (errorData.details) {
          details.message += `: ${errorData.details}`
        }
      } catch {
        // Если не JSON, используем текст как есть
        details.message = responseText.substring(0, 200) // Ограничиваем длину
      }
    }
  } catch (e) {
    // Игнорируем ошибки парсинга
    console.error("[ErrorUtils] Ошибка парсинга ответа:", e)
  }

  return details
}

/**
 * Форматирует детали ошибки для отображения в UI
 */
export function formatErrorForDisplay(details: ErrorDetails): string {
  const parts: string[] = []

  // Контекст
  if (details.context) {
    parts.push(`[${details.context}]`)
  }

  // Код ошибки
  if (details.code) {
    parts.push(`Код: ${details.code}`)
  }

  // Номер ошибки
  if (details.errorNumber) {
    parts.push(`Ошибка #${details.errorNumber}`)
  }

  // Сообщение
  parts.push(details.message)

  return parts.join(" | ")
}

/**
 * Получает детали ошибки из исключения
 */
export async function getErrorDetails(
  error: any,
  response?: Response,
  context: string = "Операция"
): Promise<ErrorDetails> {
  // Если есть HTTP ответ, парсим его
  if (response) {
    return await parseHttpError(response, context)
  }

  // Иначе форматируем ошибку
  return formatError(error, context)
}

