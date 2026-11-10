interface SectionHeadingProps { number: string; title: string; description: string; badge?: React.ReactNode }
/** Shared numbered section heading matching the existing dashboard treatment. */
export function SectionHeading({ number, title, description, badge }: SectionHeadingProps) {
  return <div className="section-heading"><div><h2>{number} <span>{title}</span></h2><p>{description}</p></div>{badge}</div>;
}
