import axios, { type AxiosError, type AxiosRequestConfig } from 'axios';
import { message } from 'antd';

const apiBaseURL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';

const http = axios.create({
  baseURL: apiBaseURL,
  timeout: 30000,
});

export interface RequestConfig extends AxiosRequestConfig {
  skipErrorMessage?: boolean;
}

http.interceptors.response.use(
  (response) => response.data,
  (error: AxiosError<{ detail?: string; message?: string }>) => {
    const config = error.config as RequestConfig | undefined;
    const errorMessage =
      error.response?.data?.detail ||
      error.response?.data?.message ||
      error.message ||
      '请求失败，请检查后端服务是否启动。';

    if (!config?.skipErrorMessage) {
      message.error(errorMessage);
    }
    return Promise.reject(error);
  },
);

export function request<T>(config: RequestConfig): Promise<T> {
  return http.request<unknown, T>(config);
}

export default http;
