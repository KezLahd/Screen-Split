import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"

interface Version {
  version: string
  date: string
  isCurrent: boolean
  features: string[]
  bugfixes?: string[]
}

const versions: Version[] = [
  {
    version: "2.5",
    date: "April 2025",
    isCurrent: true,
    features: [
      "Added support for ultra-wide monitors",
      "New grid-based layout system",
      "Improved performance for 4K displays",
    ],
    bugfixes: ["Fixed memory leak when using multiple monitors", "Resolved issue with window focus after snapping"],
  },
  {
    version: "2.4",
    date: "January 2025",
    isCurrent: false,
    features: ["Added dark mode support", "New keyboard shortcut customization panel", "Improved startup time by 30%"],
    bugfixes: ["Fixed compatibility issues with Windows 11 updates", "Resolved conflict with certain graphics drivers"],
  },
  {
    version: "2.3",
    date: "October 2024",
    isCurrent: false,
    features: [
      "Added support for virtual desktops",
      "New preset layouts for common workflows",
      "Improved multi-monitor detection",
    ],
  },
  {
    version: "2.2",
    date: "July 2024",
    isCurrent: false,
    features: ["Added window grouping feature", "New animation options", "Reduced CPU usage by 15%"],
  },
]

export default function VersionHistory() {
  return (
    <div className="mt-8 grid gap-6 md:grid-cols-2">
      {versions.map((version) => (
        <Card key={version.version} className={version.isCurrent ? "border-primary" : ""}>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="text-2xl">Version {version.version}</CardTitle>
              {version.isCurrent && <Badge>Current</Badge>}
            </div>
            <CardDescription>{version.date}</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div>
                <h4 className="font-medium">New Features</h4>
                <ul className="mt-2 list-disc pl-5">
                  {version.features.map((feature, index) => (
                    <li key={index} className="text-muted-foreground">
                      {feature}
                    </li>
                  ))}
                </ul>
              </div>

              {version.bugfixes && (
                <div>
                  <h4 className="font-medium">Bug Fixes</h4>
                  <ul className="mt-2 list-disc pl-5">
                    {version.bugfixes.map((bugfix, index) => (
                      <li key={index} className="text-muted-foreground">
                        {bugfix}
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
