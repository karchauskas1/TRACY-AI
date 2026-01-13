/** @type {import('next').NextConfig} */
const nextConfig = {
  // SSG/CSR режим для Vercel - НЕ используем export
  // output: 'export', // УДАЛЕНО - используем серверный режим
  
  // Корневые роуты - НЕТ basePath
  // basePath: '/TRACY-AI', // УДАЛЕНО - домен будет корневым
  
  // Отключаем строгий режим для совместимости с Telegram SDK
  reactStrictMode: false,
  
  // Оптимизации для production
  swcMinify: true,
  
  // Разрешаем изображения с внешних доменов
  images: {
    domains: ['api.pasekaproduction.ru'],
    unoptimized: false, // Включаем оптимизацию на Vercel
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
    ]
  },
  
  // Rewrites для правильной работы роутинга на Vercel
  async rewrites() {
    return [
      {
        source: '/:path*',
        destination: '/:path*',
      },
    ]
  },
}

module.exports = nextConfig
