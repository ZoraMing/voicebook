/** @type {import('next').NextConfig} */
const nextConfig = {
    // API 代理配置 - 将前端请求转发到后端
    async rewrites() {
        return [
            {
                source: '/api/:path*',
                destination: 'http://localhost:8000/api/:path*'
            }
        ]
    }
}

export default nextConfig
