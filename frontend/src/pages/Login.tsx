import { useState } from "react";
import Input from "../components/Input";
import Button from "../components/Button";
import { login } from "../api/auth";
import { setToken } from "../api/authStorage";

export default function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const res = await login({ email, password });
      setToken(res.access_token);
      window.location.href = "/dashboard";
    } catch (err: any) {
      setError(err?.detail || "Login failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="max-w-md mx-auto py-16 px-6">
      <h2 className="text-2xl font-semibold mb-6">Sign in to Perpixa</h2>

      <form onSubmit={handleSubmit} className="space-y-4">
        <Input
          label="Email"
          type="email"
          required
          value={email}
          onChange={(e) => setEmail(e.target.value)}
        />

        <Input
          label="Password"
          type="password"
          required
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />

        {error && <p className="text-sm text-red-600">{error}</p>}

        <Button disabled={loading}>
          {loading ? "Signing in..." : "Sign In"}
        </Button>
      </form>
    </div>
  );
}
