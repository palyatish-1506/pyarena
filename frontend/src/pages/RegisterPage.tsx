import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import { AxiosError } from "axios";
import { useAuth } from "../auth/AuthContext";
import { registerSchema, type RegisterForm } from "../auth/schemas";

const inputClass = "w-full rounded-lg border border-surface-200 px-3 py-2";
const labelClass = "mb-1 block text-sm font-medium";

export function RegisterPage() {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState<RegisterForm>({
    email: "",
    password: "",
    password_confirm: "",
    full_name: "",
    roll_no: "",
    division: "",
  });
  const [errors, setErrors] = useState<Partial<Record<string, string>>>({});
  const [serverError, setServerError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  function set<K extends keyof RegisterForm>(key: K, value: RegisterForm[K]) {
    setForm((f) => ({ ...f, [key]: value }));
  }

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setServerError("");
    const parsed = registerSchema.safeParse(form);
    if (!parsed.success) {
      const fieldErrors: Record<string, string> = {};
      for (const issue of parsed.error.issues) {
        fieldErrors[String(issue.path[0])] = issue.message;
      }
      setErrors(fieldErrors);
      return;
    }
    setErrors({});
    setSubmitting(true);
    try {
      await register(form);
      navigate("/");
    } catch (err) {
      if (err instanceof AxiosError && err.response?.status === 400) {
        const data = err.response.data as Record<string, string[]>;
        const first = Object.entries(data)[0];
        setServerError(first ? `${first[0]}: ${first[1][0]}` : "Check the form and try again.");
      } else {
        setServerError("Something went wrong. Try again.");
      }
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="mx-auto max-w-sm space-y-6">
      <h1 className="text-2xl font-bold">Create account</h1>
      <form onSubmit={onSubmit} className="space-y-4" noValidate>
        <div>
          <label htmlFor="full_name" className={labelClass}>
            Full name <span className="text-surface-800/50">(optional)</span>
          </label>
          <input
            id="full_name"
            value={form.full_name}
            onChange={(e) => set("full_name", e.target.value)}
            className={inputClass}
          />
        </div>
        <div>
          <label htmlFor="email" className={labelClass}>
            Email
          </label>
          <input
            id="email"
            type="email"
            autoComplete="email"
            value={form.email}
            onChange={(e) => set("email", e.target.value)}
            className={inputClass}
          />
          {errors.email && <p className="mt-1 text-sm text-error-500">{errors.email}</p>}
        </div>
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label htmlFor="roll_no" className={labelClass}>
              Roll no.
            </label>
            <input
              id="roll_no"
              value={form.roll_no}
              onChange={(e) => set("roll_no", e.target.value)}
              className={inputClass}
            />
          </div>
          <div>
            <label htmlFor="division" className={labelClass}>
              Division
            </label>
            <input
              id="division"
              value={form.division}
              onChange={(e) => set("division", e.target.value)}
              className={inputClass}
            />
          </div>
        </div>
        <div>
          <label htmlFor="password" className={labelClass}>
            Password
          </label>
          <input
            id="password"
            type="password"
            autoComplete="new-password"
            value={form.password}
            onChange={(e) => set("password", e.target.value)}
            className={inputClass}
          />
          {errors.password && (
            <p className="mt-1 text-sm text-error-500">{errors.password}</p>
          )}
        </div>
        <div>
          <label htmlFor="password_confirm" className={labelClass}>
            Confirm password
          </label>
          <input
            id="password_confirm"
            type="password"
            autoComplete="new-password"
            value={form.password_confirm}
            onChange={(e) => set("password_confirm", e.target.value)}
            className={inputClass}
          />
          {errors.password_confirm && (
            <p className="mt-1 text-sm text-error-500">{errors.password_confirm}</p>
          )}
        </div>
        {serverError && <p className="text-sm text-error-500">{serverError}</p>}
        <button
          type="submit"
          disabled={submitting}
          className="w-full rounded-lg bg-primary-600 px-4 py-2 font-medium text-white hover:bg-primary-700 disabled:opacity-50"
        >
          {submitting ? "Creating account…" : "Sign up"}
        </button>
      </form>
      <p className="text-sm text-surface-800/70">
        Already have an account?{" "}
        <Link to="/login" className="text-primary-600 underline">
          Log in
        </Link>
      </p>
    </div>
  );
}
