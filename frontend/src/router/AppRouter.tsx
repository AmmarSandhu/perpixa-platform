import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import MainLayout from "../layouts/MainLayout";
import Home from "../pages/Home";
import Login from "../pages/Login";
import Register from "../pages/Register";
import NotFound from "../pages/NotFound";
import ProtectedRoute from "./ProtectedRoute";
import DashboardShell from "../pages/dashboard/DashboardShell";

export default function AppRouter() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Public + shared layout routes */}
        <Route element={<MainLayout />}>
          <Route path="/" element={<Home />} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />

          {/* Dashboard base → redirect to default tool */}
          <Route
            path="/dashboard"
            element={
              <ProtectedRoute>
                <Navigate to="/dashboard/video" replace />
              </ProtectedRoute>
            }
          />

          {/* Tool-specific dashboards */}
          <Route
            path="/dashboard/:tool"
            element={
              <ProtectedRoute>
                <DashboardShell />
              </ProtectedRoute>
            }
          />
        </Route>

        {/* Fallback */}
        <Route path="*" element={<NotFound />} />
      </Routes>
    </BrowserRouter>
  );
}
