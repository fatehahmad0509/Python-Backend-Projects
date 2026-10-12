import * as Dialog from "@radix-ui/react-dialog";
import { AlertTriangle, Loader2, X } from "lucide-react";

interface ConfirmModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  title: string;
  description: string;
  confirmLabel?: string;
  cancelLabel?: string;
  danger?: boolean;
  isLoading?: boolean;
  onConfirm: () => void;
  children?: React.ReactNode;
}

export default function ConfirmModal({
  open,
  onOpenChange,
  title,
  description,
  confirmLabel = "Confirm",
  cancelLabel = "Cancel",
  danger = false,
  isLoading = false,
  onConfirm,
  children,
}: ConfirmModalProps) {
  return (
    <Dialog.Root open={open} onOpenChange={onOpenChange}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 z-50 bg-black/60 animate-fadeSlideUp" />
        <Dialog.Content className="fixed left-1/2 top-1/2 z-50 w-[92vw] max-w-sm -translate-x-1/2 -translate-y-1/2 rounded-2xl border border-border bg-bg-card p-6 shadow-2xl focus:outline-none">
          <div className="mb-3 flex items-start justify-between gap-3">
            <div className="flex items-center gap-2">
              {danger && (
                <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-danger/10 text-danger">
                  <AlertTriangle className="h-5 w-5" />
                </span>
              )}
              <Dialog.Title className="text-base font-semibold text-text-heading">
                {title}
              </Dialog.Title>
            </div>
            <Dialog.Close
              aria-label="Close"
              className="rounded-lg p-1 text-text-secondary hover:bg-hover hover:text-text-body"
            >
              <X className="h-4 w-4" />
            </Dialog.Close>
          </div>
          <Dialog.Description className="text-sm text-text-secondary">
            {description}
          </Dialog.Description>

          {children && <div className="mt-4">{children}</div>}

          <div className="mt-6 flex justify-end gap-3">
            <Dialog.Close
              className="rounded-xl border border-border px-4 py-2 text-sm font-medium text-text-body hover:bg-hover"
            >
              {cancelLabel}
            </Dialog.Close>
            <button
              type="button"
              disabled={isLoading}
              onClick={onConfirm}
              className={`flex items-center gap-2 rounded-xl px-4 py-2 text-sm font-semibold text-white transition disabled:cursor-not-allowed disabled:opacity-60 ${
                danger ? "bg-danger hover:opacity-90" : "bg-user-gradient hover:opacity-90"
              }`}
            >
              {isLoading && <Loader2 className="h-4 w-4 animate-spin" />}
              {confirmLabel}
            </button>
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
