import { motion } from "framer-motion";
import { Link } from "react-router-dom";

import { HeroIllustration } from "@/assets/HeroIllustration";
import { buttonStyles } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";

const foundationItems = [
  "Observation intake",
  "Coastal location capture",
  "Validated research metadata"
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
            Academic coastal intelligence
          </p>
          <h1 className="text-5xl font-semibold tracking-tight text-research-ink sm:text-6xl lg:text-7xl">
            BlueTrace AI
          </h1>
          <p className="mt-6 max-w-2xl text-xl leading-8 text-research-muted">
            AI-powered marine debris origin estimation and coastal intelligence.
          </p>
          <div className="mt-9">
            <Link className={buttonStyles({ size: "lg" })} to="/analysis">
              Start Analysis
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

      <section className="border-y border-research-line bg-white/72">
        <div className="mx-auto grid max-w-7xl gap-4 px-5 py-8 sm:px-8 md:grid-cols-3">
          {foundationItems.map((item) => (
            <Card className="p-5 shadow-none" key={item} tone="soft">
              <p className="text-sm font-semibold text-research-ink">{item}</p>
            </Card>
          ))}
        </div>
      </section>
    </div>
  );
}

