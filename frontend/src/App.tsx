import { Route, Routes } from "react-router-dom";
import { Layout } from "./components/Layout";
import { ProtectedRoute } from "./components/ProtectedRoute";
import { SeniorOnly } from "./components/SeniorOnly";
import { HomePage } from "./pages/HomePage";
import { LeaderboardsPage } from "./pages/LeaderboardsPage";
import { PrivacyPage } from "./pages/PrivacyPage";
import { LiveQuizPage } from "./pages/LiveQuizPage";
import { LoginPage } from "./pages/LoginPage";
import { NotFoundPage } from "./pages/NotFoundPage";
import { ProfilePage } from "./pages/ProfilePage";
import { QuestionDetailPage } from "./pages/QuestionDetailPage";
import { RegisterPage } from "./pages/RegisterPage";
import { ForgotPasswordPage } from "./pages/ForgotPasswordPage";
import { ResetPasswordPage } from "./pages/ResetPasswordPage";
import { SeniorDashboardPage } from "./pages/SeniorDashboardPage";
import { HistoryPage } from "./pages/HistoryPage";

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<HomePage />} />
        <Route path="leaderboard" element={<LeaderboardsPage />} />
        <Route path="privacy" element={<PrivacyPage />} />
        <Route path="live/:code" element={<LiveQuizPage />} />
        <Route path="live" element={<LiveQuizPage />} />
        <Route path="login" element={<LoginPage />} />
        <Route path="register" element={<RegisterPage />} />
        <Route path="forgot-password" element={<ForgotPasswordPage />} />
        <Route path="reset-password" element={<ResetPasswordPage />} />
        <Route path="questions/:id" element={<QuestionDetailPage />} />
        <Route
          path="history"
          element={
            <ProtectedRoute>
              <HistoryPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="profile"
          element={
            <ProtectedRoute>
              <ProfilePage />
            </ProtectedRoute>
          }
        />
        <Route
          path="senior"
          element={
            <ProtectedRoute>
              <SeniorOnly>
                <SeniorDashboardPage />
              </SeniorOnly>
            </ProtectedRoute>
          }
        />
        <Route path="*" element={<NotFoundPage />} />
      </Route>
    </Routes>
  );
}
