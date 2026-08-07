import { SignOutButton } from "@/components/auth/sign-out-button";

export default function HomePage() {
  return (
    <main className="grid min-h-screen place-items-center gap-4 p-6">
      <p className="text-sm text-zinc-600">Authenticated SalesOS session</p>
      <SignOutButton />
    </main>
  );
}
