export function AuthDivider() {
  return (
    <div className="relative my-4 flex items-center" aria-hidden="true">
      <div className="flex-1 border-t border-zinc-200" />
      <span className="px-3 text-xs uppercase tracking-wider text-zinc-400">
        or
      </span>
      <div className="flex-1 border-t border-zinc-200" />
    </div>
  );
}
