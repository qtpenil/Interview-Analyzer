import type { Metadata } from "next";
import { cookies } from "next/headers";
import { Geist, Geist_Mono } from "next/font/google";
import Sidebar from "@/components/common/Sidebar";
import { UploadProvider } from "@/context/UploadContext";
import { AuthProvider } from "@/context/AuthContext";
import { ThemeProvider, themeInitScript } from "@/providers/ThemeProvider";
import { DEFAULT_THEME, THEME_COOKIE_KEY } from "@/styles/theme";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "InteReview",
  description: "Upload and analyze candidate interview video transcripts automatically.",
};

export default async function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  // Read the user's theme from the cookie so the server-rendered HTML
  // matches what the client will render after hydration (no flash,
  // no hydration mismatch).
  const cookieStore = await cookies();
  const storedTheme = cookieStore.get(THEME_COOKIE_KEY)?.value;
  const initialTheme =
    storedTheme === "dark" || storedTheme === "light"
      ? storedTheme
      : DEFAULT_THEME;

  return (
    <html
      lang="en"
      suppressHydrationWarning
      data-theme={initialTheme}
      className={`${geistSans.variable} ${geistMono.variable} ${
        initialTheme === "dark" ? "theme-dark" : "theme-light"
      } h-full antialiased`}
    >
      <head>
        <script dangerouslySetInnerHTML={{ __html: themeInitScript }} />
      </head>
      <body className="min-h-screen flex flex-col md:flex-row w-full bg-background text-primary">
        <ThemeProvider initialTheme={initialTheme}>
          <AuthProvider>
            <UploadProvider>
              <Sidebar />
              <div className="flex-1 flex flex-col min-h-screen min-w-0 overflow-y-auto relative">
                {/* Ambient decorative background — theme aware, sits behind content */}
                <div className="pointer-events-none fixed inset-0 -z-10 overflow-hidden">
                  {/* Radial base wash */}
                  <div className="absolute inset-0" style={{ background: "var(--gradient-radial)" }} />

                  {/* Soft mesh gradient layer */}
                  <div
                    className="absolute inset-0 opacity-[0.5]"
                    style={{
                      background:
                        "radial-gradient(40% 35% at 15% 20%, var(--accent-soft) 0%, transparent 70%), radial-gradient(45% 40% at 85% 15%, var(--accent-soft) 0%, transparent 70%), radial-gradient(50% 45% at 75% 90%, var(--accent-soft) 0%, transparent 70%)",
                    }}
                  />

                  {/* Large blurred gradient circles — gently pulsing */}
                  <div
                    className="absolute -top-40 -left-24 w-[36rem] h-[36rem] rounded-full blur-[140px] opacity-[0.13] animate-[auth-float_9s_ease-in-out_infinite]"
                    style={{ background: "var(--gradient-start)" }}
                  />
                  <div
                    className="absolute top-1/3 -right-32 w-[34rem] h-[34rem] rounded-full blur-[140px] opacity-[0.11] animate-[auth-float_11s_ease-in-out_infinite]"
                    style={{ background: "var(--gradient-end)" }}
                  />
                  <div
                    className="absolute -bottom-48 left-1/3 w-[40rem] h-[40rem] rounded-full blur-[150px] opacity-[0.09] animate-[auth-float_13s_ease-in-out_infinite]"
                    style={{ background: "var(--accent)" }}
                  />

                  {/* Floating accent ring shape */}
                  <div
                    className="absolute right-[12%] top-[18%] h-72 w-72 rounded-full border border-accent-soft-border opacity-[0.18] animate-[auth-float_10s_ease-in-out_infinite]"
                    aria-hidden="true"
                  />
                  {/* Rotating dashed ring */}
                  <div
                    className="absolute left-[6%] bottom-[14%] h-56 w-56 rounded-full border border-dashed border-accent-soft-border opacity-[0.16] animate-[spin_28s_linear_infinite]"
                    aria-hidden="true"
                  />

                  {/* Faint animated scan lines for texture */}
                  <div
                    className="absolute inset-0 opacity-[0.05] animate-[auth-grid-pan_8s_linear_infinite]"
                    style={{
                      backgroundImage:
                        "repeating-linear-gradient(0deg, var(--gradient-end) 0px, transparent 1px, transparent 3px, var(--gradient-end) 4px)",
                    }}
                  />

                  {/* Floating mesh grid */}
                  <div
                    className="absolute inset-0 opacity-[0.04] animate-[auth-grid-pan_16s_linear_infinite]"
                    style={{
                      backgroundImage:
                        "linear-gradient(var(--gradient-end) 1px, transparent 1px), linear-gradient(90deg, var(--gradient-end) 1px, transparent 1px)",
                      backgroundSize: "44px 44px",
                    }}
                  />

                  {/* Subtle dot grid pattern */}
                  <div
                    className="absolute inset-0 opacity-[0.04]"
                    style={{
                      backgroundImage:
                        "radial-gradient(var(--text-primary) 1px, transparent 1px)",
                      backgroundSize: "28px 28px",
                    }}
                  />
                </div>
                {children}
              </div>
            </UploadProvider>
          </AuthProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}