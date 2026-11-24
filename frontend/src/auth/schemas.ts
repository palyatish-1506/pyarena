import { z } from "zod";

export const loginSchema = z.object({
  email: z.string().email("Enter a valid email"),
  password: z.string().min(8, "Password must be at least 8 characters"),
});
export type LoginForm = z.infer<typeof loginSchema>;

export const registerSchema = z
  .object({
    email: z.string().email("Enter a valid email"),
    full_name: z.string().max(120).optional(),
    password: z.string().min(8, "Password must be at least 8 characters"),
    password_confirm: z.string(),
    roll_no: z.string().max(20).optional(),
    division: z.string().max(10).optional(),
  })
  .refine((d) => d.password === d.password_confirm, {
    message: "Passwords do not match",
    path: ["password_confirm"],
  });
export type RegisterForm = z.infer<typeof registerSchema>;
