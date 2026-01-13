/** @type {import('next').NextConfig} */
const path = require('path')
const isProd = process.env.NODE_ENV === 'production'
// Репозиторий называется TRACY-AI на GitHub
const repoName = process.env.GITHUB_REPOSITORY?.split('/')[1] || 'TRACY-AI'

const nextConfig = {
  output: 'export',
  basePath: isProd ? `/${repoName}` : '',
  images: {
    unoptimized: true,
  },
  trailingSlash: true,
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || (isProd ? 'https://api.pasekaproduction.ru' : 'http://localhost:8080'),
  },
  webpack: (config) => {
    // Явно настраиваем алиас для разрешения @/ путей
    const rootPath = path.resolve(__dirname)
    config.resolve.alias = {
      ...config.resolve.alias,
      '@': rootPath,
    }
    // Также настраиваем modules для правильного разрешения
    config.resolve.modules = [
      ...(config.resolve.modules || []),
      rootPath,
    ]
    return config
  },
}

module.exports = nextConfig

