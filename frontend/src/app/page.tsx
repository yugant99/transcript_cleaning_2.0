"use client";

import { BackgroundPaths } from "@/components/ui/background-paths";
import { AnimatedGradientBackground } from "@/components/ui/animated-gradient";
import { Button } from "@/components/ui/button";
import { motion } from "framer-motion";
import { useRouter } from "next/navigation";

export default function Home() {
  const router = useRouter();

  const handleLaunchAnalysis = () => {
    router.push("/dashboard/glossary");
  };

  return (
    <div className="relative min-h-screen w-full flex items-center justify-center overflow-hidden bg-white dark:bg-neutral-950">
      <AnimatedGradientBackground />
      {/* Background Paths */}
      <div className="absolute inset-0">
        <svg
          className="w-full h-full text-slate-950 dark:text-white"
          viewBox="0 0 696 316"
          fill="none"
        >
          <title>Background Paths</title>
          {Array.from({ length: 36 }, (_, i) => ({
            id: i,
            d: `M-${380 - i * 5} -${189 + i * 6}C-${380 - i * 5} -${189 + i * 6} -${312 - i * 5} ${216 - i * 6} ${152 - i * 5} ${343 - i * 6}C${616 - i * 5} ${470 - i * 6} ${684 - i * 5} ${875 - i * 6} ${684 - i * 5} ${875 - i * 6}`,
            color: `rgba(15,23,42,${0.1 + i * 0.03})`,
            width: 0.5 + i * 0.03,
          })).map((path) => (
            <motion.path
              key={path.id}
              d={path.d}
              stroke="currentColor"
              strokeWidth={path.width}
              strokeOpacity={0.1 + path.id * 0.03}
              initial={{ pathLength: 0.3, opacity: 0.6 }}
              animate={{
                pathLength: 1,
                opacity: [0.3, 0.6, 0.3],
                pathOffset: [0, 1, 0],
              }}
              transition={{
                duration: 20 + Math.random() * 10,
                repeat: Number.POSITIVE_INFINITY,
                ease: "linear",
              }}
            />
          ))}
        </svg>
      </div>

      {/* Main Content */}
      <div className="relative z-10 container mx-auto px-4 md:px-6 text-center">
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 2 }}
          className="max-w-6xl mx-auto"
        >
          {/* Title */}
          <motion.h1
            initial={{ opacity: 0, y: 50 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 1, delay: 0.5 }}
            className="text-6xl sm:text-8xl md:text-9xl font-bold mb-8 tracking-tighter leading-tight"
          >
            <span className="inline-block mr-6 last:mr-0">
              {"NLP".split("").map((letter, letterIndex) => (
                <motion.span
                  key={`nlp-${letterIndex}`}
                  initial={{ y: 100, opacity: 0 }}
                  animate={{ y: 0, opacity: 1 }}
                  transition={{
                    delay: letterIndex * 0.1,
                    type: "spring",
                    stiffness: 150,
                    damping: 25,
                  }}
                  className="inline-block text-transparent bg-clip-text
                  bg-gradient-to-r from-blue-600 via-purple-600 to-indigo-700
                  dark:from-blue-400 dark:via-purple-400 dark:to-indigo-500"
                >
                  {letter}
                </motion.span>
              ))}
            </span>
            <span className="inline-block mr-6 last:mr-0">
              {"Analysis".split("").map((letter, letterIndex) => (
                <motion.span
                  key={`analysis-${letterIndex}`}
                  initial={{ y: 100, opacity: 0 }}
                  animate={{ y: 0, opacity: 1 }}
                  transition={{
                    delay: 0.3 + letterIndex * 0.05,
                    type: "spring",
                    stiffness: 150,
                    damping: 25,
                  }}
                  className="inline-block text-transparent bg-clip-text
                  bg-gradient-to-r from-neutral-900 to-neutral-700/80
                  dark:from-white dark:to-white/80"
                >
                  {letter}
                </motion.span>
              ))}
            </span>
          </motion.h1>

          {/* Subtitle */}
          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 1, delay: 1.2 }}
            className="text-xl sm:text-2xl md:text-3xl text-neutral-600 dark:text-neutral-300 mb-12 max-w-4xl mx-auto leading-relaxed"
          >
            Advanced transcript analysis powered by AI.
            <br />
            <span className="text-lg sm:text-xl text-neutral-500 dark:text-neutral-400">
              Discover insights, patterns, and meaning from conversational data.
            </span>
          </motion.p>

          {/* Feature highlights */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 1, delay: 1.5 }}
            className="flex flex-wrap justify-center gap-6 mb-12 text-sm sm:text-base text-neutral-500 dark:text-neutral-400"
          >
            <span className="flex items-center gap-2">
              <div className="w-2 h-2 bg-green-500 rounded-full"></div>
              Semantic Search
            </span>
            <span className="flex items-center gap-2">
              <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
              Sentiment Analysis
            </span>
            <span className="flex items-center gap-2">
              <div className="w-2 h-2 bg-purple-500 rounded-full"></div>
              Pattern Recognition
            </span>
            <span className="flex items-center gap-2">
              <div className="w-2 h-2 bg-orange-500 rounded-full"></div>
              Real-time Insights
            </span>
          </motion.div>

          {/* CTA Button */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 1, delay: 1.8 }}
            className="inline-block group relative bg-gradient-to-b from-black/10 to-white/10
            dark:from-white/10 dark:to-black/10 p-px rounded-2xl backdrop-blur-lg
            overflow-hidden shadow-lg hover:shadow-xl transition-shadow duration-300"
          >
            <Button
              onClick={handleLaunchAnalysis}
              className="rounded-[1.15rem] px-8 py-6 text-lg font-semibold backdrop-blur-md
              bg-white/95 hover:bg-white/100 dark:bg-black/95 dark:hover:bg-black/100
              text-black dark:text-white transition-all duration-300
              group-hover:-translate-y-0.5 border border-black/10 dark:border-white/10
              hover:shadow-md dark:hover:shadow-neutral-800/50"
            >
              <span className="opacity-90 group-hover:opacity-100 transition-opacity">
                Launch Analysis
              </span>
              <motion.span
                className="ml-3 opacity-70 group-hover:opacity-100 group-hover:translate-x-1.5
                transition-all duration-300"
                initial={{ x: 0 }}
                whileHover={{ x: 4 }}
              >
                →
              </motion.span>
            </Button>
          </motion.div>

          {/* Footer */}
          <motion.footer
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 1, delay: 2.2 }}
            className="mt-16 text-sm text-neutral-500 dark:text-neutral-400"
          >
            <p>Powered by advanced AI • Built for research excellence</p>
          </motion.footer>
        </motion.div>
      </div>
    </div>
  );
}
