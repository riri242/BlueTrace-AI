import { lazy, Suspense } from "react";
import { Navigate, Route, Routes } from "react-router-dom";

import { AppLayout } from "@/layouts/AppLayout";

const AnalysisPage = lazy(() =>
  import("@/pages/AnalysisPage").then((module) => ({
    default: module.AnalysisPage
  }))
);
const LandingPage = lazy(() =>
  import("@/pages/LandingPage").then((module) => ({
    default: module.LandingPage
  }))
);

function RouteFallback() {
  return (
    <div className="flex min-h-[70vh] items-center justify-center px-6">
      <div className="h-12 w-12 animate-spin rounded-full border-2 border-ocean-100 border-t-ocean-600" />
    </div>
  );
}

export function App() {
  return (
    <AppLayout>
      <Suspense fallback={<RouteFallback />}>
        <Routes>
          <Route element={<LandingPage />} path="/" />
          <Route element={<AnalysisPage />} path="/analysis" />
          <Route element={<Navigate replace to="/" />} path="*" />
        </Routes>
      </Suspense>
    </AppLayout>
  );
}
