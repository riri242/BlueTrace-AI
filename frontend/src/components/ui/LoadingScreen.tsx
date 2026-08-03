import { motion } from "framer-motion";

interface LoadingScreenProps {
  message?: string;
}

export function LoadingScreen({
  message = "Preparing analysis..."
}: LoadingScreenProps) {
  return (
    <motion.div
      animate={{ opacity: 1 }}
      aria-live="polite"
      className="fixed inset-0 z-50 flex items-center justify-center bg-white/88 px-6 backdrop-blur-md"
      initial={{ opacity: 0 }}
      role="status"
    >
      <div className="flex flex-col items-center gap-6 text-center">
        <div className="relative h-24 w-24">
          <motion.div
            animate={{ rotate: 360 }}
            className="absolute inset-0 rounded-full border border-ocean-100"
            transition={{ duration: 6, ease: "linear", repeat: Infinity }}
          />
          <motion.div
            animate={{ rotate: -360 }}
            className="absolute inset-3 rounded-full border-2 border-transparent border-t-ocean-600 border-r-cyan-400"
            transition={{ duration: 1.5, ease: "linear", repeat: Infinity }}
          />
          <motion.div
            animate={{ scale: [0.88, 1, 0.88], opacity: [0.72, 1, 0.72] }}
            className="absolute inset-8 rounded-full bg-ocean-600"
            transition={{ duration: 1.6, repeat: Infinity }}
          />
        </div>
        <p className="text-lg font-semibold text-research-ink">{message}</p>
      </div>
    </motion.div>
  );
}

