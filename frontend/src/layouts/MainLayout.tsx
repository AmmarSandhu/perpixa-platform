import { Outlet, Link, useNavigate } from "react-router-dom";
import logo from "../assets/logo.svg";
import { isAuthenticated, clearToken } from "../api/authStorage";

export default function MainLayout() {
  const navigate = useNavigate();
  const authenticated = isAuthenticated();

  function handleLogout() {
    clearToken();
    navigate("/login");
  }

  return (
    <div className="min-h-screen flex flex-col">
      <header className="border-b border-border-subtle">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          {/* Logo */}
          <div className="flex items-center gap-3">
            <img src={logo} alt="Perpixa" className="h-8" />
            <span className="font-semibold text-lg">Perpixa</span>
          </div>

          {/* Navigation */}
          <nav className="flex items-center gap-4 text-sm">
            {!authenticated && (
              <>
                <Link
                  to="/login"
                  className="text-text-secondary hover:text-text-primary"
                >
                  Login
                </Link>
                <Link
                  to="/register"
                  className="px-3 py-1.5 rounded-md bg-brand-mid text-white hover:bg-brand-purple"
                >
                  Sign up
                </Link>
              </>
            )}

            {authenticated && (
              <>
                <Link
                  to="/dashboard/video"
                  className="text-text-secondary hover:text-text-primary"
                >
                  Dashboard
                </Link>
                <button
                  onClick={handleLogout}
                  className="text-text-secondary hover:text-text-primary"
                >
                  Logout
                </button>
              </>
            )}
          </nav>
        </div>
      </header>

      <main className="flex-1">
        <Outlet />
      </main>

      <footer className="border-t border-border-subtle">
        <div className="max-w-7xl mx-auto px-6 py-4 text-sm text-text-muted">
          © {new Date().getFullYear()} Perpixa. All rights reserved.
        </div>
      </footer>
    </div>
  );
}
