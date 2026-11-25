export default function Panel({ eyebrow, title, action, children, className = '' }) {
  return (
    <section className={`rounded-2xl border border-border bg-card p-5 shadow-soft sm:p-6 ${className}`}>
      {(eyebrow || title || action) && (
        <header className="mb-5 grid grid-cols-[minmax(0,1fr)_auto] items-start gap-3">
          <div className="min-w-0">
            {eyebrow && <p className="text-[11px] font-bold uppercase tracking-[0.14em] text-primary">{eyebrow}</p>}
            {title && <h2 className="mt-1 truncate text-lg font-bold text-foreground">{title}</h2>}
          </div>
          {action}
        </header>
      )}
      {children}
    </section>
  )
}
