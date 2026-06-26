import { ConfigProvider } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import dayjs from 'dayjs';
import 'dayjs/locale/zh-cn';
import AppRouter from './router';

dayjs.locale('zh-cn');

export default function App() {
  return (
    <ConfigProvider locale={zhCN} theme={{ token: { colorPrimary: '#2155d9', borderRadius: 10 } }}>
      <AppRouter />
    </ConfigProvider>
  );
}
