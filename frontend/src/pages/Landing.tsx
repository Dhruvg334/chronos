export default function Landing() {
  return (
    <div className="min-h-screen bg-warm-ivory text-text-primary flex flex-col items-center justify-center p-6 text-center">
      <header className="max-w-3xl">
        <h1 className="text-5xl font-extrabold tracking-tight mb-4">
          Chron<span className="text-accent-amber">OS</span>
        </h1>
        <p className="text-xl text-text-secondary mb-8">
          Your time does not need another list. It needs an operating system.
        </p>
        <div className="flex gap-4 justify-center">
          <a
            href="/login"
            className="px-6 py-3 bg-accent-amber text-white font-semibold rounded-lg shadow-md hover:bg-accent-terracotta transition"
          >
            Open ChronOS
          </a>
          <a
            href="/command"
            className="px-6 py-3 bg-warm-surface text-text-secondary font-semibold rounded-lg border border-warm-border hover:bg-white transition"
          >
            View Demo Canvas
          </a>
        </div>
      </header>
    </div>
  );
}
