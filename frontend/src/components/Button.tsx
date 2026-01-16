interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {}

export default function Button({ children, ...props }: ButtonProps) {
  return (
    <button
      {...props}
      className="w-full rounded-md bg-brand-mid text-white py-2
                 hover:bg-brand-purple transition disabled:opacity-50"
    >
      {children}
    </button>
  );
}
