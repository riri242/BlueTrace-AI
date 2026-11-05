import { motion } from "framer-motion";
import { Link } from "react-router-dom";

import { HeroIllustration } from "@/assets/HeroIllustration";
import { buttonStyles } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";

const foundationItems = [
  "Observation intake",
  "Coastal location capture",
  "Experimental drift tracing"
];

export function LandingPage() {
  return (
    <div className="overflow-hidden">
      <section className="mx-auto grid min-h-[78vh] max-w-7xl items-center gap-12 px-5 py-16 sm:px-8 lg:grid-cols-[1fr_0.9fr] lg:py-20">
        <motion.div
          animate={{ opacity: 1, y: 0 }}
          className="max-w-3xl"
          initial={{ opacity: 0, y: 18 }}
          transition={{ duration: 0.55, ease: "easeOut" }}
        >
          <p className="mb-5 text-sm font-semibold uppercase tracking-[0.24em] text-ocean-600">
            CALIFORNIA COAST · EXPERIMENTAL MARINE RESEARCH
          </p>
          <h1 className="text-5xl font-semibold tracking-tight text-research-ink sm:text-6xl lg:text-7xl dark:text-white">
            Trace the <span className="bg-gradient-to-r from-ocean-600 to-cyan-400 bg-clip-text text-transparent dark:from-cyan-300 dark:to-blue-400">unseen.</span>
          </h1>
          <p className="mt-6 max-w-2xl text-xl leading-8 text-research-muted">
            BlueTrace AI brings computer vision, ocean conditions, and experimental drift analysis together to explore the story behind marine debris along California’s coast.
          </p>
          <div className="mt-9">
            <Link className={buttonStyles({ size: "lg" })} to="/analysis">
              Explore the Coast →
            </Link>
          </div>
        </motion.div>

        <motion.div
          animate={{ opacity: 1, scale: 1 }}
          className="mx-auto w-full max-w-xl"
          initial={{ opacity: 0, scale: 0.96 }}
          transition={{ delay: 0.12, duration: 0.6, ease: "easeOut" }}
        >
          <HeroIllustration />
        </motion.div>
      </section>

      <section className="border-y border-research-line bg-white/72 dark:border-white/10 dark:bg-slate-950/40">
        <div className="mx-auto grid max-w-7xl gap-4 px-5 py-8 sm:px-8 md:grid-cols-3">
          {foundationItems.map((item) => (
            <Card className="p-5 shadow-none transition-transform hover:-translate-y-1" key={item} tone="soft">
              <p className="text-sm font-semibold text-research-ink">{item}</p>
            </Card>
          ))}
        </div>
      </section>
    </div>
  );
}

