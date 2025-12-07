"use client";

import React, { useEffect, useRef } from "react";
import { FaExclamationTriangle } from "react-icons/fa";

export interface ConfirmDialogProps {
  isOpen: boolean;
  title: string;
  message: string;
  confirmText?: string;
  cancelText?: string;
  onConfirm: () => void;
  onCancel: () => void;
}

const ConfirmDialog: React.FC<ConfirmDialogProps> = ({
  isOpen,
  title,
  message,
  confirmText = "OK",
  cancelText = "Отмена",
  onConfirm,
  onCancel,
}) => {
  const cancelButtonRef = useRef<HTMLButtonElement>(null);
  const confirmButtonRef = useRef<HTMLButtonElement>(null);
  const previousActiveElementRef = useRef<HTMLElement | null>(null);

  // Auto-focus and restore focus on close
  useEffect(() => {
    if (isOpen) {
      // Save currently focused element
      previousActiveElementRef.current = document.activeElement as HTMLElement;
      // Focus cancel button on open
      cancelButtonRef.current?.focus();
    } else {
      // Restore focus on close
      previousActiveElementRef.current?.focus();
    }
  }, [isOpen]);

  // Handle keyboard events (ESC, Enter, Tab for focus trap)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (!isOpen) return;

      if (e.key === "Escape") {
        onCancel();
      } else if (e.key === "Enter") {
        onConfirm();
      } else if (e.key === "Tab") {
        // Focus trap: toggle between cancel and confirm buttons
        e.preventDefault();
        if (document.activeElement === cancelButtonRef.current) {
          confirmButtonRef.current?.focus();
        } else {
          cancelButtonRef.current?.focus();
        }
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, onCancel, onConfirm]);

  if (!isOpen) return null;

  const handleBackdropClick = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget) {
      onCancel();
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fadeIn"
      onClick={handleBackdropClick}
      role="alertdialog"
      aria-modal="true"
      aria-labelledby="confirm-title"
      aria-describedby="confirm-message"
    >
      <div className="relative w-full max-w-sm bg-gradient-to-b from-[#1E1B3A] to-[#130F30] rounded-2xl border border-white/10 shadow-2xl animate-slideUp">
        {/* Icon */}
        <div className="flex justify-center pt-6">
          <div className="w-16 h-16 flex items-center justify-center bg-yellow-500/10 rounded-full border border-yellow-500/20">
            <FaExclamationTriangle className="text-yellow-400 text-2xl" />
          </div>
        </div>

        {/* Content */}
        <div className="px-6 py-4 text-center">
          <h2 id="confirm-title" className="text-xl font-bold text-white mb-3">
            {title}
          </h2>
          <p id="confirm-message" className="text-gray-300 text-sm leading-relaxed">
            {message}
          </p>
        </div>

        {/* Buttons */}
        <div className="px-6 pb-6 flex gap-3">
          <button
            ref={cancelButtonRef}
            onClick={onCancel}
            className="flex-1 px-4 py-3 bg-white/10 text-gray-300 font-medium rounded-lg hover:bg-white/20 transition-all border border-white/10"
          >
            {cancelText}
          </button>
          <button
            ref={confirmButtonRef}
            onClick={onConfirm}
            className="flex-1 px-4 py-3 bg-gradient-to-r from-[#8B23CB] to-[#A020F0] text-white font-medium rounded-lg hover:opacity-90 transition-all shadow-lg shadow-[#8B23CB]/20"
          >
            {confirmText}
          </button>
        </div>
      </div>
    </div>
  );
};

export default ConfirmDialog;
