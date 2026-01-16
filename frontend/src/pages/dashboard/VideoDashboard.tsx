export default function VideoDashboard() {
  return (
    <div className="max-w-7xl mx-auto px-6 py-10 space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-semibold">Video Generator</h1>
        <p className="text-text-secondary">
          Generate AI-powered videos from prompts.
        </p>
      </div>

      {/* Credits */}
      <div className="rounded-lg border border-border-subtle p-4 bg-white">
        <p className="text-sm text-text-muted">Credits remaining</p>
        <p className="text-2xl font-semibold">—</p>
      </div>

      {/* Job Creation */}
      <div className="rounded-lg border border-border-subtle p-6">
        <h2 className="text-lg font-medium mb-4">Create new video</h2>
        <p className="text-text-muted text-sm">
          Video generation form will appear here.
        </p>
      </div>

      {/* Job List */}
      <div className="rounded-lg border border-border-subtle p-6">
        <h2 className="text-lg font-medium mb-4">Your videos</h2>
        <p className="text-text-muted text-sm">
          No video jobs yet.
        </p>
      </div>
    </div>
  );
}
