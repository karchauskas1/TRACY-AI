/** @type {import('next').NextConfig} */
const isProd = process.env.NODE_ENV === 'production'
const repoName = process.env.GITHUB_REPOSITORY?.split('/')[1] || 'tracy-ai-bot'

const nextConfig = {
  output: 'export',
  basePath: isProd ? `/${repoName}` : '',
  images: {
    unoptimized: true,
  },
  trailingSlash: true,
}

module.exports = nextConfig

