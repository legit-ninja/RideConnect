import styles from "./page.module.css";

interface HealthResponse {
  status: string;
}

async function fetchHealth(): Promise<HealthResponse | null> {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

  try {
    const response = await fetch(`${apiUrl}/health`, {
      next: { revalidate: 0 },
    });

    if (!response.ok) {
      return null;
    }

    return (await response.json()) as HealthResponse;
  } catch {
    return null;
  }
}

export default async function Home() {
  const health = await fetchHealth();

  return (
    <div className={styles.page}>
      <main className={styles.main}>
        <h1>RideConnect</h1>
        <p className={styles.tagline}>
          Trust-first marketplace connecting riders with verified animal owners.
        </p>
        <div className={styles.status}>
          <span className={styles.statusLabel}>API status:</span>
          {health?.status === "ok" ? (
            <span className={styles.statusOk}>Connected</span>
          ) : (
            <span className={styles.statusError}>
              Unavailable — start the backend with docker compose up
            </span>
          )}
        </div>
      </main>
    </div>
  );
}
