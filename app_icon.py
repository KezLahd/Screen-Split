from PIL import Image, ImageDraw

# Create a new image with a transparent background
size = (256, 256)
image = Image.new('RGBA', size, (0, 0, 0, 0))
draw = ImageDraw.Draw(image)

# Draw a rounded rectangle for the screen
padding = 40
screen_bounds = (padding, padding, size[0]-padding, size[1]-padding)
draw.rounded_rectangle(screen_bounds, fill=(0, 120, 212), radius=20)

# Draw a smaller rectangle for the camera
camera_width = (size[0] - 2*padding) // 3
camera_height = (size[1] - 2*padding) // 2
camera_bounds = (
    size[0] - padding - camera_width,
    padding + 20,
    size[0] - padding - 10,
    padding + camera_height
)
draw.rounded_rectangle(camera_bounds, fill=(32, 32, 32), radius=10)

# Save as ICO file
image.save('app_icon.ico', format='ICO', sizes=[(256, 256)]) 