import { Link } from "react-router-dom";

export function NotFoundPage() {
  return (
    <section className="space-y-3">
      <h1 className="text-2xl font-bold">404</h1>
      <p className="text-surface-800/70">That page doesn't exist.</p>
      <Link to="/" className="text-primary-600 underline">
        Back home
      </Link>
    </section>
  );
}
