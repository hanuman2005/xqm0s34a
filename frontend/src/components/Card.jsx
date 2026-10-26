// White panel with a title. Shows a loading or error message instead of the content when needed.
export default function Card({ title, subtitle, state, children, className = '' }) {
  let body = children
  if (state?.loading && !state?.data) body = <p className="card-message">Loading…</p>
  else if (state?.error) body = <p className="card-message card-error">{state.error}</p>

  return (
    <section className={`card ${className}`}>
      <header className="card-header">
        <h2>{title}</h2>
        {subtitle && <p>{subtitle}</p>}
      </header>
      {body}
    </section>
  )
}
