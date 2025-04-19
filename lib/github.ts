import { cache } from "react"

// Define types for GitHub API responses
interface GitHubAsset {
  name: string
  browser_download_url: string
  size: number
  download_count: number
  created_at: string
}

interface GitHubRelease {
  id: number
  tag_name: string
  name: string
  published_at: string
  body: string
  html_url: string
  prerelease: boolean
  draft: boolean
  assets: GitHubAsset[]
}

export interface ProcessedRelease {
  version: string
  name: string
  date: string
  isCurrent: boolean
  features: string[]
  changes: string[]
  fixes: string[]
  html_url: string
  assets: {
    name: string
    download_url: string
    size: number
    download_count: number
  }[]
}

// Function to parse GitHub release notes into structured sections
function parseReleaseNotes(body: string) {
  const sections = {
    features: [] as string[],
    changes: [] as string[],
    fixes: [] as string[],
  }

  if (!body) return sections

  // Split the body into lines
  const lines = body.split("\n")
  let currentSection = ""

  // Common section headers in GitHub release notes
  const featureSectionHeaders = ["new features", "features", "what's new", "new"]
  const changeSectionHeaders = ["changes", "improvements", "changed", "updated"]
  const fixSectionHeaders = ["bug fixes", "fixes", "fixed", "bugfixes", "bug-fixes"]

  for (const line of lines) {
    const trimmedLine = line.trim()
    const lowerLine = trimmedLine.toLowerCase()

    // Check for section headers
    if (featureSectionHeaders.some((header) => lowerLine.includes(header))) {
      currentSection = "features"
      continue
    } else if (changeSectionHeaders.some((header) => lowerLine.includes(header))) {
      currentSection = "changes"
      continue
    } else if (fixSectionHeaders.some((header) => lowerLine.includes(header))) {
      currentSection = "fixes"
      continue
    }

    // Skip empty lines or lines that look like headers
    if (!trimmedLine || trimmedLine.startsWith("#") || trimmedLine.startsWith("##")) {
      continue
    }

    // Extract bullet points
    if (
      (trimmedLine.startsWith("- ") || trimmedLine.startsWith("* ") || trimmedLine.startsWith("• ")) &&
      currentSection
    ) {
      const content = trimmedLine.substring(2).trim()
      if (content && sections[currentSection as keyof typeof sections]) {
        sections[currentSection as keyof typeof sections].push(content)
      }
    }
  }

  return sections
}

// Fallback data in case the GitHub API call fails
function getFallbackReleases(): ProcessedRelease[] {
  return [
    {
      version: "1.1.2",
      name: "Successful App Installer",
      date: "April 17, 2025",
      isCurrent: true,
      features: [
        "First stable .exe installer for seamless Windows setup",
        "Automatic installation of all required dependencies",
        "Supports install location selection and desktop shortcut creation",
      ],
      changes: [
        "Added installer.iss script for Inno Setup configuration",
        "Integrated installer into the GitHub Actions build workflow",
        "Minor backend refinements to improve packaging and launch flow",
      ],
      fixes: [],
      html_url: "https://github.com/KezLahd/Screen-Split/releases/tag/v1.1.2",
      assets: [
        {
          name: "ScreenSplit-Setup-1.1.2.exe",
          download_url: "https://github.com/KezLahd/Screen-Split/releases/download/v1.1.2/ScreenSplit-Setup-1.1.2.exe",
          size: 45000,
          download_count: 0,
        },
      ],
    },
    {
      version: "1.0.2",
      name: "Update System and Installation Fixes",
      date: "April 16, 2025",
      isCurrent: false,
      features: [
        "Added automatic update checking",
        "Added system download and installation system",
        "Centralized installation into entry point",
      ],
      changes: [
        "Improved reliability point for better package installation",
        "Added online features",
        "Various UI/UX improvements",
      ],
      fixes: [],
      html_url: "https://github.com/KezLahd/Screen-Split/releases/tag/v1.0.2",
      assets: [],
    },
    {
      version: "1.0.1",
      name: "Bug Fix Release",
      date: "April 15, 2025",
      isCurrent: false,
      features: [],
      changes: [
        "Fixed bug with installation issues",
        "Updated dependency versions to match tested versions",
        "Added proper fallback behavior behavior",
      ],
      fixes: [],
      html_url: "https://github.com/KezLahd/Screen-Split/releases/tag/v1.0.1",
      assets: [],
    },
    {
      version: "1.0.0",
      name: "Initial Release",
      date: "April 15, 2025",
      isCurrent: false,
      features: [
        "Multi-display screen capture support",
        "Webcam integration with customizable position",
        "Real-time quality with customizable resolution",
        "Intuitive user-friendly UI with smooth animations",
        "Customizable layout presets",
        "Support for all Windows displays",
      ],
      changes: [],
      fixes: [],
      html_url: "https://github.com/KezLahd/Screen-Split/releases/tag/v1.0.0",
      assets: [],
    },
  ]
}

// Cache the GitHub API call to avoid unnecessary requests
export const getGitHubReleases = cache(async (): Promise<ProcessedRelease[]> => {
  // For now, just return the fallback data to avoid API errors
  return getFallbackReleases()

  // Uncomment this code when you're ready to connect to GitHub
  /*
  try {
    const username = "KezLahd"
    const repo = "Screen-Split"

    console.log(`Fetching releases from GitHub: ${username}/${repo}`)

    const response = await fetch(`https://api.github.com/repos/${username}/${repo}/releases`, {
      headers: {
        Accept: "application/vnd.github.v3+json",
        Authorization: `Bearer ${process.env.GITHUB_TOKEN}`,
      },
      next: { revalidate: 3600 }, // Revalidate every hour
    })

    if (!response.ok) {
      const errorText = await response.text()
      console.error(`GitHub API error: ${response.status} - ${errorText}`)
      throw new Error(`GitHub API responded with ${response.status}: ${errorText}`)
    }

    const releases: GitHubRelease[] = await response.json()

    if (!releases || releases.length === 0) {
      console.log("No releases found, using fallback data")
      return getFallbackReleases()
    }

    const publishedReleases = releases
      .filter((release) => !release.draft)
      .sort((a, b) => new Date(b.published_at).getTime() - new Date(a.published_at).getTime())

    return publishedReleases.map((release, index) => {
      const sections = parseReleaseNotes(release.body)

      return {
        version: release.tag_name.replace(/^v/i, ""),
        name: release.name || `Release ${release.tag_name}`,
        date: new Date(release.published_at).toLocaleDateString("en-US", {
          year: "numeric",
          month: "long",
          day: "numeric",
        }),
        isCurrent: index === 0,
        features: sections.features,
        changes: sections.changes,
        fixes: sections.fixes,
        html_url: release.html_url,
        assets: release.assets.map((asset) => ({
          name: asset.name,
          download_url: asset.browser_download_url,
          size: Math.round(asset.size / 1024),
          download_count: asset.download_count,
        })),
      }
    })
  } catch (error) {
    console.error("Error fetching GitHub releases:", error)
    return getFallbackReleases()
  }
  */
})
