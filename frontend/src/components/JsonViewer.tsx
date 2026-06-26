interface JsonViewerProps {
  data?: unknown;
}

export default function JsonViewer({ data }: JsonViewerProps) {
  if (data === undefined || data === null || data === '') {
    return <div className="json-empty">暂无数据</div>;
  }

  return <pre className="json-viewer">{JSON.stringify(data, null, 2)}</pre>;
}
