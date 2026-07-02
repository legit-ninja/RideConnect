"use client";

import { useEffect, useRef } from "react";

import styles from "./marketplace.module.css";

interface ConfirmDialogProps {
  open: boolean;
  title: string;
  description: string;
  confirmLabel: string;
  cancelLabel?: string;
  destructive?: boolean;
  onConfirm: () => void;
  onCancel: () => void;
}

export function ConfirmDialog({
  open,
  title,
  description,
  confirmLabel,
  cancelLabel = "Cancel",
  destructive = false,
  onConfirm,
  onCancel,
}: ConfirmDialogProps) {
  const cancelRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    if (!open) return;
    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") onCancel();
    }
    document.addEventListener("keydown", handleKeyDown);
    cancelRef.current?.focus();
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [open, onCancel]);

  if (!open) return null;

  return (
    <div className={styles.dialogBackdrop} role="presentation" onClick={onCancel}>
      <div
        className={styles.dialog}
        role="alertdialog"
        aria-modal="true"
        aria-labelledby="mkt-confirm-title"
        aria-describedby="mkt-confirm-desc"
        onClick={(e) => e.stopPropagation()}
      >
        <h2 id="mkt-confirm-title" className={styles.dialogTitle}>
          {title}
        </h2>
        <p id="mkt-confirm-desc" className={styles.dialogBody}>
          {description}
        </p>
        <div className={styles.dialogActions}>
          <button
            ref={cancelRef}
            type="button"
            className={`${styles.button} ${styles.buttonSecondary}`}
            onClick={onCancel}
          >
            {cancelLabel}
          </button>
          <button
            type="button"
            className={
              destructive
                ? `${styles.button} ${styles.buttonDanger}`
                : styles.button
            }
            onClick={onConfirm}
          >
            {confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
}
