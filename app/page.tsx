import Link from "next/link"
import Image from "next/image"
import { Button } from "@/components/ui/button"
import { Download, Monitor, Camera, Maximize, Layout, ImageIcon, Zap, MessageSquare, RefreshCw } from "lucide-react"
import FeedbackForm from "@/components/feedback-form"
import FeatureCard from "@/components/feature-card"
import FaqSection from "@/components/faq-section"
import ChangelogSection from "@/components/changelog-section"
import ScreenshotGallery from "./images"
import { getGitHubReleases } from "@/lib/github"

export default async function Home() {
  // Get releases from GitHub or fallback data
  const releases = await getGitHubReleases()

  // Get the latest release with assets (for the installer)
  const latestRelease = releases.find((release) => release.assets.length > 0) || releases[0]

  // Find the installer asset (.exe file)
  const installerAsset = latestRelease?.assets.find(
    (asset) => asset.name.endsWith(".exe") || asset.name.includes("Setup"),
  )

  // URLs for the download buttons - using fallback "#" if not available
  const installerUrl = installerAsset?.download_url || "#"

  // Replace with your actual GitHub repository URL
  const githubReleasesUrl = "https://github.com/KezLahd/Screen-Split/releases"

  // Get download count for display
  const totalDownloads = releases.reduce((total, release) => {
    return total + release.assets.reduce((releaseTotal, asset) => releaseTotal + asset.download_count, 0)
  }, 0)

  return (
    <div className="min-h-screen bg-zinc-900 text-zinc-100">
      {/* Header */}
      <header className="sticky top-0 z-50 w-full border-b border-zinc-800 bg-zinc-900/95 backdrop-blur supports-[backdrop-filter]:bg-zinc-900/75">
        <div className="container flex h-16 items-center justify-between">
          <div className="flex items-center gap-2">
            <Layout className="h-6 w-6 text-blue-500" />
            <span className="text-xl font-bold">Screen Split</span>
            <span className="rounded-full bg-blue-500 px-2 py-0.5 text-xs font-medium text-white">BETA</span>
          </div>
          <nav className="hidden md:flex items-center gap-6">
            <Link href="#features" className="text-sm font-medium text-zinc-400 hover:text-zinc-100">
              Features
            </Link>
            <Link href="#feedback" className="text-sm font-medium text-zinc-400 hover:text-zinc-100">
              Feedback
            </Link>
            <Link href="#faq" className="text-sm font-medium text-zinc-400 hover:text-zinc-100">
              FAQ
            </Link>
            <Link href="#updates" className="text-sm font-medium text-zinc-400 hover:text-zinc-100">
              Updates
            </Link>
          </nav>
          <Button asChild variant="default" className="bg-blue-500 hover:bg-blue-600 text-white">
            <Link href="#download">
              <Download className="mr-2 h-4 w-4" />
              Download Beta
            </Link>
          </Button>
        </div>
      </header>

      <main>
        {/* Hero Section */}
        <section className="py-20 md:py-32 relative overflow-hidden">
          <div className="absolute inset-0 bg-gradient-to-br from-blue-500/10 to-transparent" />
          <div className="container relative z-10">
            <div className="grid gap-8 md:grid-cols-2 items-center">
              <div className="space-y-6">
                <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold tracking-tight bg-gradient-to-r from-white to-blue-400 text-transparent bg-clip-text">
                  Create cleaner content – with screen & self side-by-side
                </h1>
                <p className="text-xl text-zinc-400 max-w-lg">
                  The perfect tool for streamers, educators, and presenters who want to show both their screen and face
                  in one clean window.
                </p>
                <div className="flex flex-col sm:flex-row gap-4" id="download">
                  <Button size="lg" asChild className="bg-blue-500 hover:bg-blue-600 text-white">
                    <a href={installerUrl} download>
                      <Download className="mr-2 h-5 w-5" />
                      Download v{latestRelease?.version}
                      {totalDownloads > 0 && (
                        <span className="ml-2 text-xs bg-blue-600 px-2 py-0.5 rounded-full">
                          {totalDownloads.toLocaleString()} downloads
                        </span>
                      )}
                    </a>
                  </Button>
                  <Button size="lg" variant="outline" asChild className="border-zinc-700 hover:bg-zinc-800 text-white">
                    <a href={githubReleasesUrl} target="_blank" rel="noopener noreferrer">
                      <RefreshCw className="mr-2 h-5 w-5" />
                      Check for Updates
                    </a>
                  </Button>
                </div>
              </div>
              <div className="relative rounded-lg border border-zinc-800 bg-zinc-950 p-2 shadow-xl">
                <Image
                  src="/images/screen-split-demo.png"
                  width={800}
                  height={600}
                  alt="Screen Split Preview"
                  className="rounded w-full h-auto"
                  priority
                />
                <div className="absolute bottom-4 left-4 right-4 bg-black/80 backdrop-blur-sm rounded p-3 text-sm">
                  <p className="font-medium text-white">Preview: Screen Split in action</p>
                  <p className="text-zinc-400 text-xs">Replace with actual app screenshot or demo GIF</p>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Features Section */}
        <section id="features" className="py-20 bg-zinc-950">
          <div className="container">
            <div className="text-center mb-16">
              <h2 className="text-3xl md:text-4xl font-bold mb-4 bg-gradient-to-r from-white to-blue-400 text-transparent bg-clip-text">
                Powerful Features
              </h2>
              <p className="text-white max-w-2xl mx-auto">
                Screen Split gives you everything you need to create professional-looking content with both your screen
                and webcam.
              </p>
            </div>

            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
              <FeatureCard
                icon={<Layout />}
                title="Side-by-Side Display"
                description="View your screen capture and webcam feed simultaneously in a single, adjustable window."
              />
              <FeatureCard
                icon={<Monitor />}
                title="Multi-Monitor Support"
                description="Capture from any connected display while maintaining high-quality output."
              />
              <FeatureCard
                icon={<Maximize />}
                title="Resizable Interface"
                description="Drag to resize both screen and webcam areas to create your perfect layout."
              />
              <FeatureCard
                icon={<Camera />}
                title="Webcam Zoom"
                description="Adjust your webcam zoom level to focus on what matters most."
              />
              <FeatureCard
                icon={<ImageIcon />}
                title="Logo Overlay"
                description="Add your personal or brand logo to create a more professional look."
              />
              <FeatureCard
                icon={<Zap />}
                title="Lag-Free Capture"
                description="Enjoy smooth 30fps screen capture with minimal system resource usage."
              />
            </div>
          </div>
        </section>

        {/* Screenshot Gallery section */}
        <ScreenshotGallery />

        {/* Feedback Section */}
        <section id="feedback" className="py-20 bg-zinc-900">
          <div className="container">
            <div className="text-center mb-16">
              <h2 className="text-3xl md:text-4xl font-bold mb-4 bg-gradient-to-r from-white to-blue-400 text-transparent bg-clip-text">
                Help Us Improve
              </h2>
              <p className="text-zinc-400 max-w-2xl mx-auto">
                This is a beta release. Your feedback is invaluable in helping us refine Screen Split.
              </p>
            </div>

            <div className="max-w-2xl mx-auto">
              <FeedbackForm />
            </div>
          </div>
        </section>

        {/* FAQ Section */}
        <section id="faq" className="py-20 bg-zinc-950">
          <div className="container">
            <div className="text-center mb-16">
              <h2 className="text-3xl md:text-4xl font-bold mb-4 bg-gradient-to-r from-white to-blue-400 text-transparent bg-clip-text">
                Frequently Asked Questions
              </h2>
              <p className="text-zinc-400 max-w-2xl mx-auto">Get answers to common questions about Screen Split.</p>
            </div>

            <div className="max-w-3xl mx-auto">
              <FaqSection />
            </div>
          </div>
        </section>

        {/* Updates Section */}
        <section id="updates" className="py-20 bg-zinc-900">
          <div className="container">
            <div className="text-center mb-16">
              <h2 className="text-3xl md:text-4xl font-bold mb-4 bg-gradient-to-r from-white to-blue-400 text-transparent bg-clip-text">
                Updates & Changelog
              </h2>
              <p className="text-zinc-400 max-w-2xl mx-auto">Stay up to date with the latest improvements and fixes.</p>
            </div>

            <div className="max-w-3xl mx-auto">
              <ChangelogSection />
            </div>
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer className="py-12 border-t border-zinc-800 bg-zinc-950">
        <div className="container">
          <div className="flex flex-col md:flex-row justify-between items-center">
            <div className="flex items-center gap-2 mb-6 md:mb-0">
              <Layout className="h-6 w-6 text-blue-500" />
              <span className="text-xl font-bold">Screen Split</span>
              <span className="rounded-full bg-blue-500 px-2 py-0.5 text-xs font-medium text-white">BETA</span>
            </div>

            <div className="flex flex-col items-center md:items-end">
              <div className="flex items-center gap-4 mb-4">
                <Link href="mailto:contact@screensplit.com" className="text-zinc-400 hover:text-zinc-100">
                  <MessageSquare className="h-5 w-5" />
                  <span className="sr-only">Email</span>
                </Link>
                <a
                  href={githubReleasesUrl}
                  className="text-zinc-400 hover:text-zinc-100"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  <svg viewBox="0 0 24 24" className="h-5 w-5" fill="currentColor">
                    <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z" />
                  </svg>
                  <span className="sr-only">GitHub</span>
                </a>
              </div>
              <p className="text-zinc-500 text-sm text-center md:text-right">
                &copy; {new Date().getFullYear()} Screen Split. All rights reserved.
                <br />
                <span className="text-xs">Beta software. Use at your own risk. Not for commercial use.</span>
              </p>
            </div>
          </div>
        </div>
      </footer>
    </div>
  )
}
