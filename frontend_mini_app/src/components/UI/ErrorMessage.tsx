import React from "react";

interface ErrorMessageProps {
  message: string;
}

const ErrorMessage: React.FC<ErrorMessageProps> = ({ message }) => (
  <div className="p-3 bg-red-500/20 border border-red-500/40 rounded-lg">
    <p className="text-red-300">{message}</p>
  </div>
);

export default ErrorMessage;
