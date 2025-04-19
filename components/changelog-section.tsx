import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { getGitHubReleases } from "@/lib/github"
import { Download } from "lucide-react"
import Link from "next/link"

export default async function ChangelogSection() {
  const releases = await getGitHubReleases()

  return (
    <div className="space-y-6">
      {releases.map((version) => (
        <Card
          key={version.version}
          className={`bg-zinc-950 border-zinc-800 ${version.isCurrent ? "border-blue-500/50" : ""}`}
        >
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="text-xl text-white">Version {version.version}</CardTitle>
                <p className="text-zinc-500 text-sm">{version.date}</p>
              </div>
              <div className="flex items-center gap-2">
                {version.isCurrent && <Badge className="bg-blue-500 text-white hover:bg-blue-600">Current</Badge>}
                <Link
                  href={version.html_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-xs text-zinc-400 hover:text-white"
                >
                  View on GitHub
                </Link>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {version.features && version.features.length > 0 && (
                <div>
                  <h4 className="font-medium mb-2 text-white">New Features</h4>
                  <ul className="space-y-1 text-zinc-400">
                    {version.features.map((feature, index) => (
                      <li key={index} className="flex items-start">
                        <span className="text-blue-500 mr-2">•</span>
                        {feature}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {version.changes && version.changes.length > 0 && (
                <div>
                  <h4 className="font-medium mb-2 text-white">Changes & Improvements</h4>
                  <ul className="space-y-1 text-zinc-400">
                    {version.changes.map((change, index) => (
                      <li key={index} className="flex items-start">
                        <span className="text-blue-500 mr-2">•</span>
                        {change}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {version.fixes && version.fixes.length > 0 && (
                <div>
                  <h4 className="font-medium mb-2 text-white">Bug Fixes</h4>
                  <ul className="space-y-1 text-zinc-400">
                    {version.fixes.map((fix, index) => (
                      <li key={index} className="flex items-start">
                        <span className="text-blue-500 mr-2">•</span>
                        {fix}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {version.assets && version.assets.length > 0 && (
                <div className="mt-4 pt-4 border-t border-zinc-800">
                  <h4 className="font-medium mb-2 text-white">Downloads</h4>
                  <ul className="space-y-2">
                    {version.assets.map((asset, index) => (
                      <li key={index} className="flex items-center justify-between">
                        <div className="flex items-center">
                          <Download className="h-4 w-4 text-blue-500 mr-2" />
                          <span className="text-zinc-300">{asset.name}</span>
                        </div>
                        <div className="flex items-center gap-4">
                          <span className="text-xs text-zinc-500">{asset.size.toLocaleString()} KB</span>
                          <span className="text-xs text-zinc-500">
                            {asset.download_count.toLocaleString()} downloads
                          </span>
                          <a
                            href={asset.download_url}
                            className="text-xs bg-blue-500 hover:bg-blue-600 text-white px-2 py-1 rounded"
                            download
                          >
                            Download
                          </a>
                        </div>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  )
}
