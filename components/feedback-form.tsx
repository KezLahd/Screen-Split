"use client"

import type React from "react"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group"
import { Label } from "@/components/ui/label"
import { CheckCircle2 } from "lucide-react"

export default function FeedbackForm() {
  const [submitted, setSubmitted] = useState(false)

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    // In a real implementation, you would send the form data to your backend
    // For now, we'll just simulate a successful submission
    setTimeout(() => {
      setSubmitted(true)
    }, 1000)
  }

  if (submitted) {
    return (
      <div className="rounded-lg border border-zinc-800 bg-zinc-950 p-8 text-center">
        <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-blue-500/10 text-blue-500">
          <CheckCircle2 className="h-6 w-6" />
        </div>
        <h3 className="mt-4 text-xl font-semibold text-white">Thank You!</h3>
        <p className="mt-2 text-zinc-400">
          Your feedback has been submitted successfully. We appreciate your help in improving Screen Split.
        </p>
        <Button className="mt-6 bg-blue-500 hover:bg-blue-600 text-white" onClick={() => setSubmitted(false)}>
          Submit Another Response
        </Button>
      </div>
    )
  }

  return (
    <form onSubmit={handleSubmit} className="rounded-lg border border-zinc-800 bg-zinc-950 p-6">
      <div className="space-y-6">
        <div className="space-y-2">
          <Label htmlFor="email" className="text-white">
            Email
          </Label>
          <Input
            id="email"
            type="email"
            placeholder="your@email.com"
            required
            className="bg-zinc-900 border-zinc-800 focus:border-blue-500 text-white"
          />
        </div>

        <div className="space-y-2">
          <Label className="text-white">How would you rate your experience with Screen Split?</Label>
          <RadioGroup defaultValue="good" className="flex space-x-4">
            <div className="flex items-center space-x-2">
              <RadioGroupItem value="excellent" id="excellent" />
              <Label htmlFor="excellent" className="text-zinc-300">
                Excellent
              </Label>
            </div>
            <div className="flex items-center space-x-2">
              <RadioGroupItem value="good" id="good" />
              <Label htmlFor="good" className="text-zinc-300">
                Good
              </Label>
            </div>
            <div className="flex items-center space-x-2">
              <RadioGroupItem value="average" id="average" />
              <Label htmlFor="average" className="text-zinc-300">
                Average
              </Label>
            </div>
            <div className="flex items-center space-x-2">
              <RadioGroupItem value="poor" id="poor" />
              <Label htmlFor="poor" className="text-zinc-300">
                Poor
              </Label>
            </div>
          </RadioGroup>
        </div>

        <div className="space-y-2">
          <Label htmlFor="feedback" className="text-white">
            What could we improve?
          </Label>
          <Textarea
            id="feedback"
            placeholder="Share your thoughts, suggestions, or report any bugs you've encountered..."
            rows={5}
            required
            className="bg-zinc-900 border-zinc-800 focus:border-blue-500 text-white"
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="features" className="text-white">
            Any features you'd like to see added?
          </Label>
          <Textarea
            id="features"
            placeholder="Tell us what features would make Screen Split even better for you..."
            rows={3}
            className="bg-zinc-900 border-zinc-800 focus:border-blue-500 text-white"
          />
        </div>

        <Button type="submit" className="w-full bg-blue-500 hover:bg-blue-600 text-white">
          Submit Feedback
        </Button>
      </div>
    </form>
  )
}
