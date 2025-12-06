"use client";

import { useEffect, useState } from "react";
import { FaCheckCircle, FaExclamationTriangle, FaTimes, FaInfoCircle } from "react-icons/fa";

export type AlertType = "success" | "error" | "warning" | "info";

interface CustomAlertProps {
  message: string;
  type?: AlertType;
  duration?: number;
  onClose?: () => void;
  show?: boolean;
}

const CustomAlert: React.FC<CustomAlertProps> = ({
  message,
  type = "info",
  duration = 5000,
  onClose,
  show = true,
}) => {
  const [isVisible, setIsVisible] = useState(show);
  const [isExiting, setIsExiting] = useState(false);

  const icons = {
    success: <FaCheckCircle className="text-xl" />,
    error: <FaExclamationTriangle className="text-xl" />,
    warning: <FaExclamationTriangle className="text-xl" />,
    info: <FaInfoCircle className="text-xl" />,
  };

  const colors = {
    success: {
      bg: "bg-gradient-to-r from-[#8B23CB]/20 to-[#A020F0]/20",
      border: "border-[#8B23CB]/40",
      text: "text-[#d0a8ff]",
      icon: "text-[#b57aff]",
      progress: "from-[#8B23CB] to-[#A020F0]",
    },
    error: {
      bg: "bg-gradient-to-r from-[#FF416C]/20 to-[#FF4B2B]/20",
      border: "border-[#FF416C]/40",
      text: "text-[#ffa8c1]",
      icon: "text-[#ff7a9d]",
      progress: "from-[#FF416C] to-[#FF4B2B]",
    },
    warning: {
      bg: "bg-gradient-to-r from-[#FF9A3D]/20 to-[#FFB347]/20",
      border: "border-[#FF9A3D]/40",
      text: "text-[#ffd9b3]",
      icon: "text-[#ffc285]",
      progress: "from-[#FF9A3D] to-[#FFB347]",
    },
    info: {
      bg: "bg-gradient-to-r from-[#7B6F9C]/20 to-[#8B23CB]/20",
      border: "border-[#7B6F9C]/40",
      text: "text-[#d0a8ff]",
      icon: "text-[#b57aff]",
      progress: "from-[#7B6F9C] to-[#8B23CB]",
    },
  };

  const handleClose = () => {
    setIsExiting(true);
    setTimeout(() => {
      setIsVisible(false);
      onClose?.();
    }, 300);
  };

  useEffect(() => {
    if (duration > 0 && isVisible && !isExiting) {
      const timer = setTimeout(() => {
        handleClose();
      }, duration);

      return () => clearTimeout(timer);
    }
  }, [duration, isVisible, isExiting]);

  useEffect(() => {
    if (show && !isVisible) {
      setIsVisible(true);
      setIsExiting(false);
    } else if (!show && isVisible) {
      handleClose();
    }
  }, [show]);

  if (!isVisible) return null;

  return (
    <div className="fixed top-4 right-4 z-[9999] flex items-start justify-end p-4 pointer-events-none">
      <div className={`
        ${colors[type].bg} 
        ${colors[type].border}
        border backdrop-blur-xl 
        rounded-xl p-4 max-w-md w-full 
        transform transition-all duration-300 ease-in-out
        ${isExiting ? 'translate-x-[20px] opacity-0' : 'translate-x-0 opacity-100'}
        pointer-events-auto
        shadow-2xl shadow-black/30
        min-w-[320px]
      `}>
        <div className="flex items-start gap-3">
          <div className={`${colors[type].icon} flex-shrink-0 mt-0.5`}>
            {icons[type]}
          </div>
          
          <div className="flex-1 min-w-0">
            <p className={`${colors[type].text} font-medium text-sm leading-relaxed whitespace-pre-line`}>
              {message}
            </p>
          </div>
          
          <button
            onClick={handleClose}
            className={`
              flex-shrink-0 
              ${colors[type].text}
              hover:opacity-80 
              transition-opacity 
              p-1 rounded-lg
              hover:bg-white/10
              ml-2
            `}
            aria-label="Закрыть"
          >
            <FaTimes className="text-sm" />
          </button>
        </div>

        {duration > 0 && (
          <div className="mt-3 h-1 bg-white/10 rounded-full overflow-hidden">
            <div 
              className={`h-full rounded-full bg-gradient-to-r ${colors[type].progress}`}
              style={{
                animation: `shrink ${duration}ms linear forwards`,
                animationPlayState: isExiting ? 'paused' : 'running'
              }}
            />
          </div>
        )}
      </div>
    </div>
  );
};

export function useAlert() {
  const [alertState, setAlertState] = useState<{
    show: boolean;
    message: string;
    type: AlertType;
    duration?: number;
  }>({
    show: false,
    message: "",
    type: "info",
  });

  const showAlert = (
    message: string, 
    type: AlertType = "info", 
    duration: number = 5000
  ) => {
    setAlertState({
      show: true,
      message,
      type,
      duration,
    });
  };

  const hideAlert = () => {
    setAlertState(prev => ({ ...prev, show: false }));
  };

  const AlertComponent = () => (
    <CustomAlert
      message={alertState.message}
      type={alertState.type}
      duration={alertState.duration}
      show={alertState.show}
      onClose={hideAlert}
    />
  );

  return {
    showAlert,
    hideAlert,
    AlertComponent,
  };
}

export const alertService = {
  success: (message: string, duration?: number) => ({
    show: true,
    message,
    type: "success" as AlertType,
    duration,
  }),
  error: (message: string, duration?: number) => ({
    show: true,
    message,
    type: "error" as AlertType,
    duration,
  }),
  warning: (message: string, duration?: number) => ({
    show: true,
    message,
    type: "warning" as AlertType,
    duration,
  }),
  info: (message: string, duration?: number) => ({
    show: true,
    message,
    type: "info" as AlertType,
    duration,
  }),
};

export default CustomAlert;