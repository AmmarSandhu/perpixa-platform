interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label: string;
}

export default function Input({ label, ...props }: InputProps) {
  return (
    <label className="block space-y-1">
      <span className="text-sm text-text-secondary">{label}</span>
      <input
        {...props}
        className="w-full rounded-md border border-border-subtle px-3 py-2
                   focus:outline-none focus:ring-2 focus:ring-brand-blue"
      />
    </label>
  );
}
