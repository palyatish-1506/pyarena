export function PrivacyPage() {
  return (
    <article className="prose mx-auto max-w-2xl space-y-4">
      <h1 className="text-2xl font-bold">Privacy Policy</h1>
      <p className="text-sm text-surface-800/70">Last updated: Nov 2025</p>

      <section className="space-y-2 text-sm">
        <h2 className="text-lg font-semibold">What we store</h2>
        <ul className="list-disc pl-5">
          <li><strong>Account:</strong> email, password (hashed — never stored plain), full name, roll number, branch, year, division.</li>
          <li><strong>Activity:</strong> question submissions (answers, points, time taken), comments you post, XP/level/streak, badges earned.</li>
          <li><strong>Technical:</strong> IP address (rate limiting only), timestamps, request IDs in logs.</li>
        </ul>
      </section>

      <section className="space-y-2 text-sm">
        <h2 className="text-lg font-semibold">Why</h2>
        <ul className="list-disc pl-5">
          <li>Answers & scores power leaderboards, streaks, and badges — the learning loop.</li>
          <li>Email is used for login and password resets only.</li>
          <li>Roll number/division are for leaderboard grouping — never shown publicly beyond your display name.</li>
          <li>We do <strong>not</strong> sell data, run ads, or share it with third parties except infrastructure providers (Render, Vercel, Brevo for email).</li>
        </ul>
      </section>

      <section className="space-y-2 text-sm">
        <h2 className="text-lg font-semibold">Your controls</h2>
        <ul className="list-disc pl-5">
          <li>Edit profile anytime on the Profile page.</li>
          <li>Comment authors can ask an admin to hide/remove their comment.</li>
          <li>To delete your account and all data, email the admin — we remove everything within 7 days.</li>
        </ul>
      </section>

      <section className="space-y-2 text-sm">
        <h2 className="text-lg font-semibold">Security</h2>
        <p>
          Passwords are hashed with Django's PBKDF2. Auth uses short-lived JWT access
          tokens (in memory only) + httpOnly refresh cookies. All traffic is HTTPS.
          Admin endpoints are staff-only.
        </p>
      </section>
    </article>
  );
}
