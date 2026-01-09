/** @type {import('next').NextConfig} */
const path = require('path')
const isProd = process.env.NODE_ENV === 'production'
const repoName = process.env.GITHUB_REPOSITORY?.split('/')[1] || 'tracy-ai-bot'

const nextConfig = {
  output: 'export',
  basePath: isProd ? `/${repoName}` : '',
  images: {
    unoptimized: true,
  },
  trailingSlash: true,
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

