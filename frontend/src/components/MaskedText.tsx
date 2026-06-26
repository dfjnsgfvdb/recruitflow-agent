interface MaskedTextProps {
  value?: string | null;
}

export default function MaskedText({ value }: MaskedTextProps) {
  if (!value) {
    return <span>-</span>;
  }
  if (/^1\d{10}$/.test(value)) {
    return <span>{value.replace(/^(\d{3})\d{4}(\d{4})$/, '$1****$2')}</span>;
  }
  return <span>{value}</span>;
}
