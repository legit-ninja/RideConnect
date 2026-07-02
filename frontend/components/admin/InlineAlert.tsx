import { ReactNode } from "react";

import styles from "./admin.module.css";

type AlertVariant = "error" | "success" | "info" | "warning";

const VARIANT_CLASS: Record<AlertVariant, string> = {
  error: styles.alertError,
  success: styles.alertSuccess,
  info: styles.alertInfo,
  warning: styles.alertWarning,
};

interface InlineAlertProps {
  variant: AlertVariant;
  children: ReactNode;
  live?: "polite" | "assertive";
}

export function InlineAlert({
  variant,
  children,
  live = "polite",
}: InlineAlertProps) {
  return (
    <div
      className={`${styles.alert} ${VARIANT_CLASS[variant]}`}
      role="alert"
      aria-live={live}
    >
      {children}
    </div>
  );
}
