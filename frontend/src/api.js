// API 地址配置：本地用代理，线上用环境变量
const API = import.meta.env.VITE_API_URL || '/api'
export default API
