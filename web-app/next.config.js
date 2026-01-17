/** @type {import('next').NextConfig} */
const nextConfig = {
  // Серверный режим (SSR) - не static export
  // output: 'export', // Отключено - используем SSR
  
  // Корневые роуты - НЕТ basePath
  // basePath: '/TRACY-AI', // УДАЛЕНО - домен будет корневым
  
  // Отключаем строгий режим для совместимости с Telegram SDK
  reactStrictMode: false,
  
  // Оптимизации для production
  swcMinify: true,
  
  // Разрешаем изображения с внешних доменов
  images: {
    domains: ['api.pasekaproduction.ru'],
    unoptimized: false,
  },
  
  // Environment variables доступные на клиенте
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || '',
    NEXT_PUBLIC_TELEGRAM_BOT_USERNAME: process.env.NEXT_PUBLIC_TELEGRAM_BOT_USERNAME || '',
  },
  
  // Headers для безопасности и CORS
  async headers() {
    return [
      {
        // HTML страницы - no-store для предотвращения кеширования в Telegram WebView
        source: '/:path*',
        headers: [
          {
            key: 'X-Frame-Options',
            value: 'SAMEORIGIN',
          },
          {
            key: 'X-Content-Type-Options',
            value: 'nosniff',
          },
        ],
      },
      {
        // HTML страницы (не статические файлы) - no-store
        source: '/:path((?!_next|static|favicon|.*\\..*).*)',
        headers: [
          {
            key: 'Cache-Control',
            value: 'no-store, no-cache, must-revalidate, proxy-revalidate, max-age=0',
          },
        ],
      },
    ]
  },
}

module.exports = nextConfig
