import { cache } from "react"

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

export const getGitHubReleases = cache(async (): Promise<ProcessedRelease[]> => {
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
})
