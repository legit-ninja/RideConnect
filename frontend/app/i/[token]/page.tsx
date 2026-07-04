import type { Metadata } from "next";
import Link from "next/link";

import styles from "@/components/marketplace/marketplace.module.css";
import { InviteRedeemPanel } from "@/components/marketplace/InviteActions";
import type { PublicInvitePreview } from "@/lib/api";
import { buildAuthQuery } from "@/lib/funnel";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function loadInvite(token: string): Promise<PublicInvitePreview> {
  const response = await fetch(`${API_URL}/public/invites/${token}`, {
    next: { revalidate: 30 },
  });
  if (!response.ok) {
    return {
      owner_first_name: "",
      owner_verified: false,
      animal_names: [],
      token_valid: false,
      expired: false,
      revoked: false,
    };
  }
  return (await response.json()) as PublicInvitePreview;
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ token: string }>;
}): Promise<Metadata> {
  const { token } = await params;
  const invite = await loadInvite(token);
  const title = invite.owner_first_name
    ? `Invite from ${invite.owner_first_name} — RideConnect`
    : "Friend invite — RideConnect";
  return {
    title,
    robots: { index: false, follow: false },
  };
}

export default async function InviteLandingPage({
  params,
}: {
  params: Promise<{ token: string }>;
}) {
  const { token } = await params;
  const invite = await loadInvite(token);
  const signupHref = `/register${buildAuthQuery({ src: "invite", ref: token, next: `/i/${token}` })}`;
  const loginHref = `/login${buildAuthQuery({ src: "invite", ref: token, next: `/i/${token}` })}`;

  return (
    <div className={styles.detailPage}>
      <h1>Verified friend invite</h1>

      {!invite.token_valid ? (
        <div className={styles.banner} role="alert">
          {invite.expired
            ? "This invite link has expired."
            : invite.revoked
              ? "This invite link was revoked."
              : "This invite link is not valid."}
        </div>
      ) : (
        <>
          <p>
            <strong>{invite.owner_first_name}</strong>
            {invite.owner_verified ? " (verified owner)" : ""} invited you to connect for
            free-ride eligibility.
          </p>
          {invite.animal_names.length > 0 ? (
            <p>
              Animals: {invite.animal_names.join(", ")}
            </p>
          ) : null}
          <p className={styles.cardMeta}>
            You must complete identity verification before redeeming this invite. The owner
            confirms each redemption for safety.
          </p>
        </>
      )}

      <section className={styles.publicCta}>
        <Link href={signupHref} className={styles.button}>
          Create account to redeem
        </Link>
        <p className={styles.cardMeta}>
          Already verified? <Link href={loginHref}>Sign in</Link>
        </p>
        {invite.token_valid ? <InviteRedeemPanel token={token} /> : null}
      </section>
    </div>
  );
}
