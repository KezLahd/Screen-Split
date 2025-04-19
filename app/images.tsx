import Image from "next/image"

export default function ScreenshotGallery() {
  return (
    <section className="py-20 bg-zinc-900">
      <div className="container">
        <div className="text-center mb-16">
          <h2 className="text-3xl md:text-4xl font-bold mb-4 bg-gradient-to-r from-white to-blue-400 text-transparent bg-clip-text">
            See Screen Split in Action
          </h2>
          <p className="text-zinc-400 max-w-2xl mx-auto">
            Take a closer look at how Screen Split helps content creators deliver professional presentations.
          </p>
        </div>

        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          <div className="group relative rounded-lg border border-zinc-800 bg-zinc-950 overflow-hidden transition-all hover:border-blue-500/50">
            <Image
              src="/images/screen-split-demo1.png"
              width={600}
              height={400}
              alt="Educational tutorial with Screen Split"
              className="w-full aspect-video object-cover"
            />
            <div className="absolute inset-0 bg-gradient-to-t from-zinc-950 to-transparent opacity-0 group-hover:opacity-100 transition-opacity flex items-end">
              <div className="p-4">
                <h3 className="font-medium text-white">Educational Tutorial</h3>
                <p className="text-sm text-zinc-400">Perfect for online teaching and tutorials</p>
              </div>
            </div>
          </div>

          <div className="group relative rounded-lg border border-zinc-800 bg-zinc-950 overflow-hidden transition-all hover:border-blue-500/50">
            <Image
              src="/images/screen-split-demo2.png"
              width={600}
              height={400}
              alt="Streaming setup with Screen Split"
              className="w-full aspect-video object-cover"
            />
            <div className="absolute inset-0 bg-gradient-to-t from-zinc-950 to-transparent opacity-0 group-hover:opacity-100 transition-opacity flex items-end">
              <div className="p-4">
                <h3 className="font-medium text-white">Streaming Setup</h3>
                <p className="text-sm text-zinc-400">Ideal for game streamers and live content</p>
              </div>
            </div>
          </div>

          <div className="group relative rounded-lg border border-zinc-800 bg-zinc-950 overflow-hidden transition-all hover:border-blue-500/50">
            <Image
              src="/images/screen-split-demo3.png"
              width={600}
              height={400}
              alt="Professional presentation with Screen Split"
              className="w-full aspect-video object-cover"
            />
            <div className="absolute inset-0 bg-gradient-to-t from-zinc-950 to-transparent opacity-0 group-hover:opacity-100 transition-opacity flex items-end">
              <div className="p-4">
                <h3 className="font-medium text-white">Professional Presentation</h3>
                <p className="text-sm text-zinc-400">Enhance your business presentations</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}
