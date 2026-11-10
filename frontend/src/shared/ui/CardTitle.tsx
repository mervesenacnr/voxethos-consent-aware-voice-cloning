interface CardTitleProps { label: string; title: string; trailing?: React.ReactNode }
/** Shared card title row used by telemetry and result cards. */
export function CardTitle({ label, title, trailing }: CardTitleProps) {
  return <div className="card-title"><div><span className="tiny-label">{label}</span><h3>{title}</h3></div>{trailing}</div>;
}
