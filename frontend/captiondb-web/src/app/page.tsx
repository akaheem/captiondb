// ============================================================
// Home page — redirects to /auth/login or /dashboard
// ============================================================
// This is not a landing page — CaptionDB is a private app.
// Authenticated users go to dashboard, guests go to login.
// ============================================================

import { redirect } from "next/navigation";
import { ROUTES } from "@/lib/routes";

// On the server we can't know if the user is logged in
// (no cookies yet — tokens are in sessionStorage).
// So we redirect to /dashboard which has the ProtectedRoute guard;
// if not authenticated it will redirect to /auth/login.
export default function HomePage() {
  redirect(ROUTES.dashboard);
}
