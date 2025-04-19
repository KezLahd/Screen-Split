import type { ReactNode } from "react"
import { Card, CardContent, CardHeader } from "@/components/ui/card"

interface FeatureCardProps {
  icon: ReactNode
  title: string
  description: string
}

export default function FeatureCard({ icon, title, description }: FeatureCardProps) {
  return (
    <Card className="bg-zinc-900 border-zinc-800 hover:border-blue-500/50 transition-colors">
      <CardHeader className="pb-2">
        <div className="flex items-center gap-3">
          <div className="rounded-full bg-blue-500/10 p-2 text-blue-500">{icon}</div>
          <h3 className="font-bold text-lg text-white">{title}</h3>
        </div>
      </CardHeader>
      <CardContent>
        <p className="text-zinc-400">{description}</p>
      </CardContent>
    </Card>
  )
}
