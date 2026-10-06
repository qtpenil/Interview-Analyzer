import type { Metadata } from "next";
import Navbar from "@/components/landing/Navbar";
import ScrollToTop from "@/components/landing/ScrollToTop";
import Hero from "@/components/landing/Hero";
import TrustBar from "@/components/landing/TrustBar";
import Problem from "@/components/landing/Problem";
import Features from "@/components/landing/Features";
import Workflow from "@/components/landing/Workflow";
import DashboardPreview from "@/components/landing/DashboardPreview";
import Reports from "@/components/landing/Reports";
import WhyChooseUs from "@/components/landing/WhyChooseUs";
import FAQ from "@/components/landing/FAQ";
import CTA from "@/components/landing/CTA";
import Footer from "@/components/landing/Footer";

const SITE_URL = "https://interview-ai.app";

export const metadata: Metadata = {
  metadataBase: new URL(SITE_URL),
  title: "InteReview — Turn Every Interview Into Actionable Insights",
  description:
    "Upload interview recordings and get AI-powered transcripts, question analysis, communication insights, topic breakdowns, and professional PDF reports in minutes.",
  keywords: [
    "AI interview analysis",
    "interview transcription",
    "candidate assessment",
    "hiring insights",
    "interview report",
  ],
  openGraph: {
    title: "InteReview — Turn Every Interview Into Actionable Insights",
    description:
      "AI-powered transcripts, scoring, and professional reports for every interview.",
    url: SITE_URL,
    siteName: "InteReview",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "InteReview — Turn Every Interview Into Actionable Insights",
    description:
      "AI-powered transcripts, scoring, and professional reports for every interview.",
  },
};

export default function LandingPage() {
  return (
    <>
      <Navbar />
      <ScrollToTop />
      <main className="pt-16">
        <Hero />
        <TrustBar />
        <Problem />
        <Features />
        <Workflow />
        <DashboardPreview />
        <Reports />
        <WhyChooseUs />
        <FAQ />
        <CTA />
      </main>
      <Footer />
    </>
  );
}
