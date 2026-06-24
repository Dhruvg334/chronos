export default function Login() {
  return (
    <div className="min-h-screen bg-warm-ivory text-text-primary flex flex-col items-center justify-center p-6">
      <div className="bg-white border border-warm-border p-8 rounded-2xl shadow-sm w-full max-w-md">
        <h2 className="text-3xl font-bold mb-6 text-center">
          Login to Chron<span className="text-accent-amber">OS</span>
        </h2>
        <form onSubmit={(e) => e.preventDefault()} className="space-y-4">
          <div>
            <label className="block text-sm font-semibold text-text-secondary mb-1">Email Address</label>
            <input
              type="email"
              disabled
              placeholder="disabled for Phase 0"
              className="w-full p-3 border border-warm-border rounded-lg bg-warm-cream"
            />
          </div>
          <div>
            <label className="block text-sm font-semibold text-text-secondary mb-1">Password</label>
            <input
              type="password"
              disabled
              placeholder="disabled for Phase 0"
              className="w-full p-3 border border-warm-border rounded-lg bg-warm-cream"
            />
          </div>
          <button
            type="submit"
            disabled
            className="w-full py-3 bg-warm-surface text-text-muted rounded-lg font-semibold border border-warm-border"
          >
            Sign In
          </button>
        </form>
        <p className="mt-4 text-center text-sm text-text-secondary">
          Don't have an account? <a href="/signup" className="text-accent-amber hover:underline">Sign up</a>
        </p>
      </div>
    </div>
  );
}
