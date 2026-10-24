import { Button } from "@/components/ui/button";
import { publicEnv } from "@/lib/env";

export default function Home() {
  return (
    <main className="mx-auto flex w-full max-w-3xl flex-1 flex-col justify-center gap-6 px-6 py-24">
      <h1 className="font-heading text-3xl font-semibold tracking-tight">
        CAWASMA
      </h1>
      <p className="text-lg text-muted-foreground">
        Context-Aware Web &amp; API Security Misconfiguration Analyzer
      </p>
      <div>
        <Button
          nativeButton={false}
          render={<a href={`${publicEnv.apiUrl}/docs`} />}
        >
          API docs
        </Button>
      </div>
    </main>
  );
}
