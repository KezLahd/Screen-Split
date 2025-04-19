"use client"

import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion"

export default function FaqSection() {
  return (
    <Accordion type="single" collapsible className="w-full">
      <AccordionItem value="item-1" className="border-zinc-800">
        <AccordionTrigger className="text-left text-white">
          What are the system requirements for Screen Split?
        </AccordionTrigger>
        <AccordionContent className="text-zinc-400">
          Screen Split requires Windows 10 or newer, 4GB RAM, and a modern CPU. For optimal performance, we recommend a
          quad-core processor and 8GB RAM. The app works with any webcam compatible with Windows.
        </AccordionContent>
      </AccordionItem>

      <AccordionItem value="item-2" className="border-zinc-800">
        <AccordionTrigger className="text-left text-white">
          Will Screen Split work with my streaming software?
        </AccordionTrigger>
        <AccordionContent className="text-zinc-400">
          Yes! Screen Split works with OBS Studio, Streamlabs, XSplit, and most other streaming software. You can
          capture the Screen Split window as a source in your streaming software.
        </AccordionContent>
      </AccordionItem>

      <AccordionItem value="item-3" className="border-zinc-800">
        <AccordionTrigger className="text-left text-white">Is there a Mac version available?</AccordionTrigger>
        <AccordionContent className="text-zinc-400">
          Currently, Screen Split is only available for Windows. We're considering Mac support for future releases based
          on user demand.
        </AccordionContent>
      </AccordionItem>

      <AccordionItem value="item-4" className="border-zinc-800">
        <AccordionTrigger className="text-left text-white">How do I report bugs or request features?</AccordionTrigger>
        <AccordionContent className="text-zinc-400">
          You can report bugs or request features through our feedback form on this page. For urgent issues, please
          email us directly at support@screensplit.com.
        </AccordionContent>
      </AccordionItem>

      <AccordionItem value="item-5" className="border-zinc-800">
        <AccordionTrigger className="text-left text-white">
          Will my webcam settings be preserved between sessions?
        </AccordionTrigger>
        <AccordionContent className="text-zinc-400">
          Yes, Screen Split saves your layout preferences, webcam settings, and other configurations between sessions.
          Your settings are stored locally on your computer.
        </AccordionContent>
      </AccordionItem>

      <AccordionItem value="item-6" className="border-zinc-800">
        <AccordionTrigger className="text-left text-white">Is Screen Split free to use?</AccordionTrigger>
        <AccordionContent className="text-zinc-400">
          The beta version is free to use. We're still determining our pricing model for the full release, but early
          beta testers will receive special benefits and discounts.
        </AccordionContent>
      </AccordionItem>
    </Accordion>
  )
}
