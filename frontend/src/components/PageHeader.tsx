import type { ReactNode } from 'react';

interface PageHeaderProps {
  title: string;
  description?: string;
  extra?: ReactNode;
}

export default function PageHeader({ title, description, extra }: PageHeaderProps) {
  return (
    <div className="page-header">
      <div>
        <h1>{title}</h1>
        {description ? <p>{description}</p> : null}
      </div>
      {extra ? <div className="page-header-extra">{extra}</div> : null}
    </div>
  );
}
